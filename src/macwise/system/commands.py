"""Bounded, allowlisted access to read-only host commands."""

import os
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from time import monotonic
from typing import Protocol

SAFE_PATH = "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/usr/local/bin"
SAFE_ENVIRONMENT_KEYS = ("HOME", "LANG", "LC_ALL", "TMPDIR")


class ReadCommand(StrEnum):
    """Programs MacWise is permitted to invoke while gathering evidence."""

    BREW = "brew"
    DISKUTIL = "diskutil"
    MDLS = "mdls"


class CommandState(StrEnum):
    """Normalized outcomes for a bounded command invocation."""

    COMPLETE = "complete"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class CommandResult:
    """Captured command output and limitations, safe for collector handling."""

    command: ReadCommand
    state: CommandState
    stdout: str
    stderr: str
    return_code: int | None
    duration_seconds: float
    limitations: tuple[str, ...] = ()


class ProcessRunner(Protocol):
    """Injectable subprocess boundary used by unit tests."""

    def __call__(
        self,
        args: Sequence[str],
        /,
        *,
        shell: bool,
        check: bool,
        capture_output: bool,
        timeout: float,
        env: Mapping[str, str],
    ) -> subprocess.CompletedProcess[bytes]: ...


class ExecutableResolver(Protocol):
    """Resolve one allowlisted command to a fixed executable path."""

    def __call__(self, command: ReadCommand, /) -> str | None: ...


COMMAND_CANDIDATES: Mapping[ReadCommand, tuple[str, ...]] = {
    ReadCommand.BREW: ("/opt/homebrew/bin/brew", "/usr/local/bin/brew"),
    ReadCommand.DISKUTIL: ("/usr/sbin/diskutil",),
    ReadCommand.MDLS: ("/usr/bin/mdls",),
}


def resolve_executable(command: ReadCommand) -> str | None:
    """Find an executable only among the fixed paths for an allowlisted command."""
    for candidate in COMMAND_CANDIDATES[command]:
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


def _bounded_text(value: bytes | str | None, limit: int) -> tuple[str, bool]:
    if value is None:
        return "", False
    raw_value = value.encode("utf-8", errors="replace") if isinstance(value, str) else value
    truncated = len(raw_value) > limit
    return raw_value[:limit].decode("utf-8", errors="replace"), truncated


def run_read_command(
    command: ReadCommand,
    arguments: Sequence[str] = (),
    *,
    timeout: float = 10.0,
    max_output_bytes: int = 1_000_000,
    source_environment: Mapping[str, str] | None = None,
    runner: ProcessRunner = _default_runner,
    resolver: ExecutableResolver = resolve_executable,
) -> CommandResult:
    """Run one allowlisted read command without a shell and return bounded data."""
    if not isinstance(command, ReadCommand):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise ValueError("command must be an allowlisted ReadCommand")
    if timeout <= 0:
        raise ValueError("timeout must be greater than zero")
    if max_output_bytes <= 0:
        raise ValueError("max_output_bytes must be greater than zero")
    if any(
        not isinstance(argument, str)  # pyright: ignore[reportUnnecessaryIsInstance]
        or "\0" in argument
        for argument in arguments
    ):
        raise ValueError("arguments must be strings without null bytes")

    executable = resolver(command)
    if executable is None:
        return CommandResult(
            command=command,
            state=CommandState.UNAVAILABLE,
            stdout="",
            stderr="",
            return_code=None,
            duration_seconds=0.0,
            limitations=(f"The {command.value} read-only command is not available.",),
        )

    invocation = (executable, *arguments)
    environment = _safe_environment(
        source_environment if source_environment is not None else os.environ
    )
    started_at = monotonic()
    try:
        completed = runner(
            invocation,
            shell=False,
            check=False,
            capture_output=True,
            timeout=timeout,
            env=environment,
        )
    except subprocess.TimeoutExpired as error:
        stdout, stdout_truncated = _bounded_text(error.stdout, max_output_bytes)
        stderr, stderr_truncated = _bounded_text(error.stderr, max_output_bytes)
        limitations = [f"The {command.value} command timed out after {timeout:g} seconds."]
        if stdout_truncated or stderr_truncated:
            limitations.append(
                f"Command output was truncated to {max_output_bytes} bytes per stream."
            )
        return CommandResult(
            command=command,
            state=CommandState.TIMED_OUT,
            stdout=stdout,
            stderr=stderr,
            return_code=None,
            duration_seconds=monotonic() - started_at,
            limitations=tuple(limitations),
        )
    except FileNotFoundError:
        return CommandResult(
            command=command,
            state=CommandState.UNAVAILABLE,
            stdout="",
            stderr="",
            return_code=None,
            duration_seconds=monotonic() - started_at,
            limitations=(f"The {command.value} read-only command became unavailable.",),
        )
    except OSError as error:
        return CommandResult(
            command=command,
            state=CommandState.FAILED,
            stdout="",
            stderr="",
            return_code=None,
            duration_seconds=monotonic() - started_at,
            limitations=(f"The {command.value} command could not run: {error.strerror or error}.",),
        )

    stdout, stdout_truncated = _bounded_text(completed.stdout, max_output_bytes)
    stderr, stderr_truncated = _bounded_text(completed.stderr, max_output_bytes)
    limitations: list[str] = []
    state = CommandState.COMPLETE
    if completed.returncode != 0:
        state = CommandState.FAILED
        limitations.append(
            f"The {command.value} command exited with status {completed.returncode}."
        )
    if stdout_truncated or stderr_truncated:
        limitations.append(f"Command output was truncated to {max_output_bytes} bytes per stream.")

    return CommandResult(
        command=command,
        state=state,
        stdout=stdout,
        stderr=stderr,
        return_code=completed.returncode,
        duration_seconds=monotonic() - started_at,
        limitations=tuple(limitations),
    )
