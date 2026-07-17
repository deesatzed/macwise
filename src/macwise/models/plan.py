"""Immutable cleanup-plan previews that never grant execution authority."""

from enum import StrEnum
from hashlib import sha256
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from macwise.models.analysis import UsageLabel
from macwise.models.software import EntityType, InstallRole


class PlanEligibility(StrEnum):
    """Whether a saved preview has unresolved blocking checks."""

    BLOCKED = "blocked"
    PREVIEW_READY = "preview_ready"


class PlanActionKind(StrEnum):
    """Typed Phase 4 intent; these values are not executable commands."""

    MOVE_APPLICATION_TO_TRASH = "move_application_to_trash"
    HOMEBREW_UNINSTALL_FORMULA = "homebrew_uninstall_formula"
    HOMEBREW_UNINSTALL_CASK = "homebrew_uninstall_cask"


class PreflightKind(StrEnum):
    """Bounded safety questions evaluated for every plan candidate."""

    IDENTITY = "identity"
    PROTECTION = "protection"
    DEPENDENCY = "dependency"
    USAGE = "usage"
    OVERLAP = "overlap"
    RELATED_DATA = "related_data"
    BACKUP = "backup"
    STARTUP = "startup"
    ROLLBACK = "rollback"
    STALENESS = "staleness"


class PreflightOutcome(StrEnum):
    """A bounded observed result, warning, or hard planning block."""

    PASS = "pass"
    WARNING = "warning"
    BLOCK = "block"


class RollbackFeasibility(StrEnum):
    """How honestly a future action could be reversed."""

    REVERSIBLE = "reversible"
    BEST_EFFORT = "best_effort"
    UNAVAILABLE = "unavailable"


class PlanCandidate(BaseModel):
    """Action-relevant snapshot of one exactly resolved software record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    subject_id: str = Field(min_length=1)
    source_audit_id: str = Field(min_length=1)
    source_audit_collected_at: AwareDatetime
    entity_type: EntityType
    display_name: str = Field(min_length=1)
    version: str | None = None
    identifier: str | None = None
    install_path: str | None = None
    homebrew_token: str | None = None
    install_source: str | None = None
    install_role: InstallRole = InstallRole.UNKNOWN
    protected: bool = False
    reverse_dependencies: tuple[str, ...] = ()
    project_references: tuple[str, ...] = ()
    usage_label: UsageLabel | None = None
    related_path_ids: tuple[str, ...] = ()
    startup_ids: tuple[str, ...] = ()


class PlannedAction(BaseModel):
    """Typed preview intent that a future executor must reconstruct and revalidate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    kind: PlanActionKind
    source_path: str | None = None
    destination_path: str | None = None
    homebrew_token: str | None = None

    @model_validator(mode="after")
    def require_kind_specific_identity(self) -> "PlannedAction":
        """Reject mixed or incomplete action identities."""
        if self.kind is PlanActionKind.MOVE_APPLICATION_TO_TRASH:
            if not self.source_path or not self.destination_path or self.homebrew_token is not None:
                raise ValueError("Trash intent requires only source and destination paths")
        elif (
            not self.homebrew_token
            or self.source_path is not None
            or self.destination_path is not None
        ):
            raise ValueError("Homebrew intent requires only an exact package token")
        return self


class PreflightCheck(BaseModel):
    """One evidence-linked bounded planning check."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    kind: PreflightKind
    outcome: PreflightOutcome
    statement: str = Field(min_length=1)
    evidence_ids: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


class RollbackBlueprint(BaseModel):
    """Recovery intent and limitations for one typed future action."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    action_id: str = Field(min_length=1)
    feasibility: RollbackFeasibility
    strategy: str = Field(min_length=1)
    original_path: str | None = None
    restore_path: str | None = None
    homebrew_token: str | None = None
    captured_version: str | None = None
    prerequisites: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


class PlanDocument(BaseModel):
    """One complete immutable plan revision and its no-authority limitations."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    plan_id: str = Field(min_length=1)
    revision: int = Field(ge=1)
    created_at: AwareDatetime
    source_audit_id: str = Field(min_length=1)
    source_audit_collected_at: AwareDatetime
    candidates: tuple[PlanCandidate, ...] = Field(min_length=1)
    actions: tuple[PlannedAction, ...] = ()
    checks: tuple[PreflightCheck, ...] = Field(min_length=1)
    rollback: tuple[RollbackBlueprint, ...] = ()
    eligibility: PlanEligibility
    limitations: tuple[str, ...] = ()

    @model_validator(mode="after")
    def require_consistent_references_and_eligibility(self) -> "PlanDocument":
        """Keep plan snapshots internally complete and fail closed on blockers."""
        subject_ids = [candidate.subject_id for candidate in self.candidates]
        if len(subject_ids) != len(set(subject_ids)):
            raise ValueError("Plan candidates must have unique subject IDs")
        known_subjects = set(subject_ids)

        action_ids = [action.id for action in self.actions]
        if len(action_ids) != len(set(action_ids)):
            raise ValueError("Plan actions must have unique IDs")
        action_subject_ids = [action.subject_id for action in self.actions]
        if len(action_subject_ids) != len(set(action_subject_ids)):
            raise ValueError("A plan may contain only one action per subject")
        if any(action.subject_id not in known_subjects for action in self.actions):
            raise ValueError("Plan action references an unknown subject")

        check_ids = [check.id for check in self.checks]
        if len(check_ids) != len(set(check_ids)):
            raise ValueError("Preflight checks must have unique IDs")
        if any(check.subject_id not in known_subjects for check in self.checks):
            raise ValueError("Preflight check references an unknown subject")
        checked_subjects = {check.subject_id for check in self.checks}
        if checked_subjects != known_subjects:
            raise ValueError("Every plan candidate requires preflight checks")

        rollback_ids = [item.id for item in self.rollback]
        if len(rollback_ids) != len(set(rollback_ids)):
            raise ValueError("Rollback blueprints must have unique IDs")
        rollback_action_ids = [item.action_id for item in self.rollback]
        if len(rollback_action_ids) != len(set(rollback_action_ids)) or set(
            rollback_action_ids
        ) != set(action_ids):
            raise ValueError("Actions and rollback blueprints require a one-to-one mapping")

        has_blocker = any(check.outcome is PreflightOutcome.BLOCK for check in self.checks)
        if has_blocker and self.eligibility is not PlanEligibility.BLOCKED:
            raise ValueError("A blocking check requires blocked eligibility")
        if not has_blocker and self.eligibility is PlanEligibility.BLOCKED:
            raise ValueError("A plan without blocking checks cannot be blocked")
        return self


def stable_plan_component_id(scope: str, *values: str) -> str:
    """Return a deterministic scoped ID without embedding raw plan values."""
    normalized = "\0".join(value.strip().casefold() for value in values)
    digest = sha256(f"{scope}\0{normalized}".encode()).hexdigest()[:20]
    return f"{scope}:{digest}"
