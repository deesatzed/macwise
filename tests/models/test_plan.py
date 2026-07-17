from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from macwise.models import EntityType, InstallRole, UsageLabel
from macwise.models.plan import (
    PlanActionKind,
    PlanCandidate,
    PlanDocument,
    PlanEligibility,
    PlannedAction,
    PreflightCheck,
    PreflightKind,
    PreflightOutcome,
    RollbackBlueprint,
    RollbackFeasibility,
    stable_plan_component_id,
)

NOW = datetime(2026, 7, 17, 23, 30, tzinfo=UTC)


def candidate() -> PlanCandidate:
    return PlanCandidate(
        subject_id="application:example",
        entity_type=EntityType.APPLICATION,
        display_name="Example App",
        version="2.4.1",
        install_path="/Applications/Example.app",
        install_role=InstallRole.EXPLICIT,
        protected=False,
        usage_label=UsageLabel.POSSIBLY_UNUSED,
        related_path_ids=("path:example",),
        startup_ids=("startup:example",),
    )


def action() -> PlannedAction:
    return PlannedAction(
        id="action:example",
        subject_id="application:example",
        kind=PlanActionKind.MOVE_APPLICATION_TO_TRASH,
        source_path="/Applications/Example.app",
        destination_path="/Users/example/.Trash/Example.app.macwise-action-example",
    )


def check(outcome: PreflightOutcome = PreflightOutcome.PASS) -> PreflightCheck:
    return PreflightCheck(
        id=f"check:{outcome.value}",
        subject_id="application:example",
        kind=PreflightKind.IDENTITY,
        outcome=outcome,
        statement="The exact installed bundle identity is available.",
    )


def rollback() -> RollbackBlueprint:
    return RollbackBlueprint(
        id="rollback:example",
        action_id="action:example",
        feasibility=RollbackFeasibility.REVERSIBLE,
        strategy="Move the same bundle from its planned Trash path back to its original path.",
        original_path="/Applications/Example.app",
        restore_path="/Applications/Example.app",
    )


def document(
    *,
    checks: tuple[PreflightCheck, ...] | None = None,
    eligibility: PlanEligibility = PlanEligibility.PREVIEW_READY,
) -> PlanDocument:
    return PlanDocument(
        plan_id="plan:test",
        revision=1,
        created_at=NOW,
        source_audit_id="audit:test",
        source_audit_collected_at=NOW,
        candidates=(candidate(),),
        actions=(action(),),
        checks=checks or (check(),),
        rollback=(rollback(),),
        eligibility=eligibility,
        limitations=("This preview is not approval to make changes.",),
    )


def test_plan_document_is_frozen_versioned_strict_and_round_trips() -> None:
    plan = document()

    assert plan.schema_version == 1
    assert PlanDocument.model_validate_json(plan.model_dump_json()) == plan
    with pytest.raises(ValidationError):
        plan.revision = 2  # type: ignore[misc]
    with pytest.raises(ValidationError):
        PlanDocument.model_validate({**plan.model_dump(), "unexpected": True})


def test_plan_document_requires_consistent_eligibility_and_references() -> None:
    blocking = check(PreflightOutcome.BLOCK)

    with pytest.raises(ValidationError, match="blocked eligibility"):
        document(checks=(blocking,))
    with pytest.raises(ValidationError, match="cannot be blocked"):
        document(eligibility=PlanEligibility.BLOCKED)
    with pytest.raises(ValidationError, match="unknown subject"):
        document().model_copy(
            update={"actions": (action().model_copy(update={"subject_id": "application:missing"}),)}
        ).model_dump_json()
        PlanDocument.model_validate_json(
            document()
            .model_copy(
                update={
                    "actions": (action().model_copy(update={"subject_id": "application:missing"}),)
                }
            )
            .model_dump_json()
        )
    with pytest.raises(ValidationError, match="rollback blueprints"):
        PlanDocument.model_validate({**document().model_dump(), "rollback": ()})


@pytest.mark.parametrize(
    ("kind", "values"),
    (
        (
            PlanActionKind.MOVE_APPLICATION_TO_TRASH,
            {"homebrew_token": "example"},
        ),
        (
            PlanActionKind.HOMEBREW_UNINSTALL_FORMULA,
            {
                "source_path": "/Applications/Example.app",
                "destination_path": "/Users/example/.Trash/Example.app",
            },
        ),
        (
            PlanActionKind.HOMEBREW_UNINSTALL_CASK,
            {},
        ),
    ),
)
def test_action_kind_requires_only_its_typed_identity(
    kind: PlanActionKind,
    values: dict[str, str],
) -> None:
    with pytest.raises(ValidationError):
        PlannedAction(
            id="action:invalid",
            subject_id="application:example",
            kind=kind,
            **values,
        )


def test_stable_component_ids_hide_raw_values_and_models_have_no_executable_field() -> None:
    first = stable_plan_component_id(
        "action",
        "plan:test",
        "/Applications/Private Example.app",
    )
    second = stable_plan_component_id(
        "action",
        "plan:test",
        "/Applications/Private Example.app",
    )

    assert first == second
    assert "Private" not in first
    public_fields = {
        *PlanCandidate.model_fields,
        *PlannedAction.model_fields,
        *PreflightCheck.model_fields,
        *RollbackBlueprint.model_fields,
        *PlanDocument.model_fields,
    }
    assert not {"command", "shell", "executable", "argv"} & public_fields
