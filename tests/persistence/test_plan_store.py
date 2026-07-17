import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from macwise.models import (
    EntityType,
    InstallRole,
    PlanActionKind,
    PlanCandidate,
    PlanDocument,
    PlanEligibility,
    PlannedAction,
    PreflightCheck,
    PreflightKind,
    PreflightOutcome,
    RollbackBlueprint,
    RollbackFeasibility,
)
from macwise.persistence import PlanStore, PlanStoreError

NOW = datetime(2026, 7, 17, 23, 50, tzinfo=UTC)


def plan(revision: int = 1) -> PlanDocument:
    candidate = PlanCandidate(
        subject_id="application:example",
        source_audit_id=f"audit:{revision}",
        source_audit_collected_at=NOW,
        entity_type=EntityType.APPLICATION,
        display_name="Example App",
        version="2.4.1",
        install_path="/Applications/Example.app",
        install_role=InstallRole.EXPLICIT,
    )
    action = PlannedAction(
        id="action:example",
        subject_id=candidate.subject_id,
        kind=PlanActionKind.MOVE_APPLICATION_TO_TRASH,
        source_path="/Applications/Example.app",
        destination_path="/Users/example/.Trash/Example.app.macwise-test",
    )
    check = PreflightCheck(
        id=f"check:{revision}",
        subject_id=candidate.subject_id,
        kind=PreflightKind.IDENTITY,
        outcome=PreflightOutcome.PASS,
        statement="An exact typed action identity is available.",
    )
    rollback = RollbackBlueprint(
        id="rollback:example",
        action_id=action.id,
        feasibility=RollbackFeasibility.REVERSIBLE,
        strategy="Restore the same bundle to its original path.",
        original_path="/Applications/Example.app",
        restore_path="/Applications/Example.app",
    )
    return PlanDocument(
        plan_id="plan:test",
        revision=revision,
        created_at=NOW,
        source_audit_id=f"audit:{revision}",
        source_audit_collected_at=NOW,
        candidates=(candidate,),
        actions=(action,),
        checks=(check,),
        rollback=(rollback,),
        eligibility=PlanEligibility.PREVIEW_READY,
        limitations=("This preview is not approval to make changes.",),
    )


def test_construction_is_read_only_and_first_append_creates_versioned_store(
    tmp_path: Path,
) -> None:
    database = tmp_path / "state" / "macwise.db"
    store = PlanStore(database)

    assert not database.exists()
    assert store.active() is None
    assert not database.exists()

    store.append(plan())

    assert database.is_file()
    with sqlite3.connect(database) as connection:
        version = connection.execute("PRAGMA user_version").fetchone()
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    assert version == (1,)
    assert {"plan_revisions", "active_plan"} <= tables


def test_append_and_active_round_trip_canonical_json_with_integrity_digest(
    tmp_path: Path,
) -> None:
    database = tmp_path / "macwise.db"
    store = PlanStore(database)
    expected = plan()

    store.append(expected)

    assert store.active() == expected
    with sqlite3.connect(database) as connection:
        document_json, digest = connection.execute(
            "SELECT document_json, document_sha256 FROM plan_revisions"
        ).fetchone()
    loaded = json.loads(document_json)
    assert document_json == json.dumps(
        loaded,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert digest == hashlib.sha256(document_json.encode()).hexdigest()


def test_revisions_are_append_only_and_only_active_pointer_advances(tmp_path: Path) -> None:
    database = tmp_path / "macwise.db"
    store = PlanStore(database)

    store.append(plan(1))
    store.append(plan(2))

    assert store.active() == plan(2)
    with sqlite3.connect(database) as connection:
        revisions = connection.execute(
            "SELECT revision FROM plan_revisions ORDER BY revision"
        ).fetchall()
        active = connection.execute(
            "SELECT plan_id, revision FROM active_plan WHERE singleton_id = 1"
        ).fetchone()
    assert revisions == [(1,), (2,)]
    assert active == ("plan:test", 2)

    with pytest.raises(PlanStoreError, match="already exists"):
        store.append(plan(2))
    assert store.active() == plan(2)


def test_tampered_digest_and_malformed_document_fail_closed(tmp_path: Path) -> None:
    database = tmp_path / "macwise.db"
    store = PlanStore(database)
    store.append(plan())

    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE plan_revisions SET document_json = ?",
            ('{"schema_version":1}',),
        )
        connection.commit()
    with pytest.raises(PlanStoreError, match="integrity"):
        store.active()

    malformed = '{"schema_version":1}'
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE plan_revisions SET document_json = ?, document_sha256 = ?",
            (malformed, hashlib.sha256(malformed.encode()).hexdigest()),
        )
        connection.commit()
    with pytest.raises(PlanStoreError, match="invalid"):
        store.active()


