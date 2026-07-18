import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

import macwise.cli as cli
from macwise.models import (
    ActionObservation,
    AuditDocument,
    CollectorState,
    CollectorStatus,
    EntityType,
    SoftwareRecord,
)
from macwise.persistence import PlanStore
from macwise.services import RevalidationError, add_candidate

NOW = datetime(2026, 7, 18, 7, 0, tzinfo=UTC)
RUNNER = CliRunner()
COMPLETE_COLLECTORS = tuple(
    CollectorStatus(
        collector=name,
        state=CollectorState.COMPLETE,
        collected_at=NOW,
        records_count=1,
    )
    for name in ("applications", "usage", "backups", "overlap")
)


def test_external_manual_app_is_refused_before_approval_or_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "ExternalApps" / "Example.app"
    trash = tmp_path / ".Trash"
    source.mkdir(parents=True)
    trash.mkdir()
    record = SoftwareRecord(
        id="application:external",
        entity_type=EntityType.APPLICATION,
        name="External",
        display_name="External",
        install_path=str(source),
    )
    audit = AuditDocument(
        audit_id="audit:external",
        collected_at=NOW,
        software=(record,),
        collectors=COMPLETE_COLLECTORS,
    )
    plan = add_candidate(
        None,
        audit,
        record.id,
        clock=lambda: NOW,
        plan_id_factory=lambda: "plan:external",
        trash_root=trash,
    ).plan
    monkeypatch.setattr(cli, "_trash_root_factory", lambda: trash)

    with pytest.raises(RevalidationError, match="outside the live execution allowlist"):
        cli.prepare_execution_for_cli(plan, audit)


def test_refusal_and_help_paths_never_cross_a_live_mutation_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        raise AssertionError(f"unexpected live subprocess: {args!r} {kwargs!r}")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(
        cli,
        "_plan_store_factory",
        lambda: PlanStore(tmp_path / "state" / "macwise.db"),
    )
    monkeypatch.setattr(cli, "_is_interactive", lambda: False)

    apply = RUNNER.invoke(cli.app, ["apply", "--approve", "APPLY AAAAAAAAAAAAAAAA"])
    undo = RUNNER.invoke(cli.app, ["undo", "--approve", "UNDO AAAAAAAAAAAAAAAA"])
    help_result = RUNNER.invoke(cli.app, ["apply", "--help"])

    assert apply.exit_code == 2
    assert undo.exit_code == 2
    assert help_result.exit_code == 0
    assert "No active cleanup plan" in apply.stdout
    assert "No MacWise execution manifest" in undo.stdout


def test_filesystem_observation_does_not_follow_a_missing_target() -> None:
    observation = cli.filesystem_observation(Path("/definitely/missing/MacWise.app"))

    assert observation == ActionObservation(exists=False)


def test_filesystem_observation_normalizes_unreadable_bundle_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = tmp_path / "Unreadable.app"
    bundle.mkdir()

    def unreadable(_path: Path) -> str:
        raise cli.FilesystemActionError("synthetic unreadable metadata")

    monkeypatch.setattr(cli, "application_identity_digest", unreadable)

    assert cli.filesystem_observation(bundle) == ActionObservation(exists=None)
