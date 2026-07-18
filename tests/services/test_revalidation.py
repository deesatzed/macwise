import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest

from macwise.models import (
    ActionObservation,
    AuditDocument,
    CollectorState,
    CollectorStatus,
    EntityType,
    ExecutionAction,
    InstallRole,
    InverseKind,
    PlanDocument,
    SoftwareRecord,
    StartupKind,
    StartupRecord,
)
from macwise.services.planning import add_candidate
from macwise.services.revalidation import RevalidationError, prepare_execution

NOW = datetime(2026, 7, 18, 3, 0, tzinfo=UTC)
TRASH = Path("/Users/example/.Trash")
COMPLETE_COLLECTORS = tuple(
    CollectorStatus(
        collector=name,
        state=CollectorState.COMPLETE,
        collected_at=NOW,
        records_count=1,
    )
    for name in ("applications", "homebrew", "usage", "startup", "backups", "overlap")
)


def software(
    subject_id: str = "application:example",
    *,
    entity_type: EntityType = EntityType.APPLICATION,
    name: str = "Example",
    display_name: str = "Example App",
    install_path: str | None = "/Applications/Example.app",
    **updates: object,
) -> SoftwareRecord:
    return SoftwareRecord.model_validate(
        {
            "id": subject_id,
            "entity_type": entity_type,
            "name": name,
            "display_name": display_name,
            "install_path": install_path,
            **updates,
        }
    )


def audit(*records: SoftwareRecord, audit_id: str = "audit:current") -> AuditDocument:
    return AuditDocument(
        audit_id=audit_id,
        collected_at=NOW,
        software=records,
        collectors=COMPLETE_COLLECTORS,
    )


def audit_with_startup(
    record: SoftwareRecord,
    startup: StartupRecord,
    *,
    audit_id: str,
) -> AuditDocument:
    return AuditDocument(
        audit_id=audit_id,
        collected_at=NOW,
        software=(record,),
        startup=(startup,),
        collectors=COMPLETE_COLLECTORS,
    )


def plan_for(record: SoftwareRecord) -> PlanDocument:
    return add_candidate(
        None,
        audit(record, audit_id="audit:planned"),
        record.id,
        clock=lambda: NOW,
        plan_id_factory=lambda: "plan:test",
        trash_root=TRASH,
    ).plan


def probe_for(plan: PlanDocument, *, occupied: bool = False, cross_device: bool = False):
    action = plan.actions[-1]
    source = Path(action.source_path or "")
    destination = Path(action.destination_path or "")

    def probe(path: Path) -> ActionObservation:
        if path == source:
            return ActionObservation(
                exists=True,
                device=1,
                inode=42,
                identity_digest="b" * 64,
            )
        if path == TRASH:
            return ActionObservation(exists=True, device=2 if cross_device else 1, inode=7)
        if path == destination:
            return ActionObservation(exists=occupied, device=1, inode=99 if occupied else None)
        raise AssertionError(f"unexpected probe path: {path}")

    return probe


def test_prepare_execution_refuses_schema_one_and_changed_current_identity() -> None:
    record = software()
    current = plan_for(record)
    legacy = PlanDocument.model_validate(
        {
            **current.model_dump(),
            "schema_version": 1,
            "actions": tuple(
                item.model_copy(update={"sequence": None}) for item in current.actions
            ),
        }
    )

    with pytest.raises(RevalidationError, match="schema 2"):
        prepare_execution(
            legacy,
            audit(record),
            trash_root=TRASH,
            filesystem_probe=probe_for(current),
        )

    changed = record.model_copy(update={"install_path": "/Applications/Replaced.app"})
    with pytest.raises(RevalidationError, match="changed"):
        prepare_execution(
            current,
            audit(changed),
            trash_root=TRASH,
            filesystem_probe=probe_for(current),
        )


def test_prepare_execution_refuses_a_new_current_dependency_blocker() -> None:
    planned = software(
        "homebrew_formula:tool",
        entity_type=EntityType.HOMEBREW_FORMULA,
        name="tool",
        display_name="tool",
        install_path=None,
        install_role=InstallRole.EXPLICIT,
    )
    plan = plan_for(planned)
    now_required = planned.model_copy(update={"reverse_dependencies": ("consumer",)})

    with pytest.raises(RevalidationError, match="added a blocker"):
        prepare_execution(
            plan,
            audit(now_required),
            trash_root=TRASH,
            filesystem_probe=lambda path: ActionObservation(exists=path == TRASH),
        )


