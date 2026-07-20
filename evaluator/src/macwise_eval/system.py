"""Bounded, allowlisted system-command boundary for independent reference capture."""

import subprocess
from dataclasses import dataclass

_ALLOWLIST = frozenset(
    {
        "/bin/df",
        "/bin/launchctl",
        "/opt/homebrew/bin/brew",
        "/usr/bin/printf",
        "/usr/bin/sw_vers",
        "/usr/bin/tmutil",
        "/usr/local/bin/brew",
    }
)


@dataclass(frozen=True)
class CommandResult:
    """Bounded inert result of one fixed argument-vector command."""

    returncode: int | None
    stdout: str
    stderr: str
    truncated: bool
    error: str | None


class FixedCommandRunner:
    """Run only named read-only system commands without a shell or inherited Homebrew side effects."""

    def __init__(self, *, timeout_seconds: float, max_output_bytes: int) -> None:
        self._timeout_seconds = timeout_seconds
        self._max_output_bytes = max_output_bytes

    def run(self, executable: str, *arguments: str) -> CommandResult:
        """Execute an allowlisted argv with strict output and timeout bounds."""
        if executable not in _ALLOWLIST:
            return CommandResult(
                returncode=None,
                stdout="",
                stderr="",
                truncated=False,
                error="executable is not allowlisted",
            )
        environment = {
            "HOMEBREW_NO_ANALYTICS": "1",
            "HOMEBREW_NO_AUTO_UPDATE": "1",
            "LANG": "C",
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/usr/local/bin",
        }
        try:
            completed = subprocess.run(
                (executable, *arguments),
                check=False,
                capture_output=True,
                env=environment,
                shell=False,
                text=False,
                timeout=self._timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return CommandResult(None, "", "", False, str(error))
        stdout = completed.stdout[: self._max_output_bytes]
        stderr = completed.stderr[: self._max_output_bytes]
        return CommandResult(
            returncode=completed.returncode,
            stdout=stdout.decode("utf-8", errors="replace"),
            stderr=stderr.decode("utf-8", errors="replace"),
            truncated=(
                len(completed.stdout) > self._max_output_bytes
                or len(completed.stderr) > self._max_output_bytes
            ),
            error=None,
        )
