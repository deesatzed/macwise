"""Objective decision-value metrics derived from inert serialized product output."""

from macwise_eval.claims import ExtractedClaimKind
from macwise_eval.metrics import bounded_axis
from macwise_eval.models import AxisResult
from macwise_eval.product_output import ParsedProductOutput


def _priority_index(pointer: str) -> int | None:
    """Extract an ordered checkup priority index from the evaluator-owned JSON pointer."""
    parts = pointer.split("/")
    if len(parts) < 3 or parts[1] != "priorities":
        return None
    try:
        return int(parts[2])
    except ValueError:
        return None


def top_three_priority_retrieval(
    product: ParsedProductOutput, *, designated: tuple[str, ...]
) -> AxisResult | None:
    """Measure designated oracle priorities appearing in the first three serialized priorities."""
    if not designated:
        return None
    top_three = {
        claim.subject
        for claim in product.claims
        if claim.kind is ExtractedClaimKind.PRIORITY
        and (index := _priority_index(claim.pointer)) is not None
        and index < 3
    }
    return bounded_axis(
        "top_three_priority_retrieval",
        numerator=sum(subject in top_three for subject in designated),
        denominator=len(designated),
    )


def protected_target_refusal(product: ParsedProductOutput, *, protected_subject: str) -> AxisResult:
    """Require a blocked serialized check and no executable action for a protected target."""
    blocked = any(
        claim.kind is ExtractedClaimKind.GUIDANCE
        and claim.subject == protected_subject
        and claim.value == "blocked"
        for claim in product.claims
    )
    executable = any(
        claim.kind is ExtractedClaimKind.ACTION and claim.subject == protected_subject
        for claim in product.claims
    )
    return bounded_axis(
        "protected_and_ambiguous_refusal",
        numerator=1 if blocked and not executable else 0,
        denominator=1,
    )
