"""Read-only reconstruction and fresh safety checks for approved plan intent."""

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from macwise.models import (
    ActionObservation,
    ActionState,
    AuditDocument,
    EntityType,
    ExecutionAction,
    InverseIntent,
    InverseKind,
    PlanActionKind,
    PlanDocument,
    PlanEligibility,
    PlannedAction,
    VerificationState,
)
from macwise.persistence import plan_digest
from macwise.services.planning import add_candidate

FilesystemProbe = Callable[[Path], ActionObservation]
PlistReader = Callable[[Path], bytes]
_SAFE_CASK_ARTIFACTS = frozenset({"app", "binary"})


class RevalidationError(RuntimeError):
    """Fresh evidence cannot safely reconstruct the exact reviewed action."""


@dataclass(frozen=True, slots=True)
class PreparedExecution:
    """Read-only reconstructed operations ready for a later approval gate."""

    plan_digest: str
    actions: tuple[ExecutionAction, ...]


def _fresh_plan(plan: PlanDocument, audit: AuditDocument, trash_root: Path) -> PlanDocument:
    refreshed: PlanDocument | None = None
    startup_subjects = {
        action.subject_id for action in plan.actions if action.startup_id is not None
    }
    for candidate in plan.candidates:
        try:
            result = add_candidate(
                refreshed,
                audit,
                candidate.subject_id,
                clock=lambda: audit.collected_at,
                plan_id_factory=lambda: plan.plan_id,
                trash_root=trash_root,
                include_startup=candidate.subject_id in startup_subjects,
            )
        except ValueError as error:
            raise RevalidationError(
                "A planned software identity is missing or changed in the fresh audit."
            ) from error
        refreshed = result.plan
    if refreshed is None:
        raise RevalidationError("The plan has no candidates to revalidate.")
    return refreshed


def _require_same_candidate_identity(plan: PlanDocument, fresh: PlanDocument) -> None:
    fresh_by_id = {candidate.subject_id: candidate for candidate in fresh.candidates}
    for candidate in plan.candidates:
        current = fresh_by_id.get(candidate.subject_id)
        if current is None or (
            current.entity_type,
            current.identifier,
            current.version,
            current.install_path,
            current.homebrew_token,
        ) != (
            candidate.entity_type,
            candidate.identifier,
            candidate.version,
            candidate.install_path,
            candidate.homebrew_token,
        ):
            raise RevalidationError("A planned software identity changed after preview.")


def _trash_action(
    action: PlannedAction,
    *,
    trash_root: Path,
    filesystem_probe: FilesystemProbe,
) -> ExecutionAction:
    if action.source_path is None or action.destination_path is None:
        raise RevalidationError("The Trash action is missing an exact path identity.")
    source_path = Path(action.source_path)
    destination_path = Path(action.destination_path)
    canonical_destination = trash_root / (
        f"{source_path.name}.macwise-{action.id.removeprefix('action:')}"
    )
    if destination_path != canonical_destination:
        raise RevalidationError("The planned Trash destination changed or is not canonical.")

    source = filesystem_probe(source_path)
    trash = filesystem_probe(trash_root)
    destination = filesystem_probe(destination_path)
    if source.exists is not True or source.device is None or source.inode is None:
        raise RevalidationError("The planned application source is missing or changed.")
    if trash.exists is not True or trash.device is None:
        raise RevalidationError("The canonical Trash directory is unavailable.")
    if destination.exists is not False:
        raise RevalidationError("The exact Trash destination is already occupied.")
    if source.device != trash.device:
        raise RevalidationError("The application and Trash must be on the same filesystem.")
    return ExecutionAction(
        plan_action_id=action.id,
        sequence=action.sequence or 0,
        subject_id=action.subject_id,
        kind=action.kind,
        state=ActionState.PENDING,
        verification=VerificationState.PENDING,
        before=source,
        inverse=InverseIntent(
            kind=InverseKind.RESTORE_FROM_TRASH,
            source_path=str(destination_path),
            destination_path=str(source_path),
        ),
    )


def _homebrew_action(
    action: PlannedAction,
    *,
    audit: AuditDocument,
) -> ExecutionAction:
    if action.homebrew_token is None:
        raise RevalidationError("The Homebrew action is missing its exact token.")
    expected_entity = (
        EntityType.HOMEBREW_FORMULA
        if action.kind is PlanActionKind.HOMEBREW_UNINSTALL_FORMULA
        else EntityType.HOMEBREW_CASK
    )
    matching = tuple(
        record
        for record in audit.software
        if record.name == action.homebrew_token and record.entity_type is expected_entity
    )
    if len(matching) != 1:
        raise RevalidationError("The exact Homebrew package identity is missing or changed.")
    record = matching[0]
    if action.kind is PlanActionKind.HOMEBREW_UNINSTALL_CASK:
        kinds = frozenset(record.cask_artifact_kinds)
        if not kinds or not kinds <= _SAFE_CASK_ARTIFACTS or "app" not in kinds:
            raise RevalidationError("The cask removal behavior is risky, unknown, or unsupported.")
        inverse_kind = InverseKind.HOMEBREW_INSTALL_CASK
    else:
        inverse_kind = InverseKind.HOMEBREW_INSTALL_FORMULA
    return ExecutionAction(
        plan_action_id=action.id,
        sequence=action.sequence or 0,
        subject_id=action.subject_id,
        kind=action.kind,
        state=ActionState.PENDING,
        verification=VerificationState.PENDING,
        before=ActionObservation(installed=True),
        inverse=InverseIntent(kind=inverse_kind, homebrew_token=action.homebrew_token),
    )


