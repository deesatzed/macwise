"""Pure Phase 4 cleanup-plan preview and preflight analysis."""

import os
import re
import unicodedata
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from macwise.models import (
    AuditDocument,
    EntityType,
    FindingTopic,
    InstallRole,
    PlanActionKind,
    PlanCandidate,
    PlanDocument,
    PlanEligibility,
    PlannedAction,
    PreflightCheck,
    PreflightKind,
    PreflightOutcome,
    RecommendationAction,
    RollbackBlueprint,
    RollbackFeasibility,
    SoftwareRecord,
    UsageLabel,
    stable_plan_component_id,
)

_HOMEBREW_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9@+_.-]*")
_BLOCKING_USAGE = {
    UsageLabel.ACTIVELY_USED,
    UsageLabel.RECENTLY_USED,
    UsageLabel.PROBABLY_USED,
    UsageLabel.INDIRECTLY_REQUIRED,
}
_BLOCKING_GUIDANCE = {
    RecommendationAction.KEEP,
    RecommendationAction.KEEP_TOGETHER,
}
_PLAN_LIMITATIONS = (
    "This preview is not approval to make changes.",
    "Every target and preflight must be revalidated against current host state before action.",
    "Phase 4 does not uninstall, move, disable, delete, or otherwise change installed software.",
)


@dataclass(frozen=True, slots=True)
class PlanningResult:
    """One resulting immutable revision and whether persistence should append it."""

    plan: PlanDocument
    changed: bool


def _homebrew_token(record: SoftwareRecord) -> str | None:
    candidate: str | None = None
    if record.entity_type in {EntityType.HOMEBREW_FORMULA, EntityType.HOMEBREW_CASK}:
        candidate = record.name
    elif record.install_source and record.install_source.startswith("homebrew_cask:"):
        candidate = record.install_source.removeprefix("homebrew_cask:")
    if candidate and _HOMEBREW_TOKEN.fullmatch(candidate):
        return candidate
    return None


def _usage_label(audit: AuditDocument, subject_id: str) -> UsageLabel | None:
    return next(
        (
            finding.usage_label
            for finding in audit.findings
            if finding.subject_id == subject_id and finding.topic is FindingTopic.USAGE
        ),
        None,
    )


def _candidate(audit: AuditDocument, record: SoftwareRecord) -> PlanCandidate:
    return PlanCandidate(
        subject_id=record.id,
        source_audit_id=audit.audit_id,
        source_audit_collected_at=audit.collected_at,
        entity_type=record.entity_type,
        display_name=record.display_name,
        version=record.version,
        identifier=record.identifier,
        install_path=record.install_path,
        homebrew_token=_homebrew_token(record),
        install_source=record.install_source,
        install_role=record.install_role,
        protected=record.protected or _system_application_path(record.install_path),
        reverse_dependencies=record.reverse_dependencies,
        project_references=record.project_references,
        usage_label=_usage_label(audit, record.id),
        related_path_ids=tuple(
            sorted(item.id for item in audit.path_evidence if item.subject_id == record.id)
        ),
        startup_ids=tuple(
            sorted(item.id for item in audit.startup if record.id in item.owner_software_ids)
        ),
    )


def _system_application_path(value: str | None) -> bool:
    if value is None:
        return False
    absolute = Path(os.path.abspath(value))
    system = Path("/System")
    return absolute == system or system in absolute.parents


def _valid_application_path(value: str | None) -> bool:
    if value is None:
        return False
    if any(unicodedata.category(character) in {"Cc", "Cf"} for character in value):
        return False
    path = Path(value)
    return path.is_absolute() and path.suffix.casefold() == ".app" and ".." not in path.parts