def test_future_database_schema_refuses_without_mutation(tmp_path: Path) -> None:
    database = tmp_path / "future.db"
    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA user_version = 2")

    store = PlanStore(database)
    with pytest.raises(PlanStoreError, match="newer"):
        store.active()
    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (2,)


def test_reading_existing_zero_version_database_does_not_initialize_or_mutate_it(
    tmp_path: Path,
) -> None:
    database = tmp_path / "empty.db"
    database.touch()
    store = PlanStore(database)

    assert store.active() is None
    assert database.read_bytes() == b""


def test_reading_unknown_zero_version_schema_refuses_without_mutation(tmp_path: Path) -> None:
    database = tmp_path / "unknown.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE unrelated (value TEXT NOT NULL)")
    before = database.read_bytes()

    with pytest.raises(PlanStoreError, match="schema is not supported"):
        PlanStore(database).active()

    assert database.read_bytes() == before


def test_competing_initial_plan_cannot_replace_active_pointer(tmp_path: Path) -> None:
    database = tmp_path / "macwise.db"
    store = PlanStore(database)
    first = plan(1)
    competing = plan(1).model_copy(update={"plan_id": "plan:competing"})
    store.append(first)

    with pytest.raises(PlanStoreError, match="active plan changed"):
        store.append(competing)

    assert store.active() == first
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM plan_revisions").fetchone() == (1,)


def test_transaction_failure_preserves_prior_active_revision(tmp_path: Path) -> None:
    database = tmp_path / "macwise.db"
    store = PlanStore(database)
    store.append(plan(1))
    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            CREATE TRIGGER reject_active_update
            BEFORE UPDATE ON active_plan
            BEGIN
                SELECT RAISE(ABORT, 'synthetic transaction failure');
            END
            """
        )

    with pytest.raises(PlanStoreError, match="could not append"):
        store.append(plan(2))

    assert store.active() == plan(1)
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM plan_revisions").fetchone() == (1,)


def test_symlink_database_and_non_directory_parent_refuse(tmp_path: Path) -> None:
    target = tmp_path / "target.db"
    target.touch()
    symlink = tmp_path / "linked.db"
    symlink.symlink_to(target)

    with pytest.raises(PlanStoreError, match="symbolic link"):
        PlanStore(symlink).active()

    not_a_directory = tmp_path / "state"
    not_a_directory.write_text("not a directory", encoding="utf-8")
    with pytest.raises(PlanStoreError, match="directory"):
        PlanStore(not_a_directory / "macwise.db").append(plan())


def test_nested_existing_ancestor_symlink_cannot_redirect_state_write(tmp_path: Path) -> None:
    injected_root = tmp_path / "injected"
    outside_root = tmp_path / "outside"
    injected_root.mkdir()
    outside_root.mkdir()
    link = injected_root / "linked"
    link.symlink_to(outside_root, target_is_directory=True)
    database = link / "nested" / "macwise.db"

    with pytest.raises(PlanStoreError, match="symbolic link"):
        PlanStore(database).append(plan())

    assert not (outside_root / "nested").exists()
