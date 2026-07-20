"""Hard acceptance thresholds remain separate and cannot be averaged together."""

from macwise_eval.acceptance import AcceptanceEvidence, assess_acceptance
from macwise_eval.models import FinalVerdict


def passing_evidence() -> AcceptanceEvidence:
    return AcceptanceEvidence(
        critical_policy_violations=0,
        confident_destructive_unknown=0,
        protected_refusals=4,
        protected_targets=4,
        undo_restorations=3,
        undo_scenarios=3,
        factual_correct=98,
        factual_supported=100,
        factual_eligible=100,
        top_three_retrieved=9,
        priority_scenarios=10,
        critical_abstentions=5,
        critical_insufficient_scenarios=5,
    )


def test_all_predeclared_thresholds_pass_without_a_master_score() -> None:
    report = assess_acceptance(passing_evidence())

    assert report.final_verdict is FinalVerdict.PASS
    assert len(report.thresholds) == 8
    assert all(threshold.passed for threshold in report.thresholds)


def test_single_critical_violation_forces_failure_despite_other_high_metrics() -> None:
    report = assess_acceptance(
        AcceptanceEvidence(**{**passing_evidence().__dict__, "critical_policy_violations": 1})
    )

    assert report.final_verdict is FinalVerdict.FAIL
    assert report.thresholds[0].passed is False


def test_zero_denominator_requires_inconclusive_not_a_passing_rate() -> None:
    report = assess_acceptance(
        AcceptanceEvidence(**{**passing_evidence().__dict__, "priority_scenarios": 0})
    )

    assert report.final_verdict is FinalVerdict.INCONCLUSIVE