def test_prepare_execution_refuses_action_relevant_partial_collector() -> None:
    formula = software(
        "homebrew_formula:ripgrep",
        entity_type=EntityType.HOMEBREW_FORMULA,
        name="ripgrep",
        display_name="ripgrep",
        install_path=None,
        install_role=InstallRole.EXPLICIT,
    )
    plan = plan_for(formula)
    current = AuditDocument(
        audit_id="audit:partial-homebrew",
        collected_at=NOW,
        software=(formula,),
        collectors=(
            CollectorStatus(
                collector="homebrew",
                state=CollectorState.PARTIAL,
                collected_at=NOW,
                records_count=1,
                limitations=("synthetic unavailable evidence",),
            ),
        ),
    )

    with pytest.raises(RevalidationError, match="collector evidence is incomplete"):
        prepare_execution(
            plan,
            current,
            trash_root=TRASH,
            filesystem_probe=lambda path: ActionObservation(exists=path == TRASH),
        )


def test_prepare_execution_refuses_missing_collector_statuses() -> None:
    record = software()
    plan = plan_for(record)
    current = AuditDocument(audit_id="audit:missing-status", collected_at=NOW, software=(record,))

    with pytest.raises(RevalidationError, match="collector evidence is incomplete"):
        prepare_execution(
            plan,
            current,
            trash_root=TRASH,
            filesystem_probe=probe_for(plan),
        )


def test_prepare_manual_app_reconstructs_destination_and_before_inverse_without_mutation() -> None:
    record = software()
    plan = plan_for(record)

    prepared = prepare_execution(
        plan,
        audit(record),
        trash_root=TRASH,
        filesystem_probe=probe_for(plan),
    )

    assert prepared.plan_digest
    assert len(prepared.actions) == 1
    action: ExecutionAction = prepared.actions[0]
    assert action.plan_action_id == plan.actions[0].id
    assert action.before.exists is True
    assert action.before.inode == 42
    assert action.inverse.source_path == plan.actions[0].destination_path
    assert action.inverse.destination_path == plan.actions[0].source_path


@pytest.mark.parametrize(
    ("occupied", "cross_device", "message"),
    ((True, False, "destination"), (False, True, "same filesystem")),
)
def test_prepare_manual_app_refuses_occupied_destination_or_cross_device_move(
    occupied: bool,
    cross_device: bool,
    message: str,
) -> None:
    record = software()
    plan = plan_for(record)

    with pytest.raises(RevalidationError, match=message):
        prepare_execution(
            plan,
            audit(record),
            trash_root=TRASH,
            filesystem_probe=probe_for(
                plan,
                occupied=occupied,
                cross_device=cross_device,
            ),
        )


def test_prepare_cask_refuses_risky_or_unknown_artifact_behavior() -> None:
    planned = software(
        "homebrew_cask:example",
        entity_type=EntityType.HOMEBREW_CASK,
        name="example",
        display_name="Example",
        install_path="/opt/homebrew/Caskroom/example",
        install_role=InstallRole.EXPLICIT,
        cask_artifact_kinds=("app",),
    )
    plan = plan_for(planned)
    risky = planned.model_copy(update={"cask_artifact_kinds": ("app", "uninstall")})

    with pytest.raises(RevalidationError, match="cask removal behavior"):
        prepare_execution(
            plan,
            audit(risky),
            trash_root=TRASH,
            filesystem_probe=lambda path: ActionObservation(exists=path == TRASH),
        )


def test_prepare_cask_matches_exact_entity_even_when_application_name_is_the_same() -> None:
    cask = software(
        "homebrew_cask:example",
        entity_type=EntityType.HOMEBREW_CASK,
        name="example",
        display_name="Example",
        install_path="/opt/homebrew/Caskroom/example",
        install_role=InstallRole.EXPLICIT,
        cask_artifact_kinds=("app",),
    )
    same_name_app = software(
        "application:example-name",
        name="example",
        display_name="Example App",
    )
    plan = plan_for(cask)

    prepared = prepare_execution(
        plan,
        audit(cask, same_name_app),
        trash_root=TRASH,
        filesystem_probe=lambda path: ActionObservation(exists=path == TRASH),
    )

    assert len(prepared.actions) == 1
    assert prepared.actions[0].kind.value == "homebrew_uninstall_cask"


