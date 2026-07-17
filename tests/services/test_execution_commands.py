from datetime import UTC, datetime
from pathlib import Path

import pytest

from macwise.execution import CommandActionError
from macwise.models import (
    ActionObservation,
    AuditDocument,
    EntityType,
    ExecutionAction,
    ExecutionState,
    InstallRole,
    InverseIntent,
    PlanActionKind,
    SoftwareRecord,
    StartupKind,
    StartupRecord,
)
from macwise.persistence import ExecutionStore, PlanStore, execution_digest
from macwise.services import (
    ExecutionService,
    ExecutionServiceError,
    PreparedExecution,
    apply_approval_phrase,
    prepare_execution,
    undo_approval_phrase,
)
from macwise.services.planning import add_candidate

NOW = datetime(2026, 7, 18, 5, 0, tzinfo=UTC)


class NoTrashAdapter:
    def apply(self, action: ExecutionAction) -> ActionObservation:
        raise AssertionError(f"unexpected Trash apply: {action}")

    def undo(self, action: ExecutionAction) -> ActionObservation:
        raise AssertionError(f"unexpected Trash undo: {action}")


class RecordingCommands:
    def __init__(self, events: list[str] | None = None) -> None:
        self.calls: list[tuple[str, str]] = []
        self.fail_install = False
        self.events = events

    def uninstall_formula(self, token: str) -> None:
        self.calls.append(("uninstall_formula", token))

    def uninstall_cask(self, token: str) -> None:
        self.calls.append(("uninstall_cask", token))

    def install_formula(self, token: str) -> None:
        self.calls.append(("install_formula", token))
        if self.fail_install:
            raise CommandActionError("synthetic install failure")

    def install_cask(self, token: str) -> None:
        self.calls.append(("install_cask", token))

    def stop_service(self, token: str) -> None:
        self.calls.append(("stop_service", token))

    def start_service(self, token: str) -> None:
        self.calls.append(("start_service", token))

    def disable_launch_agent(
        self,
        label: str,
        source_path: Path,
        *,
        was_running: bool,
    ) -> None:
        del source_path, was_running
        self.calls.append(("disable_launch_agent", label))
        if self.events is not None:
            self.events.append("disable_launch_agent")

    def restore_launch_agent(
        self,
        label: str,
        source_path: Path,
        *,
        was_enabled: bool,
        was_running: bool,
    ) -> None:
        del source_path, was_enabled, was_running
        self.calls.append(("restore_launch_agent", label))
        if self.events is not None:
            self.events.append("restore_launch_agent")


class CommandObserver:
    def __init__(self, commands: RecordingCommands, *, verify: bool = True) -> None:
        self.commands = commands
        self.verify = verify

    def observe(self, action: ExecutionAction) -> ActionObservation:
        if action.kind is PlanActionKind.STOP_HOMEBREW_SERVICE:
            stopped = any(call[0] == "stop_service" for call in self.commands.calls)
            restarted = any(call[0] == "start_service" for call in self.commands.calls)
            return ActionObservation(running=not stopped or restarted)
        removed = any(call[0].startswith("uninstall_") for call in self.commands.calls)
        restored = any(call[0].startswith("install_") for call in self.commands.calls)
        installed = (not removed or restored) if self.verify else True
        return ActionObservation(installed=installed)


class LaunchObserver:
    def __init__(self, commands: RecordingCommands, plist_sha256: str) -> None:
        self.commands = commands
        self.plist_sha256 = plist_sha256

    def observe(self, action: ExecutionAction) -> ActionObservation:
        del action
        disabled = any(call[0] == "disable_launch_agent" for call in self.commands.calls)
        restored = any(call[0] == "restore_launch_agent" for call in self.commands.calls)
        active = not disabled or restored
        return ActionObservation(
            exists=True,
            running=active,
            enabled=active,
            plist_sha256=self.plist_sha256,
        )


class RecordingTrash:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def apply(self, action: ExecutionAction) -> ActionObservation:
        self.events.append("trash_apply")
        return ActionObservation(
            exists=True,
            device=action.before.device,
            inode=action.before.inode,
            identity_digest=action.before.identity_digest,
        )

    def undo(self, action: ExecutionAction) -> ActionObservation:
        self.events.append("trash_undo")
        assert action.after is not None
        return action.after


