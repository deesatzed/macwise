"""Independent reference collectors preserve raw facts and source correlation labels."""

from pathlib import Path

from macwise_eval.reference.capture import collect_reference_observations
from macwise_eval.system import CommandResult


class FakeRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    def run(self, executable: str, *arguments: str) -> CommandResult:
        command = (executable, *arguments)
        self.calls.append(command)
        outputs: dict[tuple[str, ...], CommandResult] = {
            ("/bin/df", "-kP"): CommandResult(0, "/dev/disk1 100 25 75 25% /\n", "", False, None),
            ("/usr/bin/tmutil", "latestbackup"): CommandResult(
                0, "/Volumes/.timemachine/example\n", "", False, None
            ),
            ("/opt/homebrew/bin/brew", "list", "--formula"): CommandResult(
                0, "example\n", "", False, None
            ),
            ("/bin/launchctl", "print-disabled", "user/501"): CommandResult(
                0, '{"example" => false}\n', "", False, None
            ),
        }
        return outputs[command]


def test_reference_capture_uses_fixed_read_only_commands_and_marks_correlated_sources(
    tmp_path: Path,
) -> None:
    runner = FakeRunner()
    app_root = tmp_path / "Applications"
    app_root.mkdir()
    (app_root / "Example.app").mkdir()

    observations = collect_reference_observations(runner, app_roots=(app_root,), user_id="501")

    assert tuple(observations) == ("applications", "backups", "homebrew", "startup", "storage")
    assert observations["storage"].source_correlated is True
    assert observations["applications"].source_correlated is False
    assert ("/bin/df", "-kP") in runner.calls
    assert ("/opt/homebrew/bin/brew", "list", "--formula") in runner.calls
    assert observations["applications"].document["bundle_count"] == 1