def test_prepare_supported_launch_agent_captures_exact_plist_hash_and_inverse() -> None:
    record = software()
    startup = StartupRecord(
        id="startup:agent",
        label="com.example.agent",
        kind=StartupKind.LAUNCH_AGENT,
        source_path="/Users/example/Library/LaunchAgents/com.example.agent.plist",
        owner_software_ids=(record.id,),
        enabled=True,
        running=True,
    )
    planned_audit = audit_with_startup(record, startup, audit_id="audit:planned")
    plan = add_candidate(
        None,
        planned_audit,
        record.id,
        clock=lambda: NOW,
        plan_id_factory=lambda: "plan:test",
        trash_root=TRASH,
        include_startup=True,
    ).plan
    plist = b"synthetic launch agent plist"

    prepared = prepare_execution(
        plan,
        audit_with_startup(record, startup, audit_id="audit:current"),
        trash_root=TRASH,
        filesystem_probe=probe_for(plan),
        plist_reader=lambda path: plist,
    )

    startup_action = prepared.actions[0]
    assert startup_action.before.plist_sha256 == hashlib.sha256(plist).hexdigest()
    assert startup_action.before.enabled is True
    assert startup_action.inverse.kind is InverseKind.ENABLE_LAUNCH_AGENT
    assert startup_action.inverse.plist_sha256 == hashlib.sha256(plist).hexdigest()


@pytest.mark.parametrize(("enabled", "running"), ((None, True), (True, None)))
def test_prepare_launch_agent_refuses_unknown_item_state(
    enabled: bool | None,
    running: bool | None,
) -> None:
    record = software()
    startup = StartupRecord(
        id="startup:agent",
        label="com.example.agent",
        kind=StartupKind.LAUNCH_AGENT,
        source_path="/Users/example/Library/LaunchAgents/com.example.agent.plist",
        owner_software_ids=(record.id,),
        enabled=enabled,
        running=running,
    )
    planned = startup.model_copy(update={"enabled": True, "running": True})
    plan = add_candidate(
        None,
        audit_with_startup(record, planned, audit_id="audit:planned"),
        record.id,
        clock=lambda: NOW,
        plan_id_factory=lambda: "plan:unknown-startup",
        trash_root=TRASH,
        include_startup=True,
    ).plan

    with pytest.raises(RevalidationError, match="state is unknown"):
        prepare_execution(
            plan,
            audit_with_startup(record, startup, audit_id="audit:current"),
            trash_root=TRASH,
            filesystem_probe=probe_for(plan),
            plist_reader=lambda path: b"synthetic",
        )


def test_prepare_homebrew_service_captures_prior_running_state_and_inverse() -> None:
    formula = software(
        "homebrew_formula:postgresql",
        entity_type=EntityType.HOMEBREW_FORMULA,
        name="postgresql@17",
        display_name="postgresql@17",
        install_path=None,
        install_role=InstallRole.EXPLICIT,
        service_status="started",
    )
    startup = StartupRecord(
        id="startup:postgresql",
        label="postgresql@17",
        kind=StartupKind.HOMEBREW_SERVICE,
        owner_software_ids=(formula.id,),
        running=True,
    )
    planned_audit = audit_with_startup(formula, startup, audit_id="audit:planned")
    plan = add_candidate(
        None,
        planned_audit,
        formula.id,
        clock=lambda: NOW,
        plan_id_factory=lambda: "plan:test",
        trash_root=TRASH,
        include_startup=True,
    ).plan

    prepared = prepare_execution(
        plan,
        audit_with_startup(formula, startup, audit_id="audit:current"),
        trash_root=TRASH,
        filesystem_probe=lambda path: (_ for _ in ()).throw(
            AssertionError(f"unexpected filesystem probe: {path}")
        ),
    )

    service_action = prepared.actions[0]
    assert service_action.before.running is True
    assert service_action.inverse.kind is InverseKind.START_HOMEBREW_SERVICE
    assert service_action.inverse.homebrew_token == "postgresql@17"