def formula_execution(
    tmp_path: Path,
    *,
    verify: bool = True,
    entity_type: EntityType = EntityType.HOMEBREW_FORMULA,
    include_service: bool = False,
) -> tuple[ExecutionService, RecordingCommands, PreparedExecution]:
    token = "docker" if entity_type is EntityType.HOMEBREW_CASK else "ripgrep"
    formula = SoftwareRecord(
        id=f"{entity_type.value}:{token}",
        entity_type=entity_type,
        name=token,
        display_name=token,
        install_role=InstallRole.EXPLICIT,
        install_path=(
            "/opt/homebrew/Caskroom/docker" if entity_type is EntityType.HOMEBREW_CASK else None
        ),
        cask_artifact_kinds=("app",) if entity_type is EntityType.HOMEBREW_CASK else (),
        service_status="started" if include_service else None,
    )
    startup = (
        (
            StartupRecord(
                id="startup:ripgrep",
                label=token,
                kind=StartupKind.HOMEBREW_SERVICE,
                owner_software_ids=(formula.id,),
                running=True,
            ),
        )
        if include_service
        else ()
    )
    audit = AuditDocument(
        audit_id="audit:formula",
        collected_at=NOW,
        software=(formula,),
        startup=startup,
    )
    plan = add_candidate(
        None,
        audit,
        formula.id,
        clock=lambda: NOW,
        plan_id_factory=lambda: "plan:formula",
        trash_root=tmp_path / "Trash",
        include_startup=include_service,
    ).plan
    prepared = prepare_execution(
        plan,
        audit,
        trash_root=tmp_path / "Trash",
        filesystem_probe=lambda path: (_ for _ in ()).throw(
            AssertionError(f"unexpected probe: {path}")
        ),
    )
    state = tmp_path / "state"
    lock_path = state / "macwise.lock"
    plan_store = PlanStore(state / "macwise.db", lock_path=lock_path)
    execution_store = ExecutionStore(state / "executions.db", lock_path=lock_path)
    plan_store.append(plan)
    commands = RecordingCommands()
    service = ExecutionService(
        plan_store=plan_store,
        execution_store=execution_store,
        state_lock_path=lock_path,
        trash_adapter=NoTrashAdapter(),
        command_adapter=commands,
        action_observer=CommandObserver(commands, verify=verify),
        clock=lambda: NOW,
        run_id_factory=lambda: "run:formula",
    )
    return service, commands, prepared


def test_command_action_requires_fresh_before_and_after_observations_then_undoes(
    tmp_path: Path,
) -> None:
    service, commands, prepared = formula_execution(tmp_path)

    applied = service.apply(
        prepared,
        approval=apply_approval_phrase(prepared.plan_digest),
    )

    assert applied.state is ExecutionState.SUCCEEDED
    assert applied.actions[0].after == ActionObservation(installed=False)
    assert commands.calls == [("uninstall_formula", "ripgrep")]

    undone = service.undo(approval=undo_approval_phrase(execution_digest(applied)))

    assert undone.state is ExecutionState.UNDONE
    assert commands.calls == [
        ("uninstall_formula", "ripgrep"),
        ("install_formula", "ripgrep"),
    ]


def test_command_exit_zero_without_verified_after_state_fails_closed(tmp_path: Path) -> None:
    service, commands, prepared = formula_execution(tmp_path, verify=False)

    with pytest.raises(ExecutionServiceError, match="approved action"):
        service.apply(
            prepared,
            approval=apply_approval_phrase(prepared.plan_digest),
        )

    active = service.execution_store.active()
    assert active is not None
    assert active.state is ExecutionState.VERIFICATION_FAILED
    assert commands.calls == [("uninstall_formula", "ripgrep")]


def test_prepared_actions_cannot_substitute_a_token_under_a_valid_plan_digest(
    tmp_path: Path,
) -> None:
    service, commands, prepared = formula_execution(tmp_path)
    original = prepared.actions[0]
    tampered_action = original.model_copy(
        update={
            "inverse": InverseIntent(
                kind=original.inverse.kind,
                homebrew_token="wget",
            )
        }
    )
    tampered = PreparedExecution(
        plan_digest=prepared.plan_digest,
        actions=(tampered_action,),
    )

    with pytest.raises(ExecutionServiceError, match="prepared actions"):
        service.apply(
            tampered,
            approval=apply_approval_phrase(tampered.plan_digest),
        )

    assert commands.calls == []
    assert service.execution_store.active() is None


