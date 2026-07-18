from pathlib import Path

import pytest
from typer.testing import CliRunner

import macwise.cli as cli
from macwise.models import AuditDocument
from macwise.persistence import PlanStore

runner = CliRunner()


class GuidedService:
    def __init__(self, audit: AuditDocument) -> None:
        self.audit = audit
        self.called = False

    def run(self, application_roots: tuple[Path, ...]) -> AuditDocument:
        assert application_roots
        self.called = True
        return self.audit


def test_interactive_guided_scan_routes_to_the_same_audit_service(
    sample_audit: AuditDocument,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = GuidedService(sample_audit)
    monkeypatch.setattr(cli, "_service_factory", lambda: service)
    monkeypatch.setattr(cli, "_is_interactive", lambda: True)

    result = runner.invoke(cli.app, input="1\n")

    assert result.exit_code == 0, result.stdout
    assert service.called is True
    assert "What would you like to do?" in result.stdout
    assert "Example App" in result.stdout


def test_noninteractive_guided_menu_never_prompts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "_is_interactive", lambda: False)

    result = runner.invoke(cli.app)

    assert result.exit_code == 0
    assert "Choose 1-11" not in result.stdout
    assert "Run macwise --help to see direct commands." in result.stdout


def test_interactive_choice_eight_routes_to_real_plan_view_without_scanning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "_is_interactive", lambda: True)
    monkeypatch.setattr(
        cli,
        "_plan_store_factory",
        lambda: PlanStore(tmp_path / "state" / "macwise.db"),
    )

    result = runner.invoke(cli.app, input="8\n")

    assert result.exit_code == 0, result.stdout
    assert "No active cleanup plan exists" in result.stdout
    assert "macwise plan add NAME" in result.stdout


def test_interactive_choice_nine_routes_to_scorecard(
    sample_audit: AuditDocument,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "_is_interactive", lambda: True)
    monkeypatch.setattr(cli, "_service_factory", lambda: GuidedService(sample_audit))

    result = runner.invoke(cli.app, input="9\n")

    assert result.exit_code == 0, result.stdout
    assert "Opportunity Profile" in result.stdout
    assert "MacWise Usefulness Score" in result.stdout


def test_interactive_choice_ten_exposes_undo_without_auto_approval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "_is_interactive", lambda: True)

    result = runner.invoke(cli.app, input="10\n")

    assert result.exit_code == 0, result.stdout
    assert "macwise undo" in result.stdout
    assert "separate approval" in result.stdout
    assert "Type the exact approval phrase" not in result.stdout