def _action(
    plan_id: str,
    candidate: PlanCandidate,
    *,
    trash_root: Path,
) -> PlannedAction | None:
    if candidate.protected:
        return None
    if candidate.entity_type is EntityType.APPLICATION and candidate.homebrew_token:
        kind = PlanActionKind.HOMEBREW_UNINSTALL_CASK
        action_id = stable_plan_component_id("action", plan_id, candidate.subject_id, kind.value)
        return PlannedAction(
            id=action_id,
            subject_id=candidate.subject_id,
            kind=kind,
            homebrew_token=candidate.homebrew_token,
        )
    if candidate.entity_type is EntityType.APPLICATION:
        if not _valid_application_path(candidate.install_path):
            return None
        kind = PlanActionKind.MOVE_APPLICATION_TO_TRASH
        action_id = stable_plan_component_id("action", plan_id, candidate.subject_id, kind.value)
        assert candidate.install_path is not None
        basename = Path(candidate.install_path).name
        destination = trash_root / f"{basename}.macwise-{action_id.removeprefix('action:')}"
        return PlannedAction(
            id=action_id,
            subject_id=candidate.subject_id,
            kind=kind,
            source_path=candidate.install_path,
            destination_path=str(destination),
        )
    if not candidate.homebrew_token:
        return None
    kind = (
        PlanActionKind.HOMEBREW_UNINSTALL_FORMULA
        if candidate.entity_type is EntityType.HOMEBREW_FORMULA
        else PlanActionKind.HOMEBREW_UNINSTALL_CASK
    )
    action_id = stable_plan_component_id("action", plan_id, candidate.subject_id, kind.value)
    return PlannedAction(
        id=action_id,
        subject_id=candidate.subject_id,
        kind=kind,
        homebrew_token=candidate.homebrew_token,
    )


def _rollback(action: PlannedAction, candidate: PlanCandidate) -> RollbackBlueprint:
    rollback_id = stable_plan_component_id("rollback", action.id)
    if action.kind is PlanActionKind.MOVE_APPLICATION_TO_TRASH:
        return RollbackBlueprint(
            id=rollback_id,
            action_id=action.id,
            feasibility=RollbackFeasibility.REVERSIBLE,
            strategy=(
                "Move the same bundle from its planned Trash path back to its original path."
            ),
            original_path=action.source_path,
            restore_path=action.source_path,
            prerequisites=(
                "The planned Trash bundle must still exist and the restore path be free.",
            ),
            limitations=("Action-time path and identity revalidation is still required.",),
        )
    assert action.homebrew_token is not None
    return RollbackBlueprint(
        id=rollback_id,
        action_id=action.id,
        feasibility=RollbackFeasibility.BEST_EFFORT,
        strategy="Request a new Homebrew installation of the exact recorded package token.",
        homebrew_token=action.homebrew_token,
        captured_version=candidate.version,
        prerequisites=("Homebrew and the recorded package token must remain available.",),
        limitations=("The captured version may no longer be available from Homebrew.",),
    )


def _check(
    plan_id: str,
    revision: int,
    subject_id: str,
    kind: PreflightKind,
    outcome: PreflightOutcome,
    statement: str,
    *,
    evidence_ids: Sequence[str] = (),
    limitations: Sequence[str] = (),
) -> PreflightCheck:
    return PreflightCheck(
        id=stable_plan_component_id(
            "check",
            plan_id,
            str(revision),
            subject_id,
            kind.value,
        ),
        subject_id=subject_id,
        kind=kind,
        outcome=outcome,
        statement=statement,
        evidence_ids=tuple(evidence_ids),
        limitations=tuple(limitations),
    )