def test_cask_and_running_service_use_exact_apply_and_reverse_undo_order(
    tmp_path: Path,
) -> None:
    cask_service, cask_commands, cask_prepared = formula_execution(
        tmp_path / "cask",
        entity_type=EntityType.HOMEBREW_CASK,
    )
    cask_applied = cask_service.apply(
        cask_prepared,
        approval=apply_approval_phrase(cask_prepared.plan_digest),
    )
    cask_service.undo(
        approval=undo_approval_phrase(execution_digest(cask_applied)),
    )
    assert cask_commands.calls == [
        ("uninstall_cask", "docker"),
        ("install_cask", "docker"),
    ]

    service, commands, prepared = formula_execution(
        tmp_path / "service",
        include_service=True,
    )
    applied = service.apply(
        prepared,
        approval=apply_approval_phrase(prepared.plan_digest),
    )
    service.undo(approval=undo_approval_phrase(execution_digest(applied)))

    assert commands.calls == [
        ("stop_service", "ripgrep"),
        ("uninstall_formula", "ripgrep"),
        ("install_formula", "ripgrep"),
        ("start_service", "ripgrep"),
    ]


def test_undo_command_failure_is_journaled_before_stopping(tmp_path: Path) -> None:
    service, commands, prepared = formula_execution(tmp_path)
    applied = service.apply(
        prepared,
        approval=apply_approval_phrase(prepared.plan_digest),
    )
    commands.fail_install = True

    with pytest.raises(ExecutionServiceError, match="approved undo"):
        service.undo(approval=undo_approval_phrase(execution_digest(applied)))

    active = service.execution_store.active()
    assert active is not None
    assert active.state is ExecutionState.UNDO_PARTIAL
    assert active.actions[0].state.value == "undo_failed"


def test_launch_agent_is_disabled_before_trash_and_restored_after_trash_undo(
    tmp_path: Path,
) -> None:
    import hashlib

    home = tmp_path
    trash = home / ".Trash"
    source = home / "Applications" / "Example.app"
    plist = home / "Library" / "LaunchAgents" / "com.example.agent.plist"
    trash.mkdir()
    source.mkdir(parents=True)
    plist.parent.mkdir(parents=True)
    plist.write_bytes(b"synthetic plist")
    record = SoftwareRecord(
        id="application:example",
        entity_type=EntityType.APPLICATION,
        name="Example",
        display_name="Example",
        install_path=str(source),
    )
    startup = StartupRecord(
        id="startup:example",
        label="com.example.agent",
        kind=StartupKind.LAUNCH_AGENT,
        source_path=str(plist),
        owner_software_ids=(record.id,),
        enabled=True,
        running=True,
    )
    audit = AuditDocument(
        audit_id="audit:launch",
        collected_at=NOW,
        software=(record,),
        startup=(startup,),
    )
    plan = add_candidate(
        None,
        audit,
        record.id,
        clock=lambda: NOW,
        plan_id_factory=lambda: "plan:launch",
        trash_root=trash,
        include_startup=True,
    ).plan

    def probe(path: Path) -> ActionObservation:
        if path == source:
            item = source.stat()
            return ActionObservation(
                exists=True,
                device=item.st_dev,
                inode=item.st_ino,
                identity_digest="a" * 64,
            )
        if path == trash:
            return ActionObservation(exists=True, device=source.stat().st_dev)
        return ActionObservation(exists=False)

    prepared = prepare_execution(
        plan,
        audit,
        trash_root=trash,
        filesystem_probe=probe,
    )
    state = tmp_path / "state"
    lock_path = state / "macwise.lock"
    plan_store = PlanStore(state / "macwise.db", lock_path=lock_path)
    execution_store = ExecutionStore(state / "executions.db", lock_path=lock_path)
    plan_store.append(plan)
    events: list[str] = []
    commands = RecordingCommands(events)
    service = ExecutionService(
        plan_store=plan_store,
        execution_store=execution_store,
        state_lock_path=lock_path,
        trash_adapter=RecordingTrash(events),
        command_adapter=commands,
        action_observer=LaunchObserver(
            commands,
            hashlib.sha256(plist.read_bytes()).hexdigest(),
        ),
        clock=lambda: NOW,
        run_id_factory=lambda: "run:launch",
    )

    applied = service.apply(
        prepared,
        approval=apply_approval_phrase(prepared.plan_digest),
    )
    service.undo(approval=undo_approval_phrase(execution_digest(applied)))

    assert events == [
        "disable_launch_agent",
        "trash_apply",
        "trash_undo",
        "restore_launch_agent",
    ]
