import pytest
from typer.testing import CliRunner

from macwise.cli import app

runner = CliRunner()

COMMANDS = (
    ("scan",),
    ("review",),
    ("review", "apps"),
    ("review", "brew"),
    ("review", "startup"),
    ("review", "duplicates"),
    ("review", "largest"),
    ("review", "unused"),
    ("review", "unknown"),
    ("explain",),
    ("compare",),
    ("startup",),
    ("storage",),
    ("backups",),
    ("plan",),
    ("plan", "add"),
    ("plan", "show"),
    ("apply",),
    ("undo",),
    ("doctor",),
    ("setup",),
    ("setup", "codex"),
    ("help",),
)


@pytest.mark.parametrize("command", COMMANDS, ids=lambda value: " ".join(value))
def test_every_public_command_has_novice_friendly_help(command: tuple[str, ...]) -> None:
    result = runner.invoke(app, [*command, "--help"])

    assert result.exit_code == 0, result.stdout
    assert "Useful when:" in result.stdout
    assert "Examples:" in result.stdout
    assert result.stdout.count("macwise") >= 2
    assert "Next:" in result.stdout
    assert any(
        safety in result.stdout
        for safety in (
            "read-only",
            "does not remove or change anything",
            "can change installed software",
            "can restore installed software",
            "writes only local MacWise planning state",
        )
    )


def test_plan_help_distinguishes_local_state_from_host_changes() -> None:
    root = runner.invoke(app, ["plan", "--help"])
    add = runner.invoke(app, ["plan", "add", "--help"])
    show = runner.invoke(app, ["plan", "show", "--help"])

    assert root.exit_code == add.exit_code == show.exit_code == 0
    assert "writes only local MacWise planning state" in root.stdout
    assert "writes only local MacWise planning state" in add.stdout
    assert "read-only" in show.stdout
    assert "does not change installed software or user data" in " ".join(add.stdout.split())


def test_root_help_lists_the_small_public_hierarchy() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in (
        "scan",
        "review",
        "explain",
        "compare",
        "startup",
        "storage",
        "backups",
        "plan",
        "apply",
        "undo",
        "doctor",
        "setup",
        "help",
    ):
        assert command in result.stdout
