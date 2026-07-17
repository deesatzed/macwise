from datetime import UTC, datetime
from pathlib import Path

import pytest

from macwise.models import (
    AuditDocument,
    BackupStatus,
    ClaimBasis,
    EntityType,
    Finding,
    FindingTopic,
    GuardedRecommendation,
    InstallRole,
    LearningValue,
    PathEvidence,
    PlanActionKind,
    PlanDocument,
    PlanEligibility,
    PreflightKind,
    PreflightOutcome,
    RecommendationAction,
    Reliability,
    RollbackFeasibility,
    SoftwareRecord,
    StartupKind,
    StartupRecord,
    UsageLabel,
)
from macwise.services.planning import add_candidate

NOW = datetime(2026, 7, 17, 23, 40, tzinfo=UTC)
TRASH_ROOT = Path("/Users/example/.Trash")


def software(
    subject_id: str,
    name: str,
    entity_type: EntityType = EntityType.APPLICATION,
    install_role: InstallRole = InstallRole.EXPLICIT,
    **updates: object,
) -> SoftwareRecord:
    return SoftwareRecord.model_validate(
        {
            "id": subject_id,
            "entity_type": entity_type,
            "name": name,
            "display_name": name,
            "install_role": install_role,
            **updates,
        }
    )


def usage(subject_id: str, label: UsageLabel) -> Finding:
    return Finding(
        subject_id=subject_id,
        topic=FindingTopic.USAGE,
        statement=f"Synthetic {label.value} signal.",
        basis=ClaimBasis.INFERRED,
        confidence=Reliability.MEDIUM,
        usage_label=label,
    )


def audit(
    *records: SoftwareRecord,
    findings: tuple[Finding, ...] = (),
    paths: tuple[PathEvidence, ...] = (),
    startup: tuple[StartupRecord, ...] = (),
    recommendations: tuple[GuardedRecommendation, ...] = (),
    backup: BackupStatus | None = None,
    audit_id: str = "audit:test",
) -> AuditDocument:
    return AuditDocument(
        audit_id=audit_id,
        collected_at=NOW,
        software=records,
        findings=findings,
        path_evidence=paths,
        startup=startup,
        recommendations=recommendations,
        backup=backup,
    )


def add(
    current: PlanDocument | None,
    document: AuditDocument,
    subject_id: str,
):
    return add_candidate(
        current,
        document,
        subject_id,
        clock=lambda: NOW,
        plan_id_factory=lambda: "plan:test",
        trash_root=TRASH_ROOT,
    )


def test_standalone_application_gets_exact_trash_preview_and_preserves_data() -> None:
    app = software(
        "application:example",
        "Example App",
        install_path="/Applications/Example.app",
        version="2.4.1",
    )
    related = PathEvidence(
        id="path:example",
        subject_id=app.id,
        path="/Users/example/Library/Application Support/Example",
        kind="application_support",
        size_bytes=4096,
        backup_excluded=False,
    )
    startup = StartupRecord(
        id="startup:example",
        label="Example helper",
        kind=StartupKind.LAUNCH_AGENT,
        owner_software_ids=(app.id,),
    )

    result = add(
        None,
        audit(
            app,
            findings=(usage(app.id, UsageLabel.POSSIBLY_UNUSED),),
            paths=(related,),
            startup=(startup,),
            backup=BackupStatus(configured=True),
        ),
        app.id,
    )

    assert result.changed is True
    assert result.plan.revision == 1
    assert result.plan.eligibility is PlanEligibility.PREVIEW_READY
    assert result.plan.candidates[0].source_audit_id == "audit:test"
    assert result.plan.candidates[0].related_path_ids == (related.id,)
    assert result.plan.candidates[0].startup_ids == (startup.id,)
    assert len(result.plan.actions) == 1
    action = result.plan.actions[0]
    assert action.kind is PlanActionKind.MOVE_APPLICATION_TO_TRASH
    assert action.source_path == "/Applications/Example.app"
    assert action.destination_path is not None
    assert action.destination_path.startswith(f"{TRASH_ROOT}/")
    assert related.path not in {
        value for item in result.plan.actions for value in item.model_dump().values()
    }
    assert result.plan.rollback[0].feasibility is RollbackFeasibility.REVERSIBLE
    checks = {item.kind: item for item in result.plan.checks}
    assert checks[PreflightKind.RELATED_DATA].outcome is PreflightOutcome.WARNING
    assert checks[PreflightKind.BACKUP].outcome is PreflightOutcome.WARNING
    assert "coverage" in checks[PreflightKind.BACKUP].statement.casefold()
    assert "safe to remove" not in result.plan.model_dump_json().casefold()


def test_exact_cask_linked_application_gets_one_cask_action_not_trash() -> None:
    app = software(
        "application:docker",
        "Docker Desktop",
        install_path="/Applications/Docker.app",
        install_source="homebrew_cask:docker",
    )

    result = add(None, audit(app), app.id)

    assert len(result.plan.actions) == 1
    action = result.plan.actions[0]
    assert action.kind is PlanActionKind.HOMEBREW_UNINSTALL_CASK
    assert action.homebrew_token == "docker"
    assert action.source_path is None
    assert result.plan.candidates[0].homebrew_token == "docker"