def _preflight(
    plan_id: str,
    revision: int,
    candidate: PlanCandidate,
    action: PlannedAction | None,
    rollback: RollbackBlueprint | None,
    audit: AuditDocument,
) -> tuple[PreflightCheck, ...]:
    subject_id = candidate.subject_id
    checks: list[PreflightCheck] = []

    checks.append(
        _check(
            plan_id,
            revision,
            subject_id,
            PreflightKind.IDENTITY,
            PreflightOutcome.PASS if action is not None else PreflightOutcome.BLOCK,
            (
                "An exact typed action identity is available."
                if action is not None
                else "No exact supported action identity or install path is available."
            ),
        )
    )
    checks.append(
        _check(
            plan_id,
            revision,
            subject_id,
            PreflightKind.PROTECTION,
            PreflightOutcome.BLOCK if candidate.protected else PreflightOutcome.PASS,
            (
                "The target is protected and cannot enter an actionable preview."
                if candidate.protected
                else "The inventory did not mark this target as an Apple/system component."
            ),
            limitations=("Protection state must be revalidated before action.",),
        )
    )

    dependency_reasons: list[str] = []
    if candidate.install_role is InstallRole.DEPENDENCY:
        dependency_reasons.append("Homebrew recorded this item as a dependency")
    if candidate.reverse_dependencies:
        dependency_reasons.append("installed reverse dependencies were recorded")
    if candidate.project_references:
        dependency_reasons.append("approved project references were recorded")
    dependency_outcome = PreflightOutcome.BLOCK if dependency_reasons else PreflightOutcome.PASS
    if not dependency_reasons and (
        candidate.entity_type in {EntityType.HOMEBREW_FORMULA, EntityType.HOMEBREW_CASK}
        and candidate.install_role is InstallRole.UNKNOWN
    ):
        dependency_outcome = PreflightOutcome.WARNING
    checks.append(
        _check(
            plan_id,
            revision,
            subject_id,
            PreflightKind.DEPENDENCY,
            dependency_outcome,
            (
                "; ".join(dependency_reasons) + "."
                if dependency_reasons
                else "No collected reverse dependency or approved project reference blocks this preview."
            ),
            evidence_ids=(*candidate.reverse_dependencies, *candidate.project_references),
            limitations=("Only collected and approved dependency evidence is represented.",),
        )
    )

    if candidate.usage_label in _BLOCKING_USAGE:
        usage_outcome = PreflightOutcome.BLOCK
        usage_statement = "Current use or dependency evidence conflicts with cleanup intent."
    else:
        usage_outcome = PreflightOutcome.WARNING
        usage_statement = "Usage evidence is cautious, absent, or user-confirmed and needs review."
    checks.append(
        _check(
            plan_id,
            revision,
            subject_id,
            PreflightKind.USAGE,
            usage_outcome,
            usage_statement,
            limitations=("Point-in-time evidence is not complete usage history.",),
        )
    )

    guidance = tuple(item for item in audit.recommendations if subject_id in item.subject_ids)
    blocking_guidance = tuple(item for item in guidance if item.action in _BLOCKING_GUIDANCE)
    checks.append(
        _check(
            plan_id,
            revision,
            subject_id,
            PreflightKind.OVERLAP,
            PreflightOutcome.BLOCK if blocking_guidance else PreflightOutcome.WARNING,
            (
                "Keep or keep-together guidance conflicts with cleanup intent."
                if blocking_guidance
                else "No keep guidance blocks this preview, but overlap remains review context."
            ),
            evidence_ids=tuple(item.id for item in guidance),
            limitations=("Catalog roles do not prove local interchangeability.",),
        )
    )

    checks.append(
        _check(
            plan_id,
            revision,
            subject_id,
            PreflightKind.RELATED_DATA,
            (PreflightOutcome.WARNING if candidate.related_path_ids else PreflightOutcome.PASS),
            (
                "Related data was measured and will be preserved by this plan."
                if candidate.related_path_ids
                else "No bounded related-data path was collected for this target."
            ),
            evidence_ids=candidate.related_path_ids,
            limitations=("No related user data is included in a Phase 4 action.",),
        )
    )

    configured = audit.backup.configured if audit.backup is not None else None
    checks.append(
        _check(
            plan_id,
            revision,
            subject_id,
            PreflightKind.BACKUP,
            PreflightOutcome.WARNING,
            (
                "Backup configuration was observed, but coverage is not verified."
                if configured is True
                else "Backup coverage is not verified for this target or its related data."
            ),
            limitations=(
                "Configuration, timestamps, and non-exclusion do not prove recoverability.",
            ),
        )
    )

    checks.append(
        _check(
            plan_id,
            revision,
            subject_id,
            PreflightKind.STARTUP,
            PreflightOutcome.WARNING if candidate.startup_ids else PreflightOutcome.PASS,
            (
                "Owned startup components were observed and will not be changed in Phase 4."
                if candidate.startup_ids
                else "No owned startup component was collected for this target."
            ),
            evidence_ids=candidate.startup_ids,
        )
    )

    rollback_outcome = PreflightOutcome.BLOCK
    rollback_statement = "No rollback blueprint can be created without an exact action."
    if rollback is not None and rollback.feasibility is RollbackFeasibility.REVERSIBLE:
        rollback_outcome = PreflightOutcome.PASS
        rollback_statement = "A reversible Trash restore blueprint is available."
    elif rollback is not None and rollback.feasibility is RollbackFeasibility.BEST_EFFORT:
        rollback_outcome = PreflightOutcome.WARNING
        rollback_statement = "A best-effort Homebrew reinstall blueprint is available."
    checks.append(
        _check(
            plan_id,
            revision,
            subject_id,
            PreflightKind.ROLLBACK,
            rollback_outcome,
            rollback_statement,
            evidence_ids=(rollback.id,) if rollback is not None else (),
            limitations=("Rollback feasibility must be revalidated at action time.",),
        )
    )
    checks.append(
        _check(
            plan_id,
            revision,
            subject_id,
            PreflightKind.STALENESS,
            PreflightOutcome.WARNING,
            "This is a point-in-time audit snapshot and can become stale.",
            limitations=("Phase 5 must collect and compare current host state before action.",),
        )
    )
    return tuple(checks)


