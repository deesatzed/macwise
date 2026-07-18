from typer.testing import CliRunner

from macwise.cli import app

runner = CliRunner()


def test_no_arguments_shows_guided_choices_without_blocking() -> None:
    result = runner.invoke(app)

    assert result.exit_code == 0
    assert "MacWise" in result.stdout
    assert "What would you like to do?" in result.stdout
    expected_choices = (
        "1. Scan this Mac",
        "2. Review installed apps",
        "3. Review Homebrew software",
        "4. See what starts automatically",
        "5. Find overlapping apps",
        "6. See what uses the most space",
        "7. Ask what an app does",
        "8. Create a safe cleanup plan",
        "9. Assess findings and usefulness",
        "10. Review undo recovery",
        "11. Help",
    )
    for choice in expected_choices:
        assert choice in result.stdout
    assert "Run macwise --help to see direct commands." in result.stdout


def test_root_help_explains_safety_examples_and_next_step() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Understand the software installed on this Mac" in result.stdout
    assert "does not remove or change anything" in result.stdout
    assert "Examples:" in result.stdout
    assert "macwise" in result.stdout
    assert "macwise scan" in result.stdout
    assert "Next:" in result.stdout
