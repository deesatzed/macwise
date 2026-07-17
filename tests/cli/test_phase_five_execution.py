from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

import macwise.cli as cli
from macwise.models import (
    ActionObservation,
    ActionState,
    AuditDocument,
    EntityType,
    ExecutionAction,
    ExecutionRun,
    ExecutionState,
    InverseIntent,
    InverseKind,
    PlanDocument,
    SoftwareRecord,
    VerificationState,
)
from macwise.persistence import PlanStore, execution_digest, plan_digest
from macwise.services import ExecutionServiceError, PreparedExecution, add_candidate
from macwise.system.commands import CommandResult, CommandState, ReadCommand

RUNNER = CliRunner()
NOW = datetime(2026, 7, 18, 6, 0, tzinfo=UTC)


class StaticAuditService:
    def __init__(self, audit: AuditDocument) -> None:
        self.audit = audit
        self.calls = 0

    def run(self, application_roots: tuple[Path, ...]) -> AuditDocument:
        assert application_roots
        self.calls += 1
        return self.audit


class FakeExecutionService:
    def __init__(self, plan: PlanDocument, prepared: PreparedExecution) -> None:
        self.plan = plan
        self.prepared = prepared
        self.apply_approvals: list[str] = []
        self.undo_approvals: list[str] = []
        self.current: ExecutionRun | None = None

    def build_run(self, *, undone: bool) -> ExecutionRun:
        actions = tuple(
            ExecutionAction.model_validate(
                {
                    **action.model_dump(),
                    "state": ActionState.UNDONE if undone else ActionState.VERIFIED,
                    "verification": VerificationState.VERIFIED,
                    "after": ActionObservation(
                        exists=True,
                        device=action.before.device,
                        inode=action.before.inode,
                        identity_digest=action.before.identity_digest,
                    ),
                }
            )
            for action in self.prepared.actions
        )
        return ExecutionRun(
            run_id="run:cli",
            manifest_revision=5 if undone else 3,
            plan_id=self.plan.plan_id,
            plan_revision=self.plan.revision,
            plan_digest=plan_digest(self.plan),
            approval_fingerprint=plan_digest(self.plan)[:16].upper(),
            created_at=NOW,
            updated_at=NOW,
            state=ExecutionState.UNDONE if undone else ExecutionState.SUCCEEDED,
            actions=actions,
            limitations=self.plan.limitations,
        )

    def apply(self, prepared: PreparedExecution, *, approval: str) -> ExecutionRun:
        assert prepared == self.prepared
        self.apply_approvals.append(approval)
        self.current = self.build_run(undone=False)
        return self.current

    def active(self) -> ExecutionRun | None:
        return self.current

    def undo(self, *, approval: str) -> ExecutionRun:
        self.undo_approvals.append(approval)
        self.current = self.build_run(undone=True)
        return self.current


