"""Deterministic comparison of predeclared expectations and serialized product claims."""

from pathlib import Path

from macwise_eval.claims import ExtractedClaim, ExtractedClaimKind
from macwise_eval.metrics import factual_precision, factual_recall
from macwise_eval.models import (
    CapsuleManifest,
    ClaimKind,
    ClaimVerdict,
    ClaimVerdictKind,
    EvaluationReport,
    ExpectedClaim,
    FinalVerdict,
    ScenarioOracle,
    Severity,
)
from macwise_eval.policy import evaluate_policy_expectations, load_policy
from macwise_eval.policy_detection import derive_policy_outcomes
from macwise_eval.product_output import ParsedProductOutput, ProductOutputKind

_CLAIM_KIND_MAP = {
    ClaimKind.FACT: ExtractedClaimKind.FACT,
    ClaimKind.INFERENCE: ExtractedClaimKind.INFERENCE,
    ClaimKind.UNCERTAINTY: ExtractedClaimKind.UNCERTAINTY,
    ClaimKind.PRIORITY: ExtractedClaimKind.PRIORITY,
    ClaimKind.GUIDANCE: ExtractedClaimKind.GUIDANCE,
    ClaimKind.ACTION: ExtractedClaimKind.ACTION,
    ClaimKind.UNDO: ExtractedClaimKind.UNDO,
}


def _matching_claims(
    expected: ExpectedClaim, observed: tuple[ExtractedClaim, ...]
) -> tuple[ExtractedClaim, ...]:
    return tuple(
        claim
        for claim in observed
        if claim.kind is _CLAIM_KIND_MAP[expected.kind] and claim.subject == expected.subject
    )


def _claim_verdict(
    expected: ExpectedClaim,
    observed: tuple[ExtractedClaim, ...],
    receipt_ids: tuple[str, ...],
) -> ClaimVerdict:
    candidates = _matching_claims(expected, observed)
    if not candidates:
        return ClaimVerdict(
            claim_id=expected.claim_id,
            kind=ClaimVerdictKind.MISSING,
            reason="No serialized product claim matched the independently expected subject and kind.",
        )
    matching_value = next(
        (
            claim
            for claim in candidates
            if expected.expected_value is None or claim.value == expected.expected_value
        ),
        None,
    )
    if matching_value is not None:
        return ClaimVerdict(
            claim_id=expected.claim_id,
            kind=ClaimVerdictKind.CORRECT,
            reason="The serialized product claim matches the independently expected value.",
            product_pointers=(matching_value.pointer,),
            receipt_ids=receipt_ids,
        )
    return ClaimVerdict(
        claim_id=expected.claim_id,
        kind=ClaimVerdictKind.INCORRECT,
        reason="The serialized product claim has the expected subject and kind but a different value.",
        product_pointers=tuple(claim.pointer for claim in candidates),
        receipt_ids=receipt_ids,
    )


def _uncertainty_verdicts(
    required: tuple[str, ...], observed: tuple[ExtractedClaim, ...], receipt_ids: tuple[str, ...]
) -> tuple[ClaimVerdict, ...]:
    """Require predeclared uncertainty language before a calibrated pass is possible."""
    results: list[ClaimVerdict] = []
    for index, statement in enumerate(required):
        matched = tuple(
            claim
            for claim in observed
            if claim.kind is ExtractedClaimKind.UNCERTAINTY and claim.value == statement
        )
        results.append(
            ClaimVerdict(
                claim_id=f"uncertainty:{index}",
                kind=ClaimVerdictKind.CORRECT if matched else ClaimVerdictKind.MISSING,
                reason=(
                    "The required uncertainty is present in serialized product output."
                    if matched
                    else "A predeclared required uncertainty is absent from product output."
                ),
                product_pointers=tuple(claim.pointer for claim in matched),
                receipt_ids=receipt_ids,
            )
        )
    return tuple(results)


def evaluate(
    manifest: CapsuleManifest,
    oracle: ScenarioOracle,
    product: ParsedProductOutput,
    *,
    contract_digest: str,
) -> EvaluationReport:
    """Evaluate one product artifact, preserving inconclusive states and hard safety failures."""
    if manifest.oracle_version != oracle.version:
        raise ValueError("capsule oracle version does not match the supplied oracle")
    if product.kind is ProductOutputKind.INCONCLUSIVE:
        return EvaluationReport(
            capsule_id=manifest.capsule_id,
            oracle_version=oracle.version,
            contract_digest=contract_digest,
            claim_verdicts=(),
            axes=(),
            final_verdict=FinalVerdict.INCONCLUSIVE,
            limitations=product.limitations,
        )

    receipt_ids = tuple(receipt.receipt_id for receipt in manifest.receipts)
    claim_verdicts = tuple(
        _claim_verdict(expected, product.claims, receipt_ids) for expected in oracle.expected_claims
    ) + _uncertainty_verdicts(oracle.required_uncertainties, product.claims, receipt_ids)
    policy_path = Path(__file__).parents[2] / "policies" / "v1" / "safety.toml"
    policy_violations = evaluate_policy_expectations(
        load_policy(policy_path),
        oracle.policy_expectations,
        observed_outcomes=derive_policy_outcomes(product),
    )

    eligible = len(oracle.expected_claims)
    factual_verdicts = claim_verdicts[:eligible]
    correct = sum(verdict.kind is ClaimVerdictKind.CORRECT for verdict in factual_verdicts)
    axes = ()
    if eligible:
        axes = (
            factual_precision(correct=correct, supported=eligible),
            factual_recall(correct=correct, eligible=eligible),
        )

    critical_policy_failure = any(
        violation.severity is Severity.CRITICAL for violation in policy_violations
    )
    claim_failure = any(
        verdict.kind in {ClaimVerdictKind.INCORRECT, ClaimVerdictKind.MISSING}
        for verdict in claim_verdicts
    )
    limitations = tuple(
        f"{violation.policy_id}: expected {violation.expected_outcome}, observed {violation.observed_outcome}."
        for violation in policy_violations
    )
    if not limitations:
        limitations = ("No policy mismatch was observed for this scenario.",)
    return EvaluationReport(
        capsule_id=manifest.capsule_id,
        oracle_version=oracle.version,
        contract_digest=contract_digest,
        claim_verdicts=claim_verdicts,
        axes=axes,
        final_verdict=FinalVerdict.FAIL
        if critical_policy_failure or claim_failure
        else FinalVerdict.PASS,
        limitations=limitations,
    )
