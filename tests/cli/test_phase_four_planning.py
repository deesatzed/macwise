import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

import macwise.cli as cli
from macwise.models import AuditDocument, EntityType, SoftwareRecord, StartupKind, StartupRecord
from macwise.persistence import PlanStore

RUNNER = CliRunner()
NOW = datetime(2026, 7, 18, 0, 0, tzinfo=UTC)


class StaticAuditService:
    def __init__(self, audit: AuditDocument) -> None:
        self.audit = audit
        self.calls = 0

    def run(self, application_roots: tuple[Path, ...]) -> AuditDocument:
        assert application_roots
        self.calls += 1
        return self.audit


@pytest.fixture
def planning_cli(
    sample_audit: AuditDocument,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[PlanStore, StaticAuditService, AuditDocument]:
    store = PlanStore(tmp_path / "state" / "macwise.db")
    service = StaticAuditService(sample_audit)
    monkeypatch.setattr(cli, "_service_factory", lambda: service)
    monkeypatch.setattr(cli, "_plan_store_factory", lambda: store)
    monkeypatch.setattr(cli, "_planning_clock", lambda: NOW)
    monkeypatch.setattr(cli, "_plan_id_factory", lambda: "plan:cli-test")
    monkeypatch.setattr(cli, "_trash_root_factory", lambda: Path("/Users/example/.Trash"))
    return store, service, sample_audit


def test_plan_and_show_without_state_are_read_only_and_explain_next_step(
    planning_cli: tuple[PlanStore, StaticAuditService, AuditDocument],
) -> None:
    store, service, _audit = planning_cli

    root = RUNNER.invoke(cli.app, ["plan"])
    shown = RUNNER.invoke(cli.app, ["plan", "show"])

    assert root.exit_code == 0, root.stdout
    assert shown.exit_code == 0, shown.stdout
    assert "No active cleanup plan exists" in root.stdout
    assert "macwise plan add NAME" in root.stdout
    assert "No changes were made" in root.stdout
    assert service.calls == 0
    assert not store.path.exists()


def test_plan_add_persists_and_renders_exact_preview_preflight_and_rollback(
    planning_cli: tuple[PlanStore, StaticAuditService, AuditDocument],
) -> None:
    store, service, _audit = planning_cli

    result = RUNNER.invoke(cli.app, ["plan", "add", "app:Example"])

    assert result.exit_code == 0, result.stdout
    assert service.calls == 1
    assert store.active() is not None
    assert "Added Example App to cleanup plan revision 1" in result.stdout
    assert "Cleanup plan preview" in result.stdout
    assert "Plan: plan:cli-test — revision 1" in result.stdout
    assert "Eligibility: preview ready" in result.stdout
    assert "Preview: move application bundle" in result.stdout
    assert "/Applications/Example.app" in result.stdout
    assert "/Users/example/.Trash/" in result.stdout
    assert "Blockers" in result.stdout
    assert "- None." in result.stdout
    assert "Warnings" in result.stdout
    assert "Observed passes" in result.stdout
    assert "Rollback: reversible" in result.stdout
    assert "Related data records preserved: 0" in result.stdout
    assert "Startup records left unchanged: 0" in result.stdout
    assert "This preview is not approval" in result.stdout
    assert "No changes were made" in result.stdout


def test_plan_add_can_explicitly_preview_supported_startup_before_removal(
    planning_cli: tuple[PlanStore, StaticAuditService, AuditDocument],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, _service, base = planning_cli
    startup = StartupRecord(
        id="startup:cli-agent",
        label="com.example.agent",
        kind=StartupKind.LAUNCH_AGENT,
        source_path="/Users/example/Library/LaunchAgents/com.example.agent.plist",
        owner_software_ids=(base.software[0].id,),
        enabled=True,
    )
    service = StaticAuditService(base.model_copy(update={"startup": (startup,)}))
    monkeypatch.setattr(cli, "_service_factory", lambda: service)

    result = RUNNER.invoke(
        cli.app,
        ["plan", "add", "--include-startup", "app:Example"],
    )

    assert result.exit_code == 0, result.stdout
    active = store.active()
    assert active is not None
    assert [item.kind for item in active.actions] == [
        cli.PlanActionKind.DISABLE_LAUNCH_AGENT,
        cli.PlanActionKind.MOVE_APPLICATION_TO_TRASH,
    ]
    assert result.stdout.index("disable user LaunchAgent") < result.stdout.index(
        "move application bundle"
    )
    assert "com.example.agent" in result.stdout


def test_duplicate_add_is_idempotent_and_second_subject_appends_revision(
    planning_cli: tuple[PlanStore, StaticAuditService, AuditDocument],
) -> None:
    store, _service, _audit = planning_cli

    first = RUNNER.invoke(cli.app, ["plan", "add", "app:Example"])
    duplicate = RUNNER.invoke(cli.app, ["plan", "add", "app:Example"])
    second = RUNNER.invoke(cli.app, ["plan", "add", "formula:openssl@3"])

    assert first.exit_code == 0
    assert duplicate.exit_code == 0
    assert "already appears in cleanup plan revision 1" in duplicate.stdout
    assert second.exit_code == 0, second.stdout
    assert "revision 2" in second.stdout
    active = store.active()
    assert active is not None and active.revision == 2
    assert len(active.candidates) == 2
    assert active.eligibility.value == "blocked"


def test_missing_or_ambiguous_target_refuses_without_writing_state(
    planning_cli: tuple[PlanStore, StaticAuditService, AuditDocument],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store, _service, base = planning_cli
    cask = SoftwareRecord(
        id="homebrew_cask:example",
        entity_type=EntityType.HOMEBREW_CASK,
        name="Example",
        display_name="Example App",
    )
    monkeypatch.setattr(
        cli,
        "_service_factory",
        lambda: StaticAuditService(base.model_copy(update={"software": (*base.software, cask)})),
    )

    missing = RUNNER.invoke(cli.app, ["plan", "add", "Does Not Exist"])
    ambiguous = RUNNER.invoke(cli.app, ["plan", "add", "Example"])

    assert missing.exit_code == 2
    assert "did not find" in missing.stdout
    assert ambiguous.exit_code == 2
    assert "more than one possible match" in ambiguous.stdout
    assert store.active() is None
    assert not store.path.exists()


def test_exact_dependency_is_saved_as_blocked_not_rejected(
    planning_cli: tuple[PlanStore, StaticAuditService, AuditDocument],
) -> None:
    store, _service, _audit = planning_cli

    result = RUNNER.invoke(cli.app, ["plan", "add", "formula:openssl@3"])

    assert result.exit_code == 0, result.stdout
    assert "Eligibility: blocked" in result.stdout
    assert "Homebrew recorded this item as a dependency" in result.stdout
    active = store.active()
    assert active is not None and active.eligibility.value == "blocked"


def test_plan_show_reads_saved_snapshot_without_running_collectors(
    planning_cli: tuple[PlanStore, StaticAuditService, AuditDocument],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    added = RUNNER.invoke(cli.app, ["plan", "add", "app:Example"])
    assert added.exit_code == 0

    class FailingService:
        def run(self, application_roots: tuple[Path, ...]) -> AuditDocument:
            del application_roots
            raise AssertionError("plan show must not scan")

    monkeypatch.setattr(cli, "_service_factory", FailingService)
    shown = RUNNER.invoke(cli.app, ["plan", "show"])

    assert shown.exit_code == 0, shown.stdout
    assert "Cleanup plan preview" in shown.stdout
    assert "Example App" in shown.stdout


def test_store_errors_fail_closed_with_recovery_message(
    sample_audit: AuditDocument,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = tmp_path / "future.db"
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute("PRAGMA user_version = 2")
    monkeypatch.setattr(cli, "_plan_store_factory", lambda: PlanStore(database))

    result = RUNNER.invoke(cli.app, ["plan", "show"])

    assert result.exit_code == 2
    assert "could not read local planning state" in result.stdout
    assert "newer MacWise schema" not in result.stdout
    assert "Move or back up" in result.stdout


def test_apply_refuses_when_fresh_source_no_longer_matches_preview(
    planning_cli: tuple[PlanStore, StaticAuditService, AuditDocument],
) -> None:
    added = RUNNER.invoke(cli.app, ["plan", "add", "app:Example"])
    assert added.exit_code == 0

    result = RUNNER.invoke(cli.app, ["apply"])

    assert result.exit_code == 2
    assert "Fresh host evidence no longer matches" in result.stdout
    assert "fresh plan revision" in result.stdout
    assert "No changes were made" in result.stdout
