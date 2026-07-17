"""Closed, allowlisted mutating command actions for approved executions."""

import os
import re
import subprocess
from collections.abc import Mapping, Sequence
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from macwise.system.commands import (
    SAFE_ENVIRONMENT_KEYS,
    SAFE_PATH,
    ProcessRunner,
)

_HOMEBREW_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9@+_.-]*")
_LAUNCH_AGENT_LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_OUTPUT_LIMIT = 64 * 1024


class CommandActionError(RuntimeError):
    """An allowlisted host command could not be constructed or completed."""


class MutationExecutable(StrEnum):
    """Programs permitted to mutate approved Homebrew or launchd state."""

    BREW = "brew"
    LAUNCHCTL = "launchctl"


class MutationExecutableResolver(Protocol):
    """Resolve one mutation command to a fixed trusted executable path."""

    def __call__(self, executable: MutationExecutable, /) -> str | None: ...


MUTATION_EXECUTABLE_CANDIDATES: Mapping[MutationExecutable, tuple[str, ...]] = {
    MutationExecutable.BREW: ("/opt/homebrew/bin/brew", "/usr/local/bin/brew"),
    MutationExecutable.LAUNCHCTL: ("/bin/launchctl",),
}


def resolve_mutation_executable(executable: MutationExecutable) -> str | None:
    """Resolve only a fixed, executable mutation-command candidate."""
    for candidate in MUTATION_EXECUTABLE_CANDIDATES[executable]:
        path = Path(candidate)
        if path.is_file() and os.access(path, os.X_OK):
            return candidate
    return None


def _safe_environment(source: Mapping[str, str]) -> dict[str, str]:
    environment = {
        "HOMEBREW_NO_ANALYTICS": "1",
        "HOMEBREW_NO_AUTO_UPDATE": "1",
        "PATH": SAFE_PATH,
    }
    environment.update({key: source[key] for key in SAFE_ENVIRONMENT_KEYS if key in source})
    return environment


def _default_runner(
    args: Sequence[str],
    *,
    shell: bool,
    check: bool,
    capture_output: bool,
    timeout: float,
    env: Mapping[str, str],
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        list(args),
        shell=shell,
        check=check,
        capture_output=capture_output,
        timeout=timeout,
        env=env,
    )


class MutationCommandAdapter:
    """Expose only the exact command actions MacWise can approve and reverse."""

    def __init__(
        self,
        *,
        launch_agents_root: Path,
        uid: int,
        source_environment: Mapping[str, str] | None = None,
        runner: ProcessRunner = _default_runner,
        resolver: MutationExecutableResolver = resolve_mutation_executable,
        timeout: float = 30.0,
    ) -> None:
        if uid < 0:
            raise ValueError("uid must not be negative")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        self.launch_agents_root = launch_agents_root.expanduser().absolute()
        self.uid = uid
        self._environment = _safe_environment(
            source_environment if source_environment is not None else os.environ
        )
        self._runner = runner
        self._resolver = resolver
        self._timeout = timeout

    @staticmethod
    def _homebrew_token(value: str) -> str:
        if _HOMEBREW_TOKEN.fullmatch(value) is None:
            raise CommandActionError("The Homebrew token is not safe to execute.")
        return value

    def _launch_agent(self, label: str, source_path: Path) -> tuple[str, Path]:
        if _LAUNCH_AGENT_LABEL.fullmatch(label) is None:
            raise CommandActionError("The LaunchAgent label is not safe to execute.")
        source = source_path.expanduser().absolute()
        if (
            source.parent != self.launch_agents_root
            or source.suffix != ".plist"
            or any(
                ancestor.is_symlink()
                for ancestor in (
                    source,
                    self.launch_agents_root,
                    *self.launch_agents_root.parents,
                )
            )
            or not source.is_file()
        ):
            raise CommandActionError("The LaunchAgent plist is not an exact safe source.")
        return label, source

    def _run(self, executable: MutationExecutable, arguments: tuple[str, ...]) -> None:
        resolved = self._resolver(executable)
        if resolved is None or resolved not in MUTATION_EXECUTABLE_CANDIDATES[executable]:
            raise CommandActionError(
                f"The allowlisted {executable.value} executable is unavailable."
            )
        try:
            completed = self._runner(
                (resolved, *arguments),
                shell=False,
                check=False,
                capture_output=True,
                timeout=self._timeout,
                env=self._environment,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as error:
            raise CommandActionError(
                f"The allowlisted {executable.value} action did not complete."
            ) from error
        output_size = len(completed.stdout) + len(completed.stderr)
        if completed.returncode != 0 or output_size > _OUTPUT_LIMIT:
            raise CommandActionError(f"The allowlisted {executable.value} action did not complete.")

    def uninstall_formula(self, token: str) -> None:
        self._run(
            MutationExecutable.BREW,
            ("uninstall", "--formula", self._homebrew_token(token)),
        )

    def uninstall_cask(self, token: str) -> None:
        self._run(
            MutationExecutable.BREW,
            ("uninstall", "--cask", self._homebrew_token(token)),
        )

    def install_formula(self, token: str) -> None:
        self._run(
            MutationExecutable.BREW,
            ("install", "--formula", self._homebrew_token(token)),
        )

    def install_cask(self, token: str) -> None:
        self._run(
            MutationExecutable.BREW,
            ("install", "--cask", self._homebrew_token(token)),
        )

    def stop_service(self, token: str) -> None:
        self._run(
            MutationExecutable.BREW,
            ("services", "stop", self._homebrew_token(token)),
        )

    def start_service(self, token: str) -> None:
        self._run(
            MutationExecutable.BREW,
            ("services", "start", self._homebrew_token(token)),
        )

    def disable_launch_agent(
        self,
        label: str,
        source_path: Path,
        *,
        was_running: bool,
    ) -> None:
        label, source = self._launch_agent(label, source_path)
        domain = f"gui/{self.uid}"
        self._run(MutationExecutable.LAUNCHCTL, ("disable", f"{domain}/{label}"))
        if was_running:
            self._run(MutationExecutable.LAUNCHCTL, ("bootout", domain, str(source)))

    def enable_launch_agent(
        self,
        label: str,
        source_path: Path,
        *,
        was_running: bool,
    ) -> None:
        self.restore_launch_agent(
            label,
            source_path,
            was_enabled=True,
            was_running=was_running,
        )

    def restore_launch_agent(
        self,
        label: str,
        source_path: Path,
        *,
        was_enabled: bool,
        was_running: bool,
    ) -> None:
        """Restore the exact recorded user-domain enablement and running state."""
        label, source = self._launch_agent(label, source_path)
        domain = f"gui/{self.uid}"
        if was_enabled:
            self._run(MutationExecutable.LAUNCHCTL, ("enable", f"{domain}/{label}"))
        if was_running:
            self._run(MutationExecutable.LAUNCHCTL, ("bootstrap", domain, str(source)))
