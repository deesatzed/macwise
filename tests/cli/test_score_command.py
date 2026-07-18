import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

import macwise.cli as cli
from macwise.models import AuditDocument, MacWiseScorecard

RUNNER = CliRunner()


class StaticAuditService:
    def __init__(self, audit: AuditDocument) -> None:
        self.audit = audit

    def run(self, application_roots: tuple[Path, ...]) -> AuditDocument:
        assert application_roots
        return self.audit


@pytest.fixture
def score_cli(sample_audit: AuditDocument, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "_service_factory", lambda: StaticAuditService(sample_audit))
    monkeypatch.setattr(cli, "_now", lambda: datetime(2026, 7, 18, 12, 0, tzinfo=UTC))


def test_score_terminal_is_read_only_explains_both_scores_and_next_steps(
    score_cli: None,
) -> None:
    del score_cli
    result = RUNNER.invoke(cli.app, ["score"])

    assert result.exit_code == 0, result.stdout
    assert "Opportunity Profile" in result.stdout
    assert "MacWise Usefulness Score" in result.stdout
    assert "Evidence coverage" in result.stdout
    assert "does not grade this Mac" in result.stdout
    assert "does not prove personalized correctness" in result.stdout
    assert "This command is read-only" in result.stdout
    assert "macwise startup" in result.stdout


@pytest.mark.parametrize("output_format", ("json", "markdown", "terminal"))
def test_score_supports_all_public_formats(score_cli: None, output_format: str) -> None:
    del score_cli
    result = RUNNER.invoke(cli.app, ["score", "--format", output_format])

    assert result.exit_code == 0, result.stdout
    if output_format == "json":
        payload = json.loads(result.stdout)
        assert payload["opportunity_score"] >= 0
        assert payload["usefulness_score"] >= 0
        assert "Example App" not in result.stdout
        assert "/Applications" not in result.stdout
    else:
        assert "Opportunity Profile" in result.stdout
        assert "MacWise Usefulness Score" in result.stdout


def test_score_writes_only_to_explicit_new_output_and_refuses_overwrite(
    score_cli: None, tmp_path: Path
) -> None:
    del score_cli
    output = tmp_path / "score.json"
    first = RUNNER.invoke(cli.app, ["score", "--format", "json", "--output", str(output)])

    assert first.exit_code == 0, first.stdout
    assert "Saved the read-only scorecard" in first.stdout
    MacWiseScorecard.model_validate_json(output.read_text(encoding="utf-8"))

    second = RUNNER.invoke(cli.app, ["score", "--format", "json", "--output", str(output)])
    assert second.exit_code == 2
    assert "already exists" in second.stdout
    assert "--force" in second.stdout
