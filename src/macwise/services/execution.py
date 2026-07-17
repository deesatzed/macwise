"""Approval, journal, exact adapter, verification, and undo coordination."""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Protocol

from macwise.execution import CommandActionError, FilesystemActionError
from macwise.models import (
    ActionObservation,
    ActionState,
    ExecutionAction,
    ExecutionRun,
    ExecutionState,
    InverseKind,
    PlanActionKind,
    PlanDocument,
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


class ActionVerificationError(RuntimeError):
    """Fresh host evidence does not confirm an action's required state."""


class TrashAdapter(Protocol):
    """Exact filesystem boundary required by the current coordinator slice."""

    def apply(self, action: ExecutionAction) -> ActionObservation: ...

    def undo(self, action: ExecutionAction) -> ActionObservation: ...


class CommandAdapter(Protocol):
    """Closed mutating commands required by non-filesystem plan actions."""

    def uninstall_formula(self, token: str) -> None: ...

    def uninstall_cask(self, token: str) -> None: ...

    def install_formula(self, token: str) -> None: ...

    def install_cask(self, token: str) -> None: ...

    def stop_service(self, token: str) -> None: ...

    def start_service(self, token: str) -> None: ...

    def disable_launch_agent(
        self,
        label: str,
        source_path: Path,
        *,
        was_running: bool,
    ) -> None: ...

    def restore_launch_agent(
        self,
        label: str,
        source_path: Path,
        *,
        was_enabled: bool,
        was_running: bool,
    ) -> None: ...


class ActionObserver(Protocol):
    """Collect fresh typed state immediately before and after a command action."""

    def observe(self, action: ExecutionAction) -> ActionObservation: ...


class ExecutionService:
    """Coordinate one exact plan through durable apply, verification, and undo."""

    def __init__(
        self,
        *,
        plan_store: PlanStore,
        execution_store: ExecutionStore,
        state_lock_path: Path,
        trash_adapter: TrashAdapter,
        command_adapter: CommandAdapter | None = None,
        action_observer: ActionObserver | None = None,
        clock: Callable[[], datetime],
        run_id_factory: Callable[[], str],
    ) -> None:
        self.plan_store = plan_store
        self.execution_store = execution_store
        self.state_lock_path = state_lock_path
        self.trash_adapter = trash_adapter
        self.command_adapter = command_adapter
        self.action_observer = action_observer
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

    @staticmethod
    def _require_observation(
        current: ActionObservation,
        expected: ActionObservation,
        fields: tuple[str, ...],
    ) -> None:
        if any(
            getattr(expected, field) is not None
            and getattr(current, field) != getattr(expected, field)
            for field in fields
        ):
            raise ActionVerificationError("Fresh host state does not match the recorded state.")

    def _command_boundaries(self) -> tuple[CommandAdapter, ActionObserver]:
        if self.command_adapter is None or self.action_observer is None:
            raise ExecutionServiceError(
                "This approved action does not have complete allowlisted command boundaries."
            )
        return self.command_adapter, self.action_observer

    @staticmethod
    def _require_prepared_matches_plan(
        plan: PlanDocument,
        prepared: PreparedExecution,
    ) -> None:
        if len(plan.actions) != len(prepared.actions):
            raise ExecutionServiceError("The prepared actions do not match the reviewed plan.")
        inverse_by_kind = {
            PlanActionKind.MOVE_APPLICATION_TO_TRASH: InverseKind.RESTORE_FROM_TRASH,
            PlanActionKind.HOMEBREW_UNINSTALL_FORMULA: InverseKind.HOMEBREW_INSTALL_FORMULA,
            PlanActionKind.HOMEBREW_UNINSTALL_CASK: InverseKind.HOMEBREW_INSTALL_CASK,
            PlanActionKind.DISABLE_LAUNCH_AGENT: InverseKind.ENABLE_LAUNCH_AGENT,
            PlanActionKind.STOP_HOMEBREW_SERVICE: InverseKind.START_HOMEBREW_SERVICE,
        }
        for planned, action in zip(plan.actions, prepared.actions, strict=True):
            if (
                (
                    planned.id,
                    planned.sequence,
                    planned.subject_id,
                    planned.kind,
                    planned.homebrew_token,
                    planned.startup_id,
                    planned.startup_label,
                    planned.startup_source_path,
                )
                != (
                    action.plan_action_id,
                    action.sequence,
                    action.subject_id,
                    action.kind,
                    action.inverse.homebrew_token,
                    action.inverse.startup_id,
                    action.inverse.startup_label,
                    action.inverse.startup_source_path,
                )
                or action.inverse.kind is not inverse_by_kind[planned.kind]
                or action.state is not ActionState.PENDING
                or action.verification is not VerificationState.PENDING
                or action.after is not None
            ):
                raise ExecutionServiceError("The prepared actions do not match the reviewed plan.")
            if planned.kind is PlanActionKind.MOVE_APPLICATION_TO_TRASH and (
                action.inverse.source_path != planned.destination_path
                or action.inverse.destination_path != planned.source_path
            ):
                raise ExecutionServiceError("The prepared actions do not match the reviewed plan.")

    def _apply_action(self, action: ExecutionAction) -> ActionObservation:
        if action.kind is PlanActionKind.MOVE_APPLICATION_TO_TRASH:
            return self.trash_adapter.apply(action)

        commands, observer = self._command_boundaries()
        before = observer.observe(action)
        if action.kind in {
            PlanActionKind.HOMEBREW_UNINSTALL_FORMULA,
            PlanActionKind.HOMEBREW_UNINSTALL_CASK,
        }:
            self._require_observation(before, action.before, ("installed",))
            token = action.inverse.homebrew_token
            if token is None:
                raise ExecutionServiceError("The Homebrew action lost its exact token.")
            if action.kind is PlanActionKind.HOMEBREW_UNINSTALL_FORMULA:
                commands.uninstall_formula(token)
            else:
                commands.uninstall_cask(token)
            after = observer.observe(action)
            self._require_observation(after, ActionObservation(installed=False), ("installed",))
            return after
        if action.kind is PlanActionKind.STOP_HOMEBREW_SERVICE:
            self._require_observation(before, action.before, ("running", "enabled"))
            token = action.inverse.homebrew_token
            if token is None:
                raise ExecutionServiceError("The service action lost its exact token.")
            commands.stop_service(token)
            after = observer.observe(action)
            self._require_observation(after, ActionObservation(running=False), ("running",))
            return after

        if action.kind is not PlanActionKind.DISABLE_LAUNCH_AGENT:
            raise ExecutionServiceError("The action kind has no allowlisted command adapter.")
        self._require_observation(
            before,
            action.before,
            ("exists", "running", "enabled", "plist_sha256"),
        )
        label = action.inverse.startup_label
        source = action.inverse.startup_source_path
        if label is None or source is None:
            raise ExecutionServiceError("The LaunchAgent action lost its exact identity.")
        commands.disable_launch_agent(
            label,
            Path(source),
            was_running=action.before.running is True,
        )
        after = observer.observe(action)
        expected_after = ActionObservation(
            exists=True,
            enabled=False,
            running=False if action.before.running is True else None,
            plist_sha256=action.inverse.plist_sha256,
        )
        self._require_observation(
            after,
            expected_after,
            ("exists", "running", "enabled", "plist_sha256"),
        )
        return after

    def _undo_action(self, action: ExecutionAction) -> ActionObservation:
        if action.kind is PlanActionKind.MOVE_APPLICATION_TO_TRASH:
            return self.trash_adapter.undo(action)

        commands, observer = self._command_boundaries()
        current = observer.observe(action)
        if action.after is None:
            raise ExecutionServiceError("The verified action has no recorded after-state.")
        if action.kind in {
            PlanActionKind.HOMEBREW_UNINSTALL_FORMULA,
            PlanActionKind.HOMEBREW_UNINSTALL_CASK,
        }:
            self._require_observation(current, action.after, ("installed",))
            token = action.inverse.homebrew_token
            if token is None:
                raise ExecutionServiceError("The Homebrew inverse lost its exact token.")
            if action.inverse.kind is InverseKind.HOMEBREW_INSTALL_FORMULA:
                commands.install_formula(token)
            elif action.inverse.kind is InverseKind.HOMEBREW_INSTALL_CASK:
                commands.install_cask(token)
            else:
                raise ExecutionServiceError("The Homebrew inverse kind changed.")
            restored = observer.observe(action)
            self._require_observation(restored, ActionObservation(installed=True), ("installed",))
            return restored
        if action.kind is PlanActionKind.STOP_HOMEBREW_SERVICE:
            self._require_observation(current, action.after, ("running",))
            token = action.inverse.homebrew_token
            if token is None:
                raise ExecutionServiceError("The service inverse lost its exact token.")
            if action.inverse.prior_running is True:
                commands.start_service(token)
            restored = observer.observe(action)
            self._require_observation(
                restored,
                ActionObservation(running=action.inverse.prior_running),
                ("running",),
            )
            return restored

        self._require_observation(
            current,
            action.after,
            ("exists", "running", "enabled", "plist_sha256"),
        )
        label = action.inverse.startup_label
        source = action.inverse.startup_source_path
        if label is None or source is None:
            raise ExecutionServiceError("The LaunchAgent inverse lost its exact identity.")
        commands.restore_launch_agent(
            label,
            Path(source),
            was_enabled=action.inverse.prior_enabled is True,
            was_running=action.inverse.prior_running is True,
        )
        restored = observer.observe(action)
        expected = ActionObservation(
            exists=True,
            running=action.inverse.prior_running,
            enabled=action.inverse.prior_enabled,
            plist_sha256=action.inverse.plist_sha256,
        )
        self._require_observation(
            restored,
            expected,
            ("exists", "running", "enabled", "plist_sha256"),
        )
        return restored

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
                self._require_prepared_matches_plan(plan, prepared)
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
                        after = self._apply_action(pending)
                    except (
                        ActionVerificationError,
                        CommandActionError,
                        ExecutionServiceError,
                        FilesystemActionError,
                    ) as error:
                        verification_failed = isinstance(error, ActionVerificationError)
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
                            ExecutionState.VERIFICATION_FAILED
                            if verification_failed
                            else (
                                ExecutionState.PARTIAL
                                if any(action.state is ActionState.VERIFIED for action in actions)
                                else ExecutionState.FAILED
                            )
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
                    try:
                        restored = self._undo_action(verified)
                    except (
                        ActionVerificationError,
                        CommandActionError,
                        ExecutionServiceError,
                        FilesystemActionError,
                    ) as error:
                        failed = ExecutionAction.model_validate(
                            {
                                **verified.model_dump(),
                                "state": ActionState.UNDO_FAILED,
                                "verification": VerificationState.FAILED,
                                "error": "The allowlisted inverse action did not complete.",
                            }
                        )
                        manifest = self._revision(
                            manifest,
                            state=ExecutionState.UNDO_PARTIAL,
                            actions=self._replace_action(manifest.actions, failed),
                        )
                        self.execution_store.append(manifest, state_lock=held)
                        raise ExecutionServiceError(
                            "MacWise could not complete the approved undo."
                        ) from error
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
        except (
            ActionVerificationError,
            CommandActionError,
            ExecutionStoreError,
            FilesystemActionError,
        ) as error:
            raise ExecutionServiceError("MacWise could not complete the approved undo.") from error