@pytest.fixture
def execution_cli(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[PlanStore, FakeExecutionService, PreparedExecution]:
    trash = tmp_path / ".Trash"
    record = SoftwareRecord(
        id="application:example",
        entity_type=EntityType.APPLICATION,
        name="Example",
        display_name="Example App",
        install_path="/Applications/Example.app",
    )
    audit = AuditDocument(audit_id="audit:cli-exec", collected_at=NOW, software=(record,))
    plan = add_candidate(
        None,
        audit,
        record.id,
        clock=lambda: NOW,
        plan_id_factory=lambda: "plan:cli-exec",
        trash_root=trash,
    ).plan
    planned = plan.actions[0]
    prepared_action = ExecutionAction(
        plan_action_id=planned.id,
        sequence=planned.sequence or 0,
        subject_id=planned.subject_id,
        kind=planned.kind,
        state=ActionState.PENDING,
        verification=VerificationState.PENDING,
        before=ActionObservation(
            exists=True,
            device=1,
            inode=42,
            identity_digest="a" * 64,
        ),
        inverse=InverseIntent(
            kind=InverseKind.RESTORE_FROM_TRASH,
            source_path=planned.destination_path,
            destination_path=planned.source_path,
        ),
    )
    prepared = PreparedExecution(
        plan_digest=plan_digest(plan),
        actions=(prepared_action,),
    )
    store = PlanStore(tmp_path / "state" / "macwise.db")
    store.append(plan)
    service = FakeExecutionService(plan, prepared)
    monkeypatch.setattr(cli, "_service_factory", lambda: StaticAuditService(audit))
    monkeypatch.setattr(cli, "_plan_store_factory", lambda: store)
    monkeypatch.setattr(cli, "_trash_root_factory", lambda: trash)

    def execution_preparer(
        _plan: PlanDocument,
        _audit: AuditDocument,
    ) -> PreparedExecution:
        return prepared

    def execution_service_factory(_store: PlanStore) -> FakeExecutionService:
        return service

    monkeypatch.setattr(cli, "_execution_preparer", execution_preparer)
    monkeypatch.setattr(cli, "_execution_service_factory", execution_service_factory)
    monkeypatch.setattr(cli, "_is_interactive", lambda: False)
    return store, service, prepared


def test_noninteractive_apply_requires_exact_explicit_approval(
    execution_cli: tuple[PlanStore, FakeExecutionService, PreparedExecution],
) -> None:
    _store, service, prepared = execution_cli
    missing = RUNNER.invoke(cli.app, ["apply"])
    wrong = RUNNER.invoke(cli.app, ["apply", "--approve", "APPLY WRONG"])

    assert missing.exit_code == 2
    assert "--approve" in missing.stdout
    assert f"APPLY {prepared.plan_digest[:16].upper()}" in missing.stdout
    assert wrong.exit_code == 2
    assert "does not exactly match" in wrong.stdout
    assert service.apply_approvals == []

    approved = f"APPLY {prepared.plan_digest[:16].upper()}"
    result = RUNNER.invoke(cli.app, ["apply", "--approve", approved])

    assert result.exit_code == 0, result.stdout
    assert service.apply_approvals == [approved]
    assert "Execution succeeded" in result.stdout
    assert "macwise undo" in result.stdout


def test_interactive_apply_shows_plan_before_prompting(
    execution_cli: tuple[PlanStore, FakeExecutionService, PreparedExecution],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _store, service, prepared = execution_cli
    monkeypatch.setattr(cli, "_is_interactive", lambda: True)
    approved = f"APPLY {prepared.plan_digest[:16].upper()}"

    result = RUNNER.invoke(cli.app, ["apply"], input=f"{approved}\n")

    assert result.exit_code == 0, result.stdout
    assert result.stdout.index("Cleanup plan preview") < result.stdout.index("Approval required")
    assert service.apply_approvals == [approved]


def test_undo_requires_active_success_and_separate_exact_approval(
    execution_cli: tuple[PlanStore, FakeExecutionService, PreparedExecution],
) -> None:
    _store, service, prepared = execution_cli
    apply_phrase = f"APPLY {prepared.plan_digest[:16].upper()}"
    applied_result = RUNNER.invoke(cli.app, ["apply", "--approve", apply_phrase])
    assert applied_result.exit_code == 0
    active = service.active()
    assert active is not None
    undo_phrase = f"UNDO {execution_digest(active)[:16].upper()}"

    missing = RUNNER.invoke(cli.app, ["undo"])
    assert missing.exit_code == 2
    assert undo_phrase in missing.stdout
    assert service.undo_approvals == []

    undone = RUNNER.invoke(cli.app, ["undo", "--approve", undo_phrase])

    assert undone.exit_code == 0, undone.stdout
    assert service.undo_approvals == [undo_phrase]
    assert "Undo succeeded" in undone.stdout


def test_apply_without_plan_refuses_before_scan_or_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = PlanStore(tmp_path / "state" / "macwise.db")
    monkeypatch.setattr(cli, "_plan_store_factory", lambda: store)
    monkeypatch.setattr(cli, "_is_interactive", lambda: False)

    result = RUNNER.invoke(cli.app, ["apply", "--approve", "APPLY AAAAAAAAAAAAAAAA"])

    assert result.exit_code == 2
    assert "No active cleanup plan" in result.stdout
    assert not store.path.exists()


def test_launchctl_read_probe_uses_override_and_running_evidence_without_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter(
        (
            CommandResult(
                command=ReadCommand.LAUNCHCTL,
                state=CommandState.COMPLETE,
                stdout='disabled services = { "com.example.agent" => true }',
                stderr="",
                return_code=0,
                duration_seconds=0,
            ),
            CommandResult(
                command=ReadCommand.LAUNCHCTL,
                state=CommandState.FAILED,
                stdout="",
                stderr="bounded synthetic failure",
                return_code=113,
                duration_seconds=0,
            ),
        )
    )
    calls: list[tuple[ReadCommand, tuple[str, ...]]] = []

    def fake_read(
        command: ReadCommand,
        arguments: tuple[str, ...],
    ) -> CommandResult:
        calls.append((command, arguments))
        return next(responses)

    monkeypatch.setattr(cli, "run_read_command", fake_read)

    state = cli.LiveActionObserver.launchctl_state(
        "com.example.agent",
        default_enabled=True,
    )

    assert state == (False, False)
    assert calls == [
        (ReadCommand.LAUNCHCTL, ("print-disabled", f"gui/{cli.os.getuid()}")),
        (ReadCommand.LAUNCHCTL, ("print", f"gui/{cli.os.getuid()}/com.example.agent")),
    ]


def test_apply_failure_reports_durable_recovery_state(
    execution_cli: tuple[PlanStore, FakeExecutionService, PreparedExecution],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _store, service, prepared = execution_cli

    def failed_apply(
        _prepared: PreparedExecution,
        *,
        approval: str,
    ) -> ExecutionRun:
        del approval
        service.current = service.build_run(undone=False).model_copy(
            update={"state": ExecutionState.VERIFICATION_FAILED}
        )
        raise ExecutionServiceError("synthetic bounded failure")

    monkeypatch.setattr(service, "apply", failed_apply)
    phrase = f"APPLY {prepared.plan_digest[:16].upper()}"

    result = RUNNER.invoke(cli.app, ["apply", "--approve", phrase])

    assert result.exit_code == 2
    assert "durable state: verification failed" in result.stdout
    assert "macwise doctor" in result.stdout
    assert "synthetic" not in result.stdout