def test_formula_preview_has_exact_token_and_best_effort_rollback_warning() -> None:
    formula = software(
        "homebrew_formula:ripgrep",
        "ripgrep",
        EntityType.HOMEBREW_FORMULA,
        version="14.1.0",
    )

    result = add(None, audit(formula), formula.id)

    action = result.plan.actions[0]
    assert action.kind is PlanActionKind.HOMEBREW_UNINSTALL_FORMULA
    assert action.homebrew_token == "ripgrep"
    assert result.plan.rollback[0].feasibility is RollbackFeasibility.BEST_EFFORT
    rollback_check = next(
        item for item in result.plan.checks if item.kind is PreflightKind.ROLLBACK
    )
    assert rollback_check.outcome is PreflightOutcome.WARNING


@pytest.mark.parametrize(
    ("record", "label", "blocking_kind", "has_action"),
    (
        (
            software(
                "homebrew_formula:library",
                "library",
                EntityType.HOMEBREW_FORMULA,
                install_role=InstallRole.DEPENDENCY,
            ),
            UsageLabel.POSSIBLY_UNUSED,
            PreflightKind.DEPENDENCY,
            True,
        ),
        (
            software(
                "application:system",
                "System App",
                install_path="/System/Applications/System.app",
                protected=True,
            ),
            UsageLabel.POSSIBLY_UNUSED,
            PreflightKind.PROTECTION,
            False,
        ),
        (
            software(
                "application:active",
                "Active App",
                install_path="/Applications/Active.app",
            ),
            UsageLabel.ACTIVELY_USED,
            PreflightKind.USAGE,
            True,
        ),
        (
            software(
                "homebrew_formula:needed",
                "needed",
                EntityType.HOMEBREW_FORMULA,
                reverse_dependencies=("consumer",),
            ),
            UsageLabel.POSSIBLY_UNUSED,
            PreflightKind.DEPENDENCY,
            True,
        ),
    ),
)
def test_exact_unsafe_candidates_are_retained_but_blocked(
    record: SoftwareRecord,
    label: UsageLabel,
    blocking_kind: PreflightKind,
    has_action: bool,
) -> None:
    result = add(None, audit(record, findings=(usage(record.id, label),)), record.id)

    assert result.plan.candidates[0].subject_id == record.id
    assert result.plan.eligibility is PlanEligibility.BLOCKED
    assert bool(result.plan.actions) is has_action
    assert any(
        item.kind is blocking_kind and item.outcome is PreflightOutcome.BLOCK
        for item in result.plan.checks
    )


def test_keep_or_keep_together_guidance_blocks_preview() -> None:
    app = software(
        "application:kept",
        "Kept App",
        install_path="/Applications/Kept.app",
    )
    recommendation = GuardedRecommendation(
        id="recommendation:keep",
        subject_ids=(app.id,),
        action=RecommendationAction.KEEP,
        statement="Current dependency evidence supports keeping this item.",
        basis=ClaimBasis.INFERRED,
        confidence=Reliability.MEDIUM,
        learning_value=LearningValue.UNKNOWN,
    )

    result = add(
        None,
        audit(app, recommendations=(recommendation,)),
        app.id,
    )

    assert result.plan.eligibility is PlanEligibility.BLOCKED
    assert any(
        item.kind is PreflightKind.OVERLAP and item.outcome is PreflightOutcome.BLOCK
        for item in result.plan.checks
    )


def test_missing_action_identity_is_retained_without_action_and_blocked() -> None:
    app = software("application:missing", "Missing Path")

    result = add(None, audit(app), app.id)

    assert result.plan.candidates[0].subject_id == app.id
    assert result.plan.actions == ()
    assert result.plan.rollback == ()
    assert result.plan.eligibility is PlanEligibility.BLOCKED
    assert any(
        item.kind is PreflightKind.IDENTITY and item.outcome is PreflightOutcome.BLOCK
        for item in result.plan.checks
    )


def test_duplicate_add_is_idempotent_and_new_subject_appends_immutable_revision() -> None:
    first = software(
        "application:first",
        "First App",
        install_path="/Applications/First.app",
    )
    second = software(
        "application:second",
        "Second App",
        install_path="/Applications/Second.app",
    )
    initial = add(None, audit(first), first.id)

    duplicate = add(initial.plan, audit(first), first.id)
    appended = add(
        initial.plan,
        audit(first, second, audit_id="audit:second"),
        second.id,
    )

    assert duplicate.changed is False
    assert duplicate.plan is initial.plan
    assert initial.plan.revision == 1
    assert appended.changed is True
    assert appended.plan.plan_id == initial.plan.plan_id
    assert appended.plan.revision == 2
    assert {item.subject_id for item in appended.plan.candidates} == {first.id, second.id}
    assert initial.plan.candidates == (initial.plan.candidates[0],)
    assert appended.plan.candidates[0].source_audit_id == "audit:test"
    assert appended.plan.candidates[1].source_audit_id == "audit:second"
