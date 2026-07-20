"""Reference capture uses bounded fixed commands and inert parsed output."""

from collections.abc import Mapping

from macwise_eval.system import CommandResult, FixedCommandRunner


class FakeRunner:
    """Record requested command vectors without invoking the host."""

    def __init__(self, outputs: Mapping[tuple[str, ...], CommandResult]) -> None:
        self.outputs = outputs
        self.calls: list[tuple[str, ...]] = []

    def run(self, executable: str, *arguments: str) -> CommandResult:
        command = (executable, *arguments)
        self.calls.append(command)
        return self.outputs[command]


def test_fixed_runner_rejects_shell_like_or_unapproved_executables() -> None:
    runner = FixedCommandRunner(timeout_seconds=1, max_output_bytes=64)

    result = runner.run("/bin/sh", "-c", "anything")

    assert result.returncode is None
    assert result.error is not None
    assert "not allowlisted" in result.error


def test_fixed_runner_uses_argument_vectors_and_bounded_output() -> None:
    runner = FixedCommandRunner(timeout_seconds=1, max_output_bytes=4)

    result = runner.run("/usr/bin/printf", "%s", "abcdef")

    assert result.stdout == "abcd"
    assert result.truncated is True
    assert result.error is None
