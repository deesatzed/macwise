"""Strict inert manifests for approval-gated cleanup execution and undo."""

import re
from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from macwise.models.plan import PlanActionKind

_SHA256 = re.compile(r"[0-9a-f]{64}")


class ExecutionState(StrEnum):
    """Observed lifecycle state of one execution run."""

    PREPARED = "prepared"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"
    VERIFICATION_FAILED = "verification_failed"
    UNDO_IN_PROGRESS = "undo_in_progress"
    UNDONE = "undone"
    UNDO_PARTIAL = "undo_partial"
    INTERRUPTED = "interrupted"


class ActionState(StrEnum):
    """Observed lifecycle state of one ordered action."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPLIED = "applied"
    VERIFIED = "verified"
    FAILED = "failed"
    UNDO_IN_PROGRESS = "undo_in_progress"
    UNDONE = "undone"
    UNDO_FAILED = "undo_failed"


class VerificationState(StrEnum):
    """Whether current evidence confirms the requested after-state."""

    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    UNKNOWN = "unknown"


class InverseKind(StrEnum):
    """Closed inert inverse operations; adapters reconstruct their implementation."""

    RESTORE_FROM_TRASH = "restore_from_trash"
    HOMEBREW_INSTALL_FORMULA = "homebrew_install_formula"
    HOMEBREW_INSTALL_CASK = "homebrew_install_cask"
    ENABLE_LAUNCH_AGENT = "enable_launch_agent"
    START_HOMEBREW_SERVICE = "start_homebrew_service"


class ActionObservation(BaseModel):
    """Typed host facts captured before or after an action."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    exists: bool | None = None
    device: int | None = Field(default=None, ge=0)
    inode: int | None = Field(default=None, ge=0)
    identity_digest: str | None = None
    installed: bool | None = None
    running: bool | None = None
    enabled: bool | None = None
    plist_sha256: str | None = None

    @model_validator(mode="after")
    def require_valid_digests(self) -> "ActionObservation":
        for value in (self.identity_digest, self.plist_sha256):
            if value is not None and _SHA256.fullmatch(value) is None:
                raise ValueError("Observation digests must be full lowercase SHA-256 values")
        return self


class InverseIntent(BaseModel):
    """Typed inert recovery intent recorded before mutation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: InverseKind
    source_path: str | None = None
    destination_path: str | None = None
    homebrew_token: str | None = None
    startup_id: str | None = None
    startup_label: str | None = None
    startup_source_path: str | None = None
    plist_sha256: str | None = None
    prior_running: bool | None = None
    prior_enabled: bool | None = None

    @model_validator(mode="after")
    def require_kind_specific_identity(self) -> "InverseIntent":
        if self.kind is InverseKind.RESTORE_FROM_TRASH:
            if not self.source_path or not self.destination_path or self.homebrew_token is not None:
                raise ValueError("Trash restoration requires exact source and destination paths")
        elif (
            self.kind
            in {
                InverseKind.HOMEBREW_INSTALL_FORMULA,
                InverseKind.HOMEBREW_INSTALL_CASK,
            }
            and not self.homebrew_token
        ):
            raise ValueError("Homebrew restoration requires an exact token")
        return self


class ExecutionAction(BaseModel):
    """One ordered manifest action copied from reviewed typed intent."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    plan_action_id: str = Field(min_length=1)
    sequence: int = Field(ge=1)
    subject_id: str = Field(min_length=1)
    kind: PlanActionKind
    state: ActionState
    verification: VerificationState
    before: ActionObservation
    after: ActionObservation | None = None
    inverse: InverseIntent
    error: str | None = None

    @model_validator(mode="after")
    def require_truthful_verified_state(self) -> "ExecutionAction":
        if self.state is ActionState.VERIFIED and (
            self.verification is not VerificationState.VERIFIED or self.after is None
        ):
            raise ValueError("A verified action requires verified after-state evidence")
        return self


class ExecutionRun(BaseModel):
    """One complete immutable revision of an execution and recovery manifest."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    run_id: str = Field(min_length=1)
    manifest_revision: int = Field(ge=1)
    plan_id: str = Field(min_length=1)
    plan_revision: int = Field(ge=1)
    plan_digest: str
    approval_fingerprint: str = Field(min_length=16, max_length=16)
    created_at: AwareDatetime
    updated_at: AwareDatetime
    state: ExecutionState
    actions: tuple[ExecutionAction, ...] = Field(min_length=1)
    limitations: tuple[str, ...] = ()

    @model_validator(mode="after")
    def require_consistent_manifest(self) -> "ExecutionRun":
        if _SHA256.fullmatch(self.plan_digest) is None:
            raise ValueError("The plan digest must be a full lowercase SHA-256 value")
        if self.approval_fingerprint != self.plan_digest[:16].upper():
            raise ValueError("The approval fingerprint must match the full plan digest")
        action_ids = [action.plan_action_id for action in self.actions]
        if len(action_ids) != len(set(action_ids)):
            raise ValueError("Execution actions must reference unique plan actions")
        if [action.sequence for action in self.actions] != list(range(1, len(self.actions) + 1)):
            raise ValueError("Execution actions require a contiguous action sequence")
        if self.state is ExecutionState.SUCCEEDED and any(
            action.state is not ActionState.VERIFIED
            or action.verification is not VerificationState.VERIFIED
            for action in self.actions
        ):
            raise ValueError("A succeeded run requires verified actions")
        if self.state is ExecutionState.UNDONE and any(
            action.state is not ActionState.UNDONE for action in self.actions
        ):
            raise ValueError("An undone run requires every action to be undone")
        return self
