from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from macwise.models import (
    ActionObservation,
    ActionState,
    ExecutionAction,
    ExecutionRun,
    ExecutionState,
    InverseIntent,
    InverseKind,
    PlanActionKind,
    VerificationState,
)

NOW = datetime(2026, 7, 18, 2, 0, tzinfo=UTC)
DIGEST = "a" * 64


def action(
    *,
    state: ActionState = ActionState.PENDING,
    verification: VerificationState = VerificationState.PENDING,
) -> ExecutionAction:
    return ExecutionAction(
        plan_action_id="action:example",
        sequence=1,
        subject_id="application:example",
        kind=PlanActionKind.MOVE_APPLICATION_TO_TRASH,
        state=state,
        verification=verification,
        before=ActionObservation(exists=True, device=42, inode=100),
        after=(
            ActionObservation(exists=True, device=42, inode=100)
            if state is ActionState.VERIFIED
            else None
        ),
        inverse=InverseIntent(
            kind=InverseKind.RESTORE_FROM_TRASH,
            source_path="/Users/example/.Trash/Example.app.macwise-test",
            destination_path="/Applications/Example.app",
        ),
    )


def run(
    *,
    state: ExecutionState = ExecutionState.PREPARED,
    actions: tuple[ExecutionAction, ...] | None = None,
) -> ExecutionRun:
    return ExecutionRun(
        run_id="run:test",
        manifest_revision=1,
        plan_id="plan:test",
        plan_revision=2,
        plan_digest=DIGEST,
        approval_fingerprint="A" * 16,
        created_at=NOW,
        updated_at=NOW,
        state=state,
        actions=actions or (action(),),
        limitations=("Homebrew restoration may be best effort.",),
    )


def test_execution_run_is_frozen_strict_versioned_and_round_trips() -> None:
    manifest = run()

    assert manifest.schema_version == 1
    assert ExecutionRun.model_validate_json(manifest.model_dump_json()) == manifest
    with pytest.raises(ValidationError):
        manifest.state = ExecutionState.SUCCEEDED  # type: ignore[misc]
    with pytest.raises(ValidationError):
        ExecutionRun.model_validate({**manifest.model_dump(), "unexpected": True})


def test_execution_run_requires_exact_fingerprint_unique_order_and_truthful_success() -> None:
    with pytest.raises(ValidationError, match="approval fingerprint"):
        ExecutionRun.model_validate({**run().model_dump(), "approval_fingerprint": "B" * 16})

    duplicate = action().model_copy(update={"plan_action_id": "action:second"})
    with pytest.raises(ValidationError, match="contiguous action sequence"):
        ExecutionRun.model_validate({**run().model_dump(), "actions": (action(), duplicate)})

    with pytest.raises(ValidationError, match="verified actions"):
        ExecutionRun.model_validate({**run().model_dump(), "state": ExecutionState.SUCCEEDED})

    verified = action(
        state=ActionState.VERIFIED,
        verification=VerificationState.VERIFIED,
    )
    succeeded = run(state=ExecutionState.SUCCEEDED, actions=(verified,))
    assert succeeded.state is ExecutionState.SUCCEEDED


def test_execution_models_have_no_generic_command_or_argv_field() -> None:
    public_fields = {
        *ActionObservation.model_fields,
        *InverseIntent.model_fields,
        *ExecutionAction.model_fields,
        *ExecutionRun.model_fields,
    }

    assert not {"command", "shell", "executable", "argv"} & public_fields
