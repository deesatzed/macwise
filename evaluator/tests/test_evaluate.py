"""Deterministic independent comparison keeps critical safety failures non-averageable."""

from dataclasses import replace
from pathlib import Path

from macwise_eval.evaluate import evaluate
from macwise_eval.models import (
    CapsuleManifest,
    FinalVerdict,
    ScenarioOracle,
)
from macwise_eval.mutations import critical_mutants
from macwise_eval.product_output import parse_product_output

FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures"


def load_fixture_models() -> tuple[CapsuleManifest, ScenarioOracle]:
    capsule_root = FIXTURE_ROOT / "synthetic" / "minimal"
    return (
        CapsuleManifest.model_validate_json(
            (capsule_root / "manifest.json").read_text(encoding="utf-8")
        ),
        ScenarioOracle.model_validate_json(
            (capsule_root / "oracle.json").read_text(encoding="utf-8")
        ),
    )


def test_evaluation_reports_exact_fact_metrics_and_passes_matching_safety_policy() -> None:
    manifest, oracle = load_fixture_models()
    product = parse_product_output(
        (FIXTURE_ROOT / "product_outputs" / "audit-v4.json").read_text(encoding="utf-8")
    )

    report = evaluate(
        manifest,
        oracle,
        product,
        contract_digest="c" * 64,
    )

    assert report.final_verdict is FinalVerdict.PASS
    assert report.claim_verdicts[0].kind.value == "correct"
    assert {(axis.name, axis.numerator, axis.denominator) for axis in report.axes} >= {
        ("factual_precision", 1, 1),
        ("factual_recall", 1, 1),
    }


def test_critical_policy_failure_forces_fail_even_when_facts_match() -> None:
    manifest, oracle = load_fixture_models()
    product = parse_product_output(
        (FIXTURE_ROOT / "product_outputs" / "audit-v4.json").read_text(encoding="utf-8")
    )
    unsafe = next(mutant for mutant in critical_mutants() if mutant.policy_id == "MW-EVAL-004")
    product = replace(product, claims=product.claims + unsafe.product_output().claims)

    report = evaluate(
        manifest,
        oracle,
        product,
        contract_digest="c" * 64,
    )

    assert report.final_verdict is FinalVerdict.FAIL
    assert "MW-EVAL-004" in report.limitations[0]


def test_inconclusive_product_output_cannot_be_scored_as_a_pass() -> None:
    manifest, oracle = load_fixture_models()
    product = parse_product_output('{"audit_id":"future","schema_version":99}')

    report = evaluate(
        manifest,
        oracle,
        product,
        contract_digest="c" * 64,
    )

    assert report.final_verdict is FinalVerdict.INCONCLUSIVE
    assert report.axes == ()


def test_missing_required_uncertainty_is_a_calibration_failure() -> None:
    manifest, oracle = load_fixture_models()
    product = parse_product_output(
        (FIXTURE_ROOT / "product_outputs" / "audit-v4.json").read_text(encoding="utf-8")
    )
    product = replace(
        product,
        claims=tuple(claim for claim in product.claims if claim.kind.value != "uncertainty"),
    )

    report = evaluate(manifest, oracle, product, contract_digest="c" * 64)

    assert report.final_verdict is FinalVerdict.FAIL
    assert any(verdict.claim_id == "uncertainty:0" for verdict in report.claim_verdicts)
    assert any(verdict.kind.value == "missing" for verdict in report.claim_verdicts)
