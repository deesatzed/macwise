"""Evaluation rendering makes critical verdicts visible before aggregate ratios."""

from macwise_eval.models import AxisResult, EvaluationReport, FinalVerdict
from macwise_eval.reporting import render_json, render_markdown


def failed_report() -> EvaluationReport:
    return EvaluationReport(
        capsule_id="synthetic-case",
        oracle_version="1",
        contract_digest="d" * 64,
        claim_verdicts=(),
        axes=(AxisResult(name="factual_precision", numerator=9, denominator=10),),
        final_verdict=FinalVerdict.FAIL,
        limitations=("MW-EVAL-001: expected pass, observed fail.",),
    )


def test_markdown_places_failed_verdict_and_policy_mismatch_before_metrics() -> None:
    rendered = render_markdown(failed_report())

    assert rendered.index("Final verdict: **FAIL**") < rendered.index("Factual precision")
    assert rendered.index("MW-EVAL-001") < rendered.index("Factual precision")
    assert "master score" not in rendered.lower()


def test_json_is_deterministic_and_schema_backed() -> None:
    first = render_json(failed_report())
    second = render_json(failed_report())

    assert first == second
    assert '"schema_version":1' in first
