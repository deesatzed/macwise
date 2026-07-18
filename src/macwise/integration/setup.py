"""Narrow, user-scoped installation of the bundled MacWise Codex plugin."""

import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
from collections.abc import Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import BinaryIO, Protocol, cast
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from macwise.system.commands import SAFE_ENVIRONMENT_KEYS, SAFE_PATH, ProcessRunner

_MAX_MARKETPLACE_BYTES = 2 * 1024 * 1024
_MAX_PAYLOAD_BYTES = 8 * 1024 * 1024
_MAX_PAYLOAD_FILES = 512
_MARKETPLACE_NAME = re.compile(r"^[A-Za-z0-9_-]+$")
_CODEX_SELECTOR = re.compile(r"^macwise@[A-Za-z0-9_-]+$")
_CODEX_OUTPUT_LIMIT = 64 * 1024
_PLUGIN_SOURCE = {"source": "local", "path": "./plugins/macwise"}
_PLUGIN_ENTRY: dict[str, object] = {
    "name": "macwise",
    "source": _PLUGIN_SOURCE,
    "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
    "category": "Productivity",
}


class SetupStatus(StrEnum):
    """Truthful bounded outcome from one setup attempt."""

    INSTALLED = "installed"
    UPDATED = "updated"
    ALREADY_CURRENT = "already_current"
    REFUSED = "refused"
    INTERRUPTED = "interrupted"


@dataclass(frozen=True, slots=True)
class CodexCommandResult:
    """Bounded result returned by an injected fixed Codex runner."""

    ok: bool
    stdout: str = ""
    stderr: str = ""


class CodexRunner(Protocol):
    """Run one fixed Codex subcommand without a shell."""

    def run(self, arguments: tuple[str, ...]) -> CodexCommandResult: ...


