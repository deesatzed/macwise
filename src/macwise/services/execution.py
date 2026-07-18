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
    StateLockError,
    execution_digest,
    plan_digest,
)
from macwise.services.approval import approval_fingerprint, require_approval
from macwise.services.revalidation import PreparedExecution, RevalidationError


class ExecutionServiceError(RuntimeError):
    """An approved run could not safely proceed or recover."""


class ActionVerificationError(RuntimeError):
    """Fresh host evidence does not confirm an action's required state."""

    def __init__(
        self,
        message: str,
        *,
        observation: ActionObservation,
        mutation_attempted: bool,
    ) -> None:
        super().__init__(message)
        self.observation = observation
        self.mutation_attempted = mutation_attempted


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
        expected_plist_sha256: str,
    ) -> None: ...

    def restore_launch_agent(
        self,
        label: str,
        source_path: Path,
        *,
        was_enabled: bool,
        was_running: bool,
        current_enabled: bool,
        current_running: bool,
        expected_plist_sha256: str,
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
        filesystem_probe: Callable[[Path], ActionObservation] | None = None,
        revalidator: Callable[[PlanDocument], PreparedExecution] | None = None,
        clock: Callable[[], datetime],
        run_id_factory: Callable[[], str],
    ) -> None:
        self.plan_store = plan_store
        self.execution_store = execution_store
        self.state_lock_path = state_lock_path
        self.trash_adapter = trash_adapter
        self.command_adapter = command_adapter
        self.action_observer = action_observer
        self.filesystem_probe = filesystem_probe
        self.revalidator = revalidator
        self.clock = clock
        self.run_id_factory = run_id_factory

    def active(self) -> ExecutionRun | None:
        """Return the current integrity-checked recovery manifest, if one exists."""
        return self.execution_store.active()

    def undoable(self) -> ExecutionRun | None:
        """Return the latest run with safely observed reversible actions."""
        return self.execution_store.latest_undoable()

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
        *,
        mutation_attempted: bool = False,
    ) -> None:
        if not ExecutionService._observation_matches(current, expected, fields):
            raise ActionVerificationError(
                "Fresh host state does not match the recorded state.",
                observation=current,
                mutation_attempted=mutation_attempted,
            )

    @staticmethod
    def _observation_matches(
        current: ActionObservation,
        expected: ActionObservation,
        fields: tuple[str, ...],
    ) -> bool:
        return not any(
            getattr(expected, field) is not None
            and getattr(current, field) != getattr(expected, field)
            for field in fields
        )

    def _command_boundaries(self) -> tuple[CommandAdapter, ActionObserver]:
        if self.command_adapter is None or self.action_observer is None:
            raise ExecutionServiceError(
                "This approved action does not have complete allowlisted command boundaries."
            )
        return self.command_adapter, self.action_observer

    @staticmethod
    def _decisive_fields(action: ExecutionAction) -> tuple[str, ...]:
        if action.kind in {
            PlanActionKind.HOMEBREW_UNINSTALL_FORMULA,
            PlanActionKind.HOMEBREW_UNINSTALL_CASK,
        }:
            return ("installed",)
        if action.kind is PlanActionKind.STOP_HOMEBREW_SERVICE:
            return ("running",)
        if action.kind is PlanActionKind.DISABLE_LAUNCH_AGENT:
            return ("exists", "running", "enabled", "plist_sha256")
        return ("exists", "device", "inode", "identity_digest")

    @classmethod
    def _observation_is_authoritative(
        cls,
        action: ExecutionAction,
        observation: ActionObservation,
    ) -> bool:
        return all(
            getattr(observation, field) is not None for field in cls._decisive_fields(action)
        )

    @staticmethod
    def _expected_command_after(action: ExecutionAction) -> ActionObservation:
        if action.kind in {
            PlanActionKind.HOMEBREW_UNINSTALL_FORMULA,
            PlanActionKind.HOMEBREW_UNINSTALL_CASK,
        }:
            return ActionObservation(installed=False)
        if action.kind is PlanActionKind.STOP_HOMEBREW_SERVICE:
            return ActionObservation(running=False)
        return ActionObservation(
            exists=True,
            enabled=False,
            running=False if action.before.running is True else None,
            plist_sha256=action.inverse.plist_sha256,
        )

    def _observe_action_position(
        self,
        action: ExecutionAction,
    ) -> tuple[bool, bool, ActionObservation]:
        """Classify fresh state as before, applied, or neither without mutation."""
        if action.kind is not PlanActionKind.MOVE_APPLICATION_TO_TRASH:
            if self.action_observer is None:
                raise ExecutionServiceError("Fresh command recovery evidence is unavailable.")
            current = self.action_observer.observe(action)
            if action.kind in {
                PlanActionKind.HOMEBREW_UNINSTALL_FORMULA,
                PlanActionKind.HOMEBREW_UNINSTALL_CASK,
            }:
                fields = ("installed",)
            elif action.kind is PlanActionKind.STOP_HOMEBREW_SERVICE:
                fields = ("running", "enabled")
            else:
                fields = ("exists", "running", "enabled", "plist_sha256")
            expected_after = action.after or self._expected_command_after(action)
            return (
                self._observation_matches(current, action.before, fields),
                self._observation_matches(current, expected_after, fields),
                current,
            )

        if self.filesystem_probe is None:
            raise ExecutionServiceError("Fresh filesystem recovery evidence is unavailable.")
        trash_path = action.inverse.source_path
        original_path = action.inverse.destination_path
        if trash_path is None or original_path is None:
            raise ExecutionServiceError("The Trash recovery paths are incomplete.")
        original = self.filesystem_probe(Path(original_path))
        trash = self.filesystem_probe(Path(trash_path))
        fields = ("exists", "device", "inode", "identity_digest")
        applied_identity = action.after or action.before
        before_match = (
            self._observation_matches(original, action.before, fields) and trash.exists is False
        )
        after_match = original.exists is False and self._observation_matches(
            trash, applied_identity, fields
        )
        return before_match, after_match, original if before_match else trash

    def _classify_interrupted(
        self,
        manifest: ExecutionRun,
        *,
        state_lock: StateLock,
    ) -> ExecutionRun:
        interrupted = next(
            (
                action
                for action in manifest.actions
                if action.state in {ActionState.IN_PROGRESS, ActionState.UNDO_IN_PROGRESS}
            ),
            None,
        )
        if interrupted is None:
            return manifest
        before_match, after_match, current = self._observe_action_position(interrupted)
        if interrupted.state is ActionState.IN_PROGRESS:
            if after_match:
                replacement = ExecutionAction.model_validate(
                    {
                        **interrupted.model_dump(),
                        "state": ActionState.VERIFIED,
                        "verification": VerificationState.VERIFIED,
                        "after": current,
                        "error": None,
                    }
                )
            elif before_match:
                replacement = ExecutionAction.model_validate(
                    {
                        **interrupted.model_dump(),
                        "state": ActionState.FAILED,
                        "verification": VerificationState.FAILED,
                        "after": current,
                        "error": "Fresh recovery evidence confirms no mutation remains.",
                    }
                )
            else:
                replacement = interrupted.model_copy(
                    update={
                        "verification": VerificationState.UNKNOWN,
                        "error": "Fresh recovery evidence is ambiguous.",
                    }
                )
                if manifest.state is ExecutionState.INTERRUPTED:
                    return manifest
                classified = self._revision(
                    manifest,
                    state=ExecutionState.INTERRUPTED,
                    actions=self._replace_action(manifest.actions, replacement),
                )
                self.execution_store.append(classified, state_lock=state_lock)
                return classified
            actions = self._replace_action(manifest.actions, replacement)
            state = (
                ExecutionState.SUCCEEDED
                if all(action.state is ActionState.VERIFIED for action in actions)
                else ExecutionState.PARTIAL
            )
        else:
            if before_match:
                replacement = ExecutionAction.model_validate(
                    {
                        **interrupted.model_dump(),
                        "state": ActionState.UNDONE,
                        "verification": VerificationState.VERIFIED,
                        "after": current,
                        "error": None,
                    }
                )
            elif after_match:
                replacement = ExecutionAction.model_validate(
                    {
                        **interrupted.model_dump(),
                        "state": ActionState.VERIFIED,
                        "verification": VerificationState.VERIFIED,
                        "error": None,
                    }
                )
            else:
                replacement = interrupted.model_copy(
                    update={
                        "verification": VerificationState.UNKNOWN,
                        "error": "Fresh undo recovery evidence is ambiguous.",
                    }
                )
                if manifest.state is ExecutionState.INTERRUPTED:
                    return manifest
                classified = self._revision(
                    manifest,
                    state=ExecutionState.INTERRUPTED,
                    actions=self._replace_action(manifest.actions, replacement),
                )
                self.execution_store.append(classified, state_lock=state_lock)
                return classified
            actions = self._replace_action(manifest.actions, replacement)
            state = (
                ExecutionState.UNDONE
                if all(action.state is ActionState.UNDONE for action in actions)
                else ExecutionState.UNDO_PARTIAL
            )
        classified = self._revision(manifest, state=state, actions=actions)
        self.execution_store.append(classified, state_lock=state_lock)
        return classified

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
            self._require_observation(
                after,
                ActionObservation(installed=False),
                ("installed",),
                mutation_attempted=True,
            )
            return after
        if action.kind is PlanActionKind.STOP_HOMEBREW_SERVICE:
            self._require_observation(before, action.before, ("running", "enabled"))
            token = action.inverse.homebrew_token
            if token is None:
                raise ExecutionServiceError("The service action lost its exact token.")
            commands.stop_service(token)
            after = observer.observe(action)
            self._require_observation(
                after,
                ActionObservation(running=False),
                ("running",),
                mutation_attempted=True,
            )
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
            expected_plist_sha256=action.inverse.plist_sha256 or "",
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
            mutation_attempted=True,
        )
        return after

    def _undo_action(self, action: ExecutionAction) -> ActionObservation:
        if action.kind is PlanActionKind.MOVE_APPLICATION_TO_TRASH:
            return self.trash_adapter.undo(action)

        commands, observer = self._command_boundaries()
        current = observer.observe(action)
        if action.after is None:
            raise ExecutionServiceError("The verified action has no recorded after-state.")
        if not self._observation_is_authoritative(action, action.after):
            raise ExecutionServiceError(
                "The recorded after-state is not authoritative enough to reverse."
            )
        if action.kind in {
            PlanActionKind.HOMEBREW_UNINSTALL_FORMULA,
            PlanActionKind.HOMEBREW_UNINSTALL_CASK,
        }:
            if self._observation_matches(current, action.before, ("installed",)):
                return current
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
            self._require_observation(
                restored,
                ActionObservation(installed=True),
                ("installed",),
                mutation_attempted=True,
            )
            return restored
        if action.kind is PlanActionKind.STOP_HOMEBREW_SERVICE:
            if self._observation_matches(current, action.before, ("running", "enabled")):
                return current
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
                mutation_attempted=True,
            )
            return restored

        launch_fields = ("exists", "running", "enabled", "plist_sha256")
        if self._observation_matches(current, action.before, launch_fields):
            return current
        self._require_observation(
            current,
            action.after,
            launch_fields,
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
            current_enabled=current.enabled is True,
            current_running=current.running is True,
            expected_plist_sha256=action.inverse.plist_sha256 or "",
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
            mutation_attempted=True,
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
                if self.revalidator is not None:
                    try:
                        locked_prepared = self.revalidator(plan)
                    except RevalidationError as error:
                        raise ExecutionServiceError(
                            "Fresh host evidence changed before the execution lock."
                        ) from error
                    if locked_prepared.plan_digest != prepared.plan_digest:
                        raise ExecutionServiceError(
                            "The revalidated cleanup plan digest changed before execution."
                        )
                    prepared = locked_prepared
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
                    current_plan = self.plan_store.active()
                    if current_plan is None or plan_digest(current_plan) != prepared.plan_digest:
                        raise ExecutionServiceError(
                            "The active cleanup plan changed before an ordered action."
                        )
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
                        OSError,
                        RuntimeError,
                        ValueError,
                    ) as error:
                        verification_failed = isinstance(error, ActionVerificationError)
                        failed_after: ActionObservation | None = None
                        if isinstance(error, ActionVerificationError) and error.mutation_attempted:
                            failed_after = error.observation
                        elif isinstance(error, CommandActionError) and self.action_observer:
                            try:
                                failed_after = self.action_observer.observe(pending)
                            except (OSError, RuntimeError, ValueError):
                                failed_after = None
                        if failed_after is not None and not self._observation_is_authoritative(
                            pending,
                            failed_after,
                        ):
                            failed_after = None
                        mutation_may_have_occurred = not (
                            isinstance(error, ActionVerificationError)
                            and not error.mutation_attempted
                        ) and not isinstance(error, ExecutionServiceError)
                        if failed_after is None and mutation_may_have_occurred:
                            failed = ExecutionAction.model_validate(
                                {
                                    **pending.model_dump(),
                                    "state": ActionState.IN_PROGRESS,
                                    "verification": VerificationState.UNKNOWN,
                                    "error": "Fresh post-action state is unavailable.",
                                }
                            )
                            failed_state = ExecutionState.INTERRUPTED
                        else:
                            failed = ExecutionAction.model_validate(
                                {
                                    **pending.model_dump(),
                                    "state": ActionState.FAILED,
                                    "verification": VerificationState.FAILED,
                                    "after": failed_after,
                                    "error": "The allowlisted action did not complete.",
                                }
                            )
                            failed_state = (
                                ExecutionState.VERIFICATION_FAILED
                                if verification_failed
                                else (
                                    ExecutionState.PARTIAL
                                    if mutation_may_have_occurred
                                    else ExecutionState.FAILED
                                )
                            )
                        actions = self._replace_action(manifest.actions, failed)
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
        except (
            ExecutionStoreError,
            PlanStoreError,
            FilesystemActionError,
            StateLockError,
        ) as error:
            raise ExecutionServiceError(
                "MacWise could not complete the approved action."
            ) from error

    def undo(self, *, approval: str) -> ExecutionRun:
        """Reverse the latest fully verified run after separate exact approval."""
        try:
            with StateLock(self.state_lock_path) as held:
                manifest = self.execution_store.latest_undoable()
                allowed_states = {
                    ExecutionState.SUCCEEDED,
                    ExecutionState.PARTIAL,
                    ExecutionState.VERIFICATION_FAILED,
                    ExecutionState.UNDO_PARTIAL,
                    ExecutionState.IN_PROGRESS,
                    ExecutionState.UNDO_IN_PROGRESS,
                    ExecutionState.INTERRUPTED,
                }
                if manifest is None or manifest.state not in allowed_states:
                    raise ExecutionServiceError(
                        "No execution with separately recoverable actions is ready to undo."
                    )
                require_approval(execution_digest(manifest), approval, verb="UNDO")
                if manifest.state in {
                    ExecutionState.IN_PROGRESS,
                    ExecutionState.UNDO_IN_PROGRESS,
                    ExecutionState.INTERRUPTED,
                }:
                    manifest = self._classify_interrupted(manifest, state_lock=held)
                    if manifest.state is ExecutionState.UNDONE:
                        return manifest
                recoverable = tuple(
                    action
                    for action in reversed(manifest.actions)
                    if action.state
                    in {
                        ActionState.VERIFIED,
                        ActionState.UNDO_FAILED,
                        ActionState.FAILED,
                    }
                    and action.after is not None
                )
                if not recoverable:
                    raise ExecutionServiceError(
                        "The unresolved execution has no safely observed inverse action."
                    )
                for verified in recoverable:
                    normalized = ExecutionAction.model_validate(
                        {
                            **verified.model_dump(),
                            "state": ActionState.VERIFIED,
                            "verification": VerificationState.VERIFIED,
                        }
                    )
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
                        restored = self._undo_action(normalized)
                    except (
                        ActionVerificationError,
                        CommandActionError,
                        ExecutionServiceError,
                        FilesystemActionError,
                        OSError,
                        RuntimeError,
                        ValueError,
                    ) as error:
                        mutation_may_have_occurred = not (
                            isinstance(error, ActionVerificationError)
                            and not error.mutation_attempted
                        ) and not isinstance(error, ExecutionServiceError)
                        failed = ExecutionAction.model_validate(
                            {
                                **verified.model_dump(),
                                "state": (
                                    ActionState.UNDO_IN_PROGRESS
                                    if mutation_may_have_occurred
                                    else ActionState.UNDO_FAILED
                                ),
                                "verification": (
                                    VerificationState.UNKNOWN
                                    if mutation_may_have_occurred
                                    else VerificationState.FAILED
                                ),
                                "error": "The allowlisted inverse action did not complete.",
                            }
                        )
                        manifest = self._revision(
                            manifest,
                            state=(
                                ExecutionState.INTERRUPTED
                                if mutation_may_have_occurred
                                else ExecutionState.UNDO_PARTIAL
                            ),
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
                    if verified is recoverable[-1] and all(
                        action.state
                        in {ActionState.UNDONE, ActionState.PENDING, ActionState.NOT_APPLIED}
                        for action in actions
                    ):
                        actions = tuple(
                            action.model_copy(update={"state": ActionState.NOT_APPLIED})
                            if action.state is ActionState.PENDING
                            else action
                            for action in actions
                        )
                    final_state = (
                        ExecutionState.UNDONE
                        if all(
                            action.state in {ActionState.UNDONE, ActionState.NOT_APPLIED}
                            for action in actions
                        )
                        else (
                            ExecutionState.UNDO_PARTIAL
                            if verified is recoverable[-1]
                            else ExecutionState.UNDO_IN_PROGRESS
                        )
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
            StateLockError,
        ) as error:
            raise ExecutionServiceError("MacWise could not complete the approved undo.") from error