def add_candidate(
    current: PlanDocument | None,
    audit: AuditDocument,
    subject_id: str,
    *,
    clock: Callable[[], datetime],
    plan_id_factory: Callable[[], str],
    trash_root: Path,
) -> PlanningResult:
    """Append one exactly identified candidate to a new immutable preview revision."""
    if current is not None and subject_id in {
        candidate.subject_id for candidate in current.candidates
    }:
        return PlanningResult(plan=current, changed=False)

    record = next((item for item in audit.software if item.id == subject_id), None)
    if record is None:
        raise ValueError("The selected software record is not present in the source audit.")

    plan_id = current.plan_id if current is not None else plan_id_factory()
    revision = current.revision + 1 if current is not None else 1
    new_candidate = _candidate(audit, record)
    new_action = _action(plan_id, new_candidate, trash_root=trash_root)
    new_rollback = _rollback(new_action, new_candidate) if new_action is not None else None
    new_checks = _preflight(
        plan_id,
        revision,
        new_candidate,
        new_action,
        new_rollback,
        audit,
    )

    candidates = (*current.candidates, new_candidate) if current is not None else (new_candidate,)
    actions = (
        (*current.actions, new_action)
        if current is not None and new_action is not None
        else current.actions
        if current is not None
        else (new_action,)
        if new_action is not None
        else ()
    )
    checks = (*current.checks, *new_checks) if current is not None else new_checks
    rollback = (
        (*current.rollback, new_rollback)
        if current is not None and new_rollback is not None
        else current.rollback
        if current is not None
        else (new_rollback,)
        if new_rollback is not None
        else ()
    )
    eligibility = (
        PlanEligibility.BLOCKED
        if any(item.outcome is PreflightOutcome.BLOCK for item in checks)
        else PlanEligibility.PREVIEW_READY
    )
    plan = PlanDocument(
        plan_id=plan_id,
        revision=revision,
        created_at=clock(),
        source_audit_id=audit.audit_id,
        source_audit_collected_at=audit.collected_at,
        candidates=candidates,
        actions=actions,
        checks=checks,
        rollback=rollback,
        eligibility=eligibility,
        limitations=_PLAN_LIMITATIONS,
    )
    return PlanningResult(plan=plan, changed=True)