def _bounded_codex_process_runner(
    args: Sequence[str],
    *,
    shell: bool,
    check: bool,
    capture_output: bool,
    timeout: float,
    env: Mapping[str, str],
) -> subprocess.CompletedProcess[bytes]:
    if not capture_output:
        raise ValueError("Codex output must be captured.")
    process = subprocess.Popen(
        list(args),
        shell=shell,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    stdout = bytearray()
    stderr = bytearray()

    def drain(stream: BinaryIO | None, destination: bytearray) -> None:
        if stream is None:
            return
        while chunk := stream.read(8192):
            remaining = (_CODEX_OUTPUT_LIMIT + 1) - len(destination)
            if remaining > 0:
                destination.extend(chunk[:remaining])

    readers = (
        threading.Thread(target=drain, args=(process.stdout, stdout), daemon=True),
        threading.Thread(target=drain, args=(process.stderr, stderr), daemon=True),
    )
    for reader in readers:
        reader.start()
    try:
        return_code = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired as error:
        process.kill()
        process.wait()
        for reader in readers:
            reader.join()
        raise subprocess.TimeoutExpired(
            error.cmd,
            error.timeout,
            output=bytes(stdout),
            stderr=bytes(stderr),
        ) from error
    for reader in readers:
        reader.join()
    completed = subprocess.CompletedProcess(
        list(args),
        return_code,
        stdout=bytes(stdout),
        stderr=bytes(stderr),
    )
    if check and return_code != 0:
        raise subprocess.CalledProcessError(
            return_code,
            list(args),
            output=completed.stdout,
            stderr=completed.stderr,
        )
    return completed


class SubprocessCodexRunner:
    """Run only the exact plugin add/remove commands needed by setup."""

    def __init__(
        self,
        *,
        executable: Path,
        home: Path,
        process_runner: ProcessRunner = _bounded_codex_process_runner,
        source_environment: Mapping[str, str] | None = None,
        timeout: float = 20.0,
    ) -> None:
        try:
            resolved = executable.expanduser().resolve(strict=True)
        except OSError as error:
            raise ValueError("The Codex executable is unavailable.") from error
        if not resolved.is_file() or not os.access(resolved, os.X_OK):
            raise ValueError("The Codex executable is unavailable.")
        if timeout <= 0:
            raise ValueError("The Codex setup timeout must be positive.")
        self.executable = resolved
        self.home = home.expanduser().absolute()
        self._runner = process_runner
        self._timeout = timeout
        source = source_environment if source_environment is not None else os.environ
        self._environment = {
            "HOME": str(self.home),
            "PATH": SAFE_PATH,
            **{
                key: source[key] for key in SAFE_ENVIRONMENT_KEYS if key != "HOME" and key in source
            },
        }

    def run(self, arguments: tuple[str, ...]) -> CodexCommandResult:
        """Run one allowlisted MacWise plugin command and bound both streams."""
        if (
            len(arguments) != 4
            or arguments[0] != "plugin"
            or arguments[1] not in {"add", "remove"}
            or _CODEX_SELECTOR.fullmatch(arguments[2]) is None
            or arguments[3] != "--json"
        ):
            return CodexCommandResult(ok=False, stderr="That Codex command is not allowlisted.")
        try:
            completed = self._runner(
                (str(self.executable), *arguments),
                shell=False,
                check=False,
                capture_output=True,
                timeout=self._timeout,
                env=self._environment,
            )
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as error:
            return CodexCommandResult(
                ok=False, stderr=f"Codex setup could not run: {type(error).__name__}."
            )
        stdout_truncated = len(completed.stdout) > _CODEX_OUTPUT_LIMIT
        stderr_truncated = len(completed.stderr) > _CODEX_OUTPUT_LIMIT
        stdout = completed.stdout[:_CODEX_OUTPUT_LIMIT].decode("utf-8", errors="replace")
        stderr = completed.stderr[:_CODEX_OUTPUT_LIMIT].decode("utf-8", errors="replace")
        if stdout_truncated or stderr_truncated:
            suffix = "Codex output limit exceeded."
            stderr = f"{stderr}\n{suffix}" if stderr else suffix
        return CodexCommandResult(
            ok=completed.returncode == 0 and not stdout_truncated and not stderr_truncated,
            stdout=stdout,
            stderr=stderr,
        )


@dataclass(frozen=True, slots=True)
class SetupResult:
    """Public setup result with optional recovery guidance."""

    status: SetupStatus
    message: str
    recovery: str = ""


class OwnershipMarker(BaseModel):
    """Evidence that a personal plugin tree is managed by MacWise setup."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: int = Field(default=1, ge=1, le=1)
    plugin_name: str = Field(default="macwise", pattern=r"^macwise$")
    repository: str = Field(default="https://github.com/deesatzed/macwise")
    plugin_version: str = Field(min_length=1, max_length=128)
    payload_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    python_executable: str = Field(min_length=1, max_length=4096)


class SetupError(RuntimeError):
    """Safe bounded setup refusal."""


def _read_regular_bytes(path: Path, *, limit: int, label: str) -> bytes:
    if path.is_symlink():
        raise SetupError(f"The {label} cannot be a symbolic link.")
    try:
        item = path.stat()
    except FileNotFoundError:
        raise SetupError(f"The {label} is missing.") from None
    except OSError as error:
        raise SetupError(f"MacWise could not inspect the {label}.") from error
    if not path.is_file():
        raise SetupError(f"The {label} is not a regular file.")
    if item.st_size > limit:
        raise SetupError(f"The {label} is too large to read safely.")
    try:
        return path.read_bytes()
    except OSError as error:
        raise SetupError(f"MacWise could not read the {label}.") from error


def _json_object(data: bytes, *, label: str) -> dict[str, object]:
    try:
        value = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SetupError(f"The {label} is not valid UTF-8 JSON.") from error
    if not isinstance(value, dict):
        raise SetupError(f"The {label} must contain a JSON object.")
    raw = cast(dict[object, object], value)
    if not all(isinstance(key, str) for key in raw):
        raise SetupError(f"The {label} must contain a JSON object.")
    return cast(dict[str, object], raw)


def _validate_managed_directory(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise SetupError(f"The {label} cannot be a symbolic link.")
    if path.exists() and not path.is_dir():
        raise SetupError(f"The {label} is not a directory.")


def _ensure_managed_parent(home: Path, relative: tuple[str, ...]) -> Path:
    current = home
    for part in relative:
        current = current / part
        _validate_managed_directory(current, label=f"setup directory {part}")
        if not current.exists():
            try:
                current.mkdir(mode=0o700)
            except OSError as error:
                raise SetupError(f"MacWise could not create setup directory {part}.") from error
            _validate_managed_directory(current, label=f"setup directory {part}")
    return current


def _payload_metadata(payload: Path) -> tuple[str, str]:
    _validate_managed_directory(payload, label="bundled plugin payload")
    if not payload.is_dir():
        raise SetupError("The bundled plugin payload is missing.")
    digest = hashlib.sha256()
    total = 0
    count = 0
    for path in sorted(payload.rglob("*"), key=lambda item: item.relative_to(payload).as_posix()):
        if path.is_symlink():
            raise SetupError("The bundled plugin payload contains a symbolic link.")
        if path.is_dir():
            continue
        if not path.is_file():
            raise SetupError("The bundled plugin payload contains a nonregular file.")
        data = _read_regular_bytes(path, limit=_MAX_PAYLOAD_BYTES, label="bundled plugin file")
        total += len(data)
        count += 1
        if total > _MAX_PAYLOAD_BYTES or count > _MAX_PAYLOAD_FILES:
            raise SetupError("The bundled plugin payload exceeds its safety bound.")
        relative = path.relative_to(payload).as_posix().encode()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    manifest_path = payload / ".codex-plugin" / "plugin.json"
    manifest = _json_object(
        _read_regular_bytes(manifest_path, limit=256 * 1024, label="plugin manifest"),
        label="plugin manifest",
    )
    if manifest.get("name") != "macwise":
        raise SetupError("The bundled plugin manifest has the wrong name.")
    version = manifest.get("version")
    if not isinstance(version, str) or not version:
        raise SetupError("The bundled plugin manifest has no valid version.")
    if manifest.get("repository") != "https://github.com/deesatzed/macwise":
        raise SetupError("The bundled plugin manifest has the wrong repository identity.")
    return digest.hexdigest(), version


def _load_marker(plugin: Path) -> OwnershipMarker:
    marker_path = plugin / ".macwise-owned.json"
    try:
        return OwnershipMarker.model_validate_json(
            _read_regular_bytes(marker_path, limit=64 * 1024, label="MacWise ownership marker")
        )
    except (SetupError, ValidationError, ValueError) as error:
        raise SetupError(
            "The existing MacWise plugin is not safely owned by this installer."
        ) from error


def _load_marketplace(path: Path) -> tuple[dict[str, object], bytes | None]:
    if not path.exists() and not path.is_symlink():
        return (
            {
                "name": "personal",
                "interface": {"displayName": "Personal"},
                "plugins": [],
            },
            None,
        )
    original = _read_regular_bytes(path, limit=_MAX_MARKETPLACE_BYTES, label="personal marketplace")
    document = _json_object(original, label="personal marketplace")
    name = document.get("name")
    plugins = document.get("plugins")
    if not isinstance(name, str) or _MARKETPLACE_NAME.fullmatch(name) is None:
        raise SetupError("The personal marketplace has an invalid name.")
    if not isinstance(plugins, list):
        raise SetupError("The personal marketplace has an invalid plugin list.")
    typed_plugins = cast(list[object], plugins)
    if not all(isinstance(entry, dict) for entry in typed_plugins):
        raise SetupError("The personal marketplace has an invalid plugin list.")
    interface = document.get("interface")
    if interface is not None and not isinstance(interface, dict):
        raise SetupError("The personal marketplace has invalid display metadata.")
    return document, original


def _with_macwise_entry(document: dict[str, object]) -> dict[str, object]:
    plugins = cast(list[object], document["plugins"])
    updated: list[object] = []
    found = False
    for raw in plugins:
        entry = cast(dict[str, object], raw)
        if entry.get("name") != "macwise":
            updated.append(entry)
            continue
        if found or entry.get("source") != _PLUGIN_SOURCE:
            raise SetupError("The personal marketplace contains a conflicting MacWise entry.")
        updated.append(dict(_PLUGIN_ENTRY))
        found = True
    if not found:
        updated.append(dict(_PLUGIN_ENTRY))
    result = dict(document)
    result["plugins"] = updated
    return result


def _atomic_write(path: Path, data: bytes) -> None:
    temporary = path.parent / f".{path.name}.macwise-{uuid4().hex}.tmp"
    descriptor: int | None = None
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = None
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except OSError as error:
        raise SetupError("MacWise could not write a setup file atomically.") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
        with suppress(OSError):
            temporary.unlink(missing_ok=True)


def _json_bytes(value: Mapping[str, object] | BaseModel) -> bytes:
    document = value.model_dump(mode="json") if isinstance(value, BaseModel) else value
    return (json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _verified_codex_result(result: CodexCommandResult) -> bool:
    if not result.ok:
        return False
    try:
        document = json.loads(result.stdout)
    except json.JSONDecodeError:
        return False
    return isinstance(document, dict) and len(cast(dict[object, object], document)) > 0


class CodexSetupService:
    """Install only MacWise-owned personal plugin state and compensate failures."""

    def __init__(
        self,
        *,
        home: Path,
        payload: Path,
        python_executable: Path,
        runner: CodexRunner,
    ) -> None:
        self.home = home.expanduser().absolute()
        self.payload = payload.expanduser().absolute()
        self.python_executable = python_executable.expanduser().absolute()
        self.runner = runner

    def install(self) -> SetupResult:
        """Install or update the plugin without touching unrelated Codex configuration."""
        try:
            return self._install()
        except SetupError as error:
            return SetupResult(status=SetupStatus.REFUSED, message=str(error))

    def _install(self) -> SetupResult:
        if self.home.is_symlink() or not self.home.is_dir():
            raise SetupError("The selected home directory is unsafe or unavailable.")
        runtime = self.python_executable.resolve(strict=True)
        if not runtime.is_file() or not os.access(runtime, os.X_OK):
            raise SetupError("The current MacWise Python runtime is not executable.")
        payload_digest, plugin_version = _payload_metadata(self.payload)

        plugins_parent = _ensure_managed_parent(self.home, ("plugins",))
        marketplace_parent = _ensure_managed_parent(self.home, (".agents", "plugins"))
        plugin = plugins_parent / "macwise"
        marketplace_path = marketplace_parent / "marketplace.json"
        if plugin.is_symlink() or (plugin.exists() and not plugin.is_dir()):
            raise SetupError("The personal MacWise plugin path is unsafe.")

        current_marker: OwnershipMarker | None = None
        if plugin.exists():
            current_marker = _load_marker(plugin)
        marketplace, original_marketplace = _load_marketplace(marketplace_path)
        marketplace_name = cast(str, marketplace["name"])
        updated_marketplace = _with_macwise_entry(marketplace)

        marker = OwnershipMarker(
            plugin_version=plugin_version,
            payload_sha256=payload_digest,
            python_executable=str(runtime),
        )
        already_current = current_marker == marker
        stage = plugins_parent / f".macwise-stage-{uuid4().hex}"
        backup = plugins_parent / f".macwise-backup-{uuid4().hex}"
        had_plugin = plugin.exists()
        replaced_plugin = False
        wrote_marketplace = False
        try:
            shutil.copytree(self.payload, stage, symlinks=False)
            mcp = {
                "mcpServers": {
                    "macwise": {
                        "command": str(runtime),
                        "args": ["-m", "macwise", "codex", "serve"],
                    }
                }
            }
            _atomic_write(stage / ".mcp.json", _json_bytes(mcp))
            _atomic_write(stage / ".macwise-owned.json", _json_bytes(marker))
            if had_plugin:
                os.replace(plugin, backup)
            os.replace(stage, plugin)
            replaced_plugin = True
            _atomic_write(marketplace_path, _json_bytes(updated_marketplace))
            wrote_marketplace = True
        except (OSError, SetupError) as error:
            self._restore_files(
                plugin=plugin,
                backup=backup,
                stage=stage,
                had_plugin=had_plugin,
                replaced_plugin=replaced_plugin,
                marketplace_path=marketplace_path,
                original_marketplace=original_marketplace,
                wrote_marketplace=wrote_marketplace,
            )
            if isinstance(error, SetupError):
                raise
            raise SetupError("MacWise could not stage the personal plugin safely.") from error

        selector = f"macwise@{marketplace_name}"
        installed = self.runner.run(("plugin", "add", selector, "--json"))
        if not _verified_codex_result(installed):
            restored = self._restore_files(
                plugin=plugin,
                backup=backup,
                stage=stage,
                had_plugin=had_plugin,
                replaced_plugin=True,
                marketplace_path=marketplace_path,
                original_marketplace=original_marketplace,
                wrote_marketplace=True,
            )
            compensation = self.runner.run(
                ("plugin", "add" if had_plugin else "remove", selector, "--json")
            )
            if not restored or not _verified_codex_result(compensation):
                return SetupResult(
                    status=SetupStatus.INTERRUPTED,
                    message="MacWise setup failed and recovery could not be fully verified.",
                    recovery="Retry macwise setup codex after reviewing the personal plugin state.",
                )
            return SetupResult(
                status=SetupStatus.REFUSED,
                message=(
                    "MacWise could not verify the Codex plugin result; prior files were restored."
                    if installed.ok
                    else "Codex did not accept the MacWise plugin; prior files were restored."
                ),
            )

        try:
            if backup.exists():
                shutil.rmtree(backup)
        except OSError:
            return SetupResult(
                status=SetupStatus.INTERRUPTED,
                message="MacWise installed the plugin but could not remove its owned setup backup.",
                recovery="Retry macwise setup codex to repair owned setup state.",
            )
        status = (
            SetupStatus.ALREADY_CURRENT
            if already_current
            else SetupStatus.UPDATED
            if had_plugin
            else SetupStatus.INSTALLED
        )
        return SetupResult(
            status=status,
            message="The MacWise Codex experience is installed for this user.",
        )

    @staticmethod
    def _restore_files(
        *,
        plugin: Path,
        backup: Path,
        stage: Path,
        had_plugin: bool,
        replaced_plugin: bool,
        marketplace_path: Path,
        original_marketplace: bytes | None,
        wrote_marketplace: bool,
    ) -> bool:
        try:
            if stage.exists():
                shutil.rmtree(stage)
            if replaced_plugin and plugin.exists():
                shutil.rmtree(plugin)
            if had_plugin and backup.exists():
                os.replace(backup, plugin)
            if wrote_marketplace:
                if original_marketplace is None:
                    marketplace_path.unlink(missing_ok=True)
                else:
                    _atomic_write(marketplace_path, original_marketplace)
            return True
        except (OSError, SetupError):
            return False