def _startup_action(
    action: PlannedAction,
    *,
    audit: AuditDocument,
    plist_reader: PlistReader,
) -> ExecutionAction:
    matching = tuple(
        item
        for item in audit.startup
        if item.id == action.startup_id
        and item.kind is action.startup_kind
        and item.label == action.startup_label
        and item.owner_software_ids == (action.subject_id,)
    )
    if len(matching) != 1:
        raise RevalidationError("The exact startup identity is missing, ambiguous, or changed.")
    startup = matching[0]
    if action.kind is PlanActionKind.DISABLE_LAUNCH_AGENT:
        if action.startup_source_path is None or startup.source_path != action.startup_source_path:
            raise RevalidationError("The LaunchAgent path changed after preview.")
        try:
            plist_sha256 = hashlib.sha256(
                plist_reader(Path(action.startup_source_path))
            ).hexdigest()
        except OSError as error:
            raise RevalidationError("The exact LaunchAgent plist cannot be read safely.") from error
        before = ActionObservation(
            exists=True,
            running=startup.running,
            enabled=startup.enabled,
            plist_sha256=plist_sha256,
        )
        inverse = InverseIntent(
            kind=InverseKind.ENABLE_LAUNCH_AGENT,
            startup_id=startup.id,
            startup_label=startup.label,
            startup_source_path=startup.source_path,
            plist_sha256=plist_sha256,
            prior_running=startup.running,
            prior_enabled=startup.enabled,
        )
    else:
        if action.homebrew_token is None or startup.label != action.homebrew_token:
            raise RevalidationError("The Homebrew service token changed after preview.")
        before = ActionObservation(running=startup.running, enabled=startup.enabled)
        inverse = InverseIntent(
            kind=InverseKind.START_HOMEBREW_SERVICE,
            homebrew_token=action.homebrew_token,
            startup_id=startup.id,
            startup_label=startup.label,
            prior_running=startup.running,
            prior_enabled=startup.enabled,
        )
    return ExecutionAction(
        plan_action_id=action.id,
        sequence=action.sequence or 0,
        subject_id=action.subject_id,
        kind=action.kind,
        state=ActionState.PENDING,
        verification=VerificationState.PENDING,
        before=before,
        inverse=inverse,
    )


def _read_plist(path: Path) -> bytes:
    return path.read_bytes()


def prepare_execution(
    plan: PlanDocument,
    audit: AuditDocument,
    *,
    trash_root: Path,
    filesystem_probe: FilesystemProbe,
    plist_reader: PlistReader = _read_plist,
    clock: Callable[[], datetime] | None = None,
) -> PreparedExecution:
    """Reconstruct exact inert operations after fresh evidence and host observations."""
    del clock
    if plan.schema_version != 2:
        raise RevalidationError("Apply requires a fresh plan schema 2 preview.")
    if plan.eligibility is not PlanEligibility.PREVIEW_READY or not plan.actions:
        raise RevalidationError("The active plan is blocked or contains no supported actions.")

    fresh = _fresh_plan(plan, audit, trash_root)
    _require_same_candidate_identity(plan, fresh)
    if fresh.eligibility is not PlanEligibility.PREVIEW_READY:
        raise RevalidationError("Fresh evidence added a blocker to the reviewed plan.")
    if fresh.actions != plan.actions:
        raise RevalidationError("The exact planned actions changed during revalidation.")

    prepared: list[ExecutionAction] = []
    for action in plan.actions:
        if action.kind is PlanActionKind.MOVE_APPLICATION_TO_TRASH:
            prepared.append(
                _trash_action(
                    action,
                    trash_root=trash_root,
                    filesystem_probe=filesystem_probe,
                )
            )
        elif action.kind in {
            PlanActionKind.HOMEBREW_UNINSTALL_FORMULA,
            PlanActionKind.HOMEBREW_UNINSTALL_CASK,
        }:
            prepared.append(_homebrew_action(action, audit=audit))
        else:
            prepared.append(_startup_action(action, audit=audit, plist_reader=plist_reader))
    return PreparedExecution(plan_digest=plan_digest(plan), actions=tuple(prepared))
