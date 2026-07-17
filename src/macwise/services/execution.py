"""Approval, journal, exact adapter, verification, and undo coordination."""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Protocol

from macwise.execution import FilesystemActionError
from macwise.models import (
    ActionObservation,
    ActionState,
    ExecutionAction,
    ExecutionRun,
    ExecutionState,
    PlanActionKind,
    VerificationState,
)
from macwise.persistence import (
    ExecutionStore,
    ExecutionStoreError,
    PlanStore,
    PlanStoreError,
    StateLock,
    execution_digest,
    plan_digest,
)
from macwise.services.approval import approval_fingerprint, require_approval
from macwise.services.revalidation import PreparedExecution


class ExecutionServiceError(RuntimeError):
    """An approved run could not safely proceed or recover."""


class TrashAdapter(Protocol):
    """Exact filesystem boundary required by the current coordinator slice."""

    def apply(self, action: ExecutionAction) -> ActionObservation: ...

    def undo(self, action: ExecutionAction) -> ActionObservation: ...


class ExecutionService:
    """Coordinate one exact plan through durable apply, verification, and undo."""

    def __init__(
        self,
        *,
        plan_store: PlanStore,
        execution_store: ExecutionStore,
        state_lock_path: Path,
        trash_adapter: TrashAdapter,
        clock: Callable[[], datetime],
        run_id_factory: Callable[[], str],
    ) -> None:
        self.plan_store = plan_store
        self.execution_store = execution_store
        self.state_lock_path = state_lock_path
        self.trash_adapter = trash_adapter
        self.clock = clock
        self.run_id_factory = run_id_factory

    def _revision(
        self,
        previous: ExecutionRun,
        *,
        state: ExecutionState,
        actions: tuple[ExecutionAction, ...],
    ) -> ExecutionRun:
        return ExecutionRun.model_validate(
            {
                **previous.model_dump(),
                "manifest_revision": previous.manifest_revision + 1,
                "updated_at": self.clock(),
                "state": state,
                "actions": actions,
            }
        )

    @staticmethod
    def _replace_action(
        actions: tuple[ExecutionAction, ...],
        replacement: ExecutionAction,
    ) -> tuple[ExecutionAction, ...]:
        return tuple(
            replacement if action.plan_action_id == replacement.plan_action_id else action
            for action in actions
        )

    def apply(self, prepared: PreparedExecution, *, approval: str) -> ExecutionRun:
        """Apply one exact prepared plan after approval, journaling before mutation."""
        require_approval(prepared.plan_digest, approval, verb="APPLY")
        try:
            with StateLock(self.state_lock_path) as held:
                plan = self.plan_store.active()
                if plan is None or plan_digest(plan) != prepared.plan_digest:
                    raise ExecutionServiceError(
                        "The active cleanup plan changed after it was reviewed."
                    )
                prior_execution = self.execution_store.active()
                if (
                    prior_execution is not None
                    and prior_execution.plan_id == plan.plan_id
                    and prior_execution.plan_revision == plan.revision
                    and prior_execution.plan_digest == prepared.plan_digest
                ):
                    raise ExecutionServiceError(
                        "This exact cleanup plan revision was already executed."
                    )
                created_at = self.clock()
                manifest = ExecutionRun(
                    run_id=self.run_id_factory(),
                    manifest_revision=1,
                    plan_id=plan.plan_id,
                    plan_revision=plan.revision,
                    plan_digest=prepared.plan_digest,
                    approval_fingerprint=approval_fingerprint(prepared.plan_digest),
                    created_at=created_at,
                    updated_at=created_at,
                    state=ExecutionState.PREPARED,
                    actions=prepared.actions,
                    limitations=plan.limitations,
                )
                self.execution_store.append(manifest, state_lock=held)

                for pending in prepared.actions:
                    in_progress = ExecutionAction.model_validate(
                        {**pending.model_dump(), "state": ActionState.IN_PROGRESS}
                    )
                    manifest = self._revision(
                        manifest,
                        state=ExecutionState.IN_PROGRESS,
                        actions=self._replace_action(manifest.actions, in_progress),
                    )
                    self.execution_store.append(manifest, state_lock=held)
                    try:
                        if pending.kind is not PlanActionKind.MOVE_APPLICATION_TO_TRASH:
                            raise ExecutionServiceError(
                                "This approved action does not yet have an allowlisted adapter."
                            )
                        after = self.trash_adapter.apply(pending)
                    except (ExecutionServiceError, FilesystemActionError) as error:
                        failed = ExecutionAction.model_validate(
                            {
                                **pending.model_dump(),
                                "state": ActionState.FAILED,
                                "verification": VerificationState.FAILED,
                                "error": "The allowlisted action did not complete.",
                            }
                        )
                        actions = self._replace_action(manifest.actions, failed)
                        failed_state = (
                            ExecutionState.PARTIAL
                            if any(action.state is ActionState.VERIFIED for action in actions)
                            else ExecutionState.FAILED
                        )
                        manifest = self._revision(
                            manifest,
                            state=failed_state,
                            actions=actions,
                        )
                        self.execution_store.append(manifest, state_lock=held)
                        raise ExecutionServiceError(
                            "MacWise could not complete the approved action."
                        ) from error
                    verified = ExecutionAction.model_validate(
                        {
                            **pending.model_dump(),
                            "state": ActionState.VERIFIED,
                            "verification": VerificationState.VERIFIED,
                            "after": after,
                        }
                    )
                    actions = self._replace_action(manifest.actions, verified)
                    final_state = (
                        ExecutionState.SUCCEEDED
                        if all(action.state is ActionState.VERIFIED for action in actions)
                        else ExecutionState.IN_PROGRESS
                    )
                    manifest = self._revision(
                        manifest,
                        state=final_state,
                        actions=actions,
                    )
                    self.execution_store.append(manifest, state_lock=held)
                return manifest
        except (ExecutionStoreError, PlanStoreError, FilesystemActionError) as error:
            raise ExecutionServiceError(
                "MacWise could not complete the approved action."
            ) from error

    def undo(self, *, approval: str) -> ExecutionRun:
        """Reverse the latest fully verified run after separate exact approval."""
        try:
            with StateLock(self.state_lock_path) as held:
                manifest = self.execution_store.active()
                if manifest is None or manifest.state is not ExecutionState.SUCCEEDED:
                    raise ExecutionServiceError("No fully verified execution is ready to undo.")
                require_approval(execution_digest(manifest), approval, verb="UNDO")
                for verified in reversed(manifest.actions):
                    undoing = ExecutionAction.model_validate(
                        {**verified.model_dump(), "state": ActionState.UNDO_IN_PROGRESS}
                    )
                    manifest = self._revision(
                        manifest,
                        state=ExecutionState.UNDO_IN_PROGRESS,
                        actions=self._replace_action(manifest.actions, undoing),
                    )
                    self.execution_store.append(manifest, state_lock=held)
                    if verified.kind is not PlanActionKind.MOVE_APPLICATION_TO_TRASH:
                        raise ExecutionServiceError(
                            "This action does not yet have an allowlisted inverse adapter."
                        )
                    restored = self.trash_adapter.undo(verified)
                    undone = ExecutionAction.model_validate(
                        {
                            **verified.model_dump(),
                            "state": ActionState.UNDONE,
                            "verification": VerificationState.VERIFIED,
                            "after": restored,
                        }
                    )
                    actions = self._replace_action(manifest.actions, undone)
                    final_state = (
                        ExecutionState.UNDONE
                        if all(action.state is ActionState.UNDONE for action in actions)
                        else ExecutionState.UNDO_IN_PROGRESS
                    )
                    manifest = self._revision(
                        manifest,
                        state=final_state,
                        actions=actions,
                    )
                    self.execution_store.append(manifest, state_lock=held)
                return manifest
        except (ExecutionStoreError, FilesystemActionError) as error:
            raise ExecutionServiceError("MacWise could not complete the approved undo.") from error
