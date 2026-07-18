import shutil
import sqlite3
from contextlib import closing
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

import macwise.cli as cli
from macwise.models import (
    AuditDocument,
    EntityType,
    PlanEligibility,
    PreflightKind,
    PreflightOutcome,
    SoftwareRecord,
)
from macwise.persistence import PlanStore
from macwise.services.planning import add_candidate

RUNNER = CliRunner()
NOW = datetime(2026, 7, 18, 0, 15, tzinfo=UTC)


def add(document: AuditDocument, subject_id: str, trash_root: Path):
    return add_candidate(
        None,
        document,
        subject_id,
        clock=lambda: NOW,
        plan_id_factory=lambda: "plan:test'; DROP TABLE plan_revisions; --",
        trash_root=trash_root,
    ).plan


def test_hostile_homebrew_token_is_raw_data_but_cannot_select_an_action(tmp_path: Path) -> None:
    marker = tmp_path / "marker"
    hostile_name = f"evil; touch {marker}"
    record = SoftwareRecord(
        id="homebrew_formula:hostile",
        entity_type=EntityType.HOMEBREW_FORMULA,
        name=hostile_name,
        display_name=hostile_name,
    )
    document = AuditDocument(audit_id="audit:hostile", collected_at=NOW, software=(record,))

    plan = add(document, record.id, tmp_path / "Trash")

    assert hostile_name in plan.model_dump_json()
    assert plan.candidates[0].homebrew_token is None
    assert plan.actions == ()
    assert plan.eligibility is PlanEligibility.BLOCKED
    assert any(
        item.kind is PreflightKind.IDENTITY and item.outcome is PreflightOutcome.BLOCK
        for item in plan.checks
    )
    assert not marker.exists()


def test_traversal_or_control_character_application_path_cannot_select_trash_action(
    tmp_path: Path,
) -> None:
    for index, hostile_path in enumerate(
        (
            "/Applications/../../private/tmp/Evil.app",
            "/Applications/Evil\x00.app",
        )
    ):
        record = SoftwareRecord(
            id=f"application:hostile-{index}",
            entity_type=EntityType.APPLICATION,
            name=f"Hostile {index}",
            display_name=f"Hostile {index}",
            install_path=hostile_path,
        )
        document = AuditDocument(
            audit_id=f"audit:hostile-{index}",
            collected_at=NOW,
            software=(record,),
        )

        plan = add(document, record.id, tmp_path / "Trash")

        assert plan.actions == ()
        assert plan.eligibility is PlanEligibility.BLOCKED


def test_sql_and_terminal_shaped_values_remain_inert_and_cannot_forge_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker = tmp_path / "executed"
    name = f"$(touch {marker})"
    display = "Visible App\n## Forged plan section\x1b[31m\u202e"
    record = SoftwareRecord(
        id="application:hostile",
        entity_type=EntityType.APPLICATION,
        name=name,
        display_name=display,
        install_path="/Applications/Visible App.app",
    )
    document = AuditDocument(audit_id="audit:hostile", collected_at=NOW, software=(record,))
    store = PlanStore(tmp_path / "state" / "macwise.db")

    class Service:
        def run(self, application_roots: tuple[Path, ...]) -> AuditDocument:
            assert application_roots
            return document

    monkeypatch.setattr(cli, "_service_factory", Service)
    monkeypatch.setattr(cli, "_plan_store_factory", lambda: store)
    monkeypatch.setattr(cli, "_planning_clock", lambda: NOW)
    monkeypatch.setattr(
        cli,
        "_plan_id_factory",
        lambda: "plan:test'; DROP TABLE plan_revisions; --",
    )
    monkeypatch.setattr(cli, "_trash_root_factory", lambda: tmp_path / "Trash")

    result = RUNNER.invoke(cli.app, ["plan", "add", name])

    assert result.exit_code == 0, result.stdout
    assert not marker.exists()
    assert "\x1b" not in result.stdout
    assert "\u202e" not in result.stdout
    assert "\n## Forged plan section" not in result.stdout
    with closing(sqlite3.connect(store.path)) as connection, connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        raw = connection.execute("SELECT document_json FROM plan_revisions").fetchone()[0]
    assert {"plan_revisions", "active_plan"} <= tables
    assert "## Forged plan section" in raw
    assert "DROP TABLE plan_revisions" in raw


def test_planning_and_local_state_write_do_not_call_host_mutation_apis(
    sample_audit: AuditDocument,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def forbidden(*_args: object, **_kwargs: object) -> None:
        calls.append("forbidden")
        raise AssertionError("host mutation API called")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(shutil, "move", forbidden)
    monkeypatch.setattr(shutil, "rmtree", forbidden)
    monkeypatch.setattr(Path, "rename", forbidden)
    monkeypatch.setattr(Path, "unlink", forbidden)

    state_root = tmp_path / "state"
    store = PlanStore(state_root / "macwise.db")
    target = sample_audit.software[0]
    plan = add(sample_audit, target.id, tmp_path / "Trash")
    store.append(plan)
    loaded = store.active()

    assert loaded == plan
    assert calls == []
    assert not (tmp_path / "Trash").exists()
    assert all(path == state_root or state_root in path.parents for path in tmp_path.rglob("*"))


def test_threat_model_names_persisted_plan_and_allowlisted_execution_boundaries() -> None:
    threat_model = (Path(__file__).parents[2] / "docs" / "threat-model.md").read_text(
        encoding="utf-8"
    )
    normalized = threat_model.casefold()

    assert "sqlite" in normalized
    assert "persisted plan" in normalized
    assert "not execution authority" in normalized
    assert "revalidate" in normalized
    assert "phase 5" in normalized
    assert "allowlisted" in normalized
    assert "not exit status" in normalized
