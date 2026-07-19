from pathlib import Path

import pytest
from typer.testing import CliRunner

import macwise.cli as cli
from macwise.models import AuditDocument
from macwise.persistence import PlanStore

RUNNER = CliRunner()


class CountingAuditService:
    def __init__(self, audit: AuditDocument) -> None:
        self.audit = audit
        self.calls = 0

    def run(self, application_roots: tuple[Path, ...]) -> AuditDocument:
        assert application_roots
        self.calls += 1
        return self.audit


@pytest.fixture
def checkup_service(
    sample_audit: AuditDocument, monkeypatch: pytest.MonkeyPatch
) -> CountingAuditService:
    service = CountingAuditService(sample_audit)
    monkeypatch.setattr(cli, "_service_factory", lambda: service)
    return service


def test_checkup_collects_fresh_evidence_and_renders_bounded_actionable_summary(
    checkup_service: CountingAuditService,
) -> None:
    result = RUNNER.invoke(cli.app, ["checkup"])

    assert result.exit_code == 0, result.stdout
    assert checkup_service.calls == 1
    assert "Fresh read-only checkup" in result.stdout
    assert "Collected:" in result.stdout
    assert "What deserves attention first" in result.stdout
    assert "Why:" in result.stdout
    assert "Evidence:" in result.stdout
    assert "Possible benefit:" in result.stdout
    assert "What this does not prove:" in result.stdout
    assert "Safest next step:" in result.stdout
    assert "Confidence in this report" in result.stdout
    assert "largest missing evidence" in result.stdout.casefold()
    assert "MacWise changed nothing on this Mac" in result.stdout
    assert max(map(len, result.stdout.splitlines())) <= 100


def test_interactive_checkup_reuses_one_audit_and_finishes_with_session_summary(
    checkup_service: CountingAuditService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "_is_interactive", lambda: True)

    result = RUNNER.invoke(cli.app, input="1\n1\n0\n0\n")

    assert result.exit_code == 0, result.stdout
    assert checkup_service.calls == 1
    assert "Recommended" in result.stdout
    assert "Focused review" in result.stdout
    assert "Session summary" in result.stdout
    assert "Reviewed: 1 priority" in result.stdout
    assert result.stdout.count("Choose a finding number to review, or 0 to finish safely.") == 2
    assert "No cleanup plan was created" in result.stdout
    assert "MacWise changed nothing on this Mac" in result.stdout
    assert max(map(len, result.stdout.splitlines())) <= 100


def test_interactive_checkup_can_stop_without_reviewing_or_changing_anything(
    checkup_service: CountingAuditService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "_is_interactive", lambda: True)

    result = RUNNER.invoke(cli.app, input="1\n0\n")

    assert result.exit_code == 0, result.stdout
    assert checkup_service.calls == 1
    assert "Reviewed: 0 priorities" in result.stdout
    assert "You can stop here safely" in result.stdout
    assert "MacWise changed nothing on this Mac" in result.stdout


def test_unknown_focus_offers_verified_facts_without_web_search_or_second_scan(
    checkup_service: CountingAuditService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "_is_interactive", lambda: True)

    result = RUNNER.invoke(cli.app, input="1\n1\n1\n1\n0\n")

    assert result.exit_code == 0, result.stdout
    assert checkup_service.calls == 1
    assert "Unknown-item choices" in result.stdout
    assert "Verified local facts" in result.stdout
    assert "Example App" in result.stdout
    assert "MacWise did not search the web or upload this inventory" in result.stdout


def test_unknown_focus_accepts_session_only_user_context(
    checkup_service: CountingAuditService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "_is_interactive", lambda: True)

    result = RUNNER.invoke(
        cli.app,
        input="1\n1\n1\n2\nI use this for class projects\n0\n",
    )

    assert result.exit_code == 0, result.stdout
    assert checkup_service.calls == 1
    assert "User-confirmed for this session" in result.stdout
    assert "not saved" in result.stdout


def test_unknown_focus_can_create_plan_preview_without_applying(
    checkup_service: CountingAuditService,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    store = PlanStore(tmp_path / "state" / "macwise.db")
    monkeypatch.setattr(cli, "_is_interactive", lambda: True)
    monkeypatch.setattr(cli, "_plan_store_factory", lambda: store)
    monkeypatch.setattr(cli, "_trash_root_factory", lambda: tmp_path / "Trash")

    result = RUNNER.invoke(cli.app, input="1\n1\n1\n4\n0\n")

    assert result.exit_code == 0, result.stdout
    assert checkup_service.calls == 1
    assert store.active() is not None
    assert "Cleanup plan preview" in result.stdout
    assert "A plan was created, but it was not applied" in result.stdout
    assert "Type the exact approval phrase" not in result.stdout
