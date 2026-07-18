import pytest
from pydantic import ValidationError

from macwise.models import MacWiseScorecard, ScoreComponent


def component(key: str, score: int, maximum: int) -> ScoreComponent:
    return ScoreComponent(
        key=key,
        label=key.replace("_", " ").title(),
        score=score,
        maximum=maximum,
        observed_count=score,
        reason="The score follows deterministic audit evidence.",
    )


def valid_scorecard() -> MacWiseScorecard:
    opportunity = (
        component("startup_attention", 10, 20),
        component("tool_overlap", 10, 20),
        component("storage_review", 10, 20),
        component("possible_non_use", 5, 15),
        component("knowledge_gaps", 5, 15),
        component("backup_attention", 5, 10),
    )
    usefulness = (
        component("evidence_coverage", 20, 25),
        component("decision_yield", 20, 25),
        component("explanation_quality", 15, 20),
        component("safety_integrity", 20, 20),
        component("review_efficiency", 10, 10),
    )
    return MacWiseScorecard(
        opportunity_score=45,
        opportunity_components=opportunity,
        usefulness_score=85,
        usefulness_components=usefulness,
        limitations=("Scores describe this audit, not personal value.",),
    )


def test_scorecard_requires_exact_components_and_matching_totals() -> None:
    scorecard = valid_scorecard()

    assert scorecard.opportunity_score == 45
    assert scorecard.usefulness_score == 85
    assert scorecard.opportunity_components[0].maximum == 20
    assert scorecard.model_dump()["limitations"]


def test_score_component_rejects_out_of_range_or_extra_values() -> None:
    with pytest.raises(ValidationError):
        ScoreComponent(
            key="bad",
            label="Bad",
            score=11,
            maximum=10,
            observed_count=0,
            reason="Invalid score.",
        )
    with pytest.raises(ValidationError):
        ScoreComponent.model_validate(
            {
                "key": "bad",
                "label": "Bad",
                "score": 1,
                "maximum": 10,
                "observed_count": 0,
                "reason": "Invalid field.",
                "invented": True,
            }
        )


def test_scorecard_rejects_missing_components_or_inconsistent_total() -> None:
    valid = valid_scorecard()
    missing = valid.model_dump()
    missing["opportunity_components"] = missing["opportunity_components"][:-1]
    with pytest.raises(ValidationError, match="opportunity component keys"):
        MacWiseScorecard.model_validate(missing)

    data = valid.model_dump()
    data["usefulness_score"] = 84
    with pytest.raises(ValidationError, match="usefulness_score"):
        MacWiseScorecard.model_validate(data)
