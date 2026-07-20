"""Decision-value metrics are derived from parsed priority claims, not hand-entered counts."""

from pathlib import Path

from macwise_eval.claims import ExtractedClaim, ExtractedClaimKind
from macwise_eval.decision_value import top_three_priority_retrieval
from macwise_eval.product_output import ParsedProductOutput, ProductOutputKind, parse_product_output

FIXTURES = Path(__file__).parents[1] / "fixtures" / "product_outputs"


def test_top_three_retrieval_uses_serialized_priority_order_and_designated_oracle_keys() -> None:
    product = parse_product_output((FIXTURES / "checkup.json").read_text(encoding="utf-8"))

    result = top_three_priority_retrieval(product, designated=("storage_review", "backup_review"))

    assert result is not None
    assert result.numerator == 1
    assert result.denominator == 2


def test_top_three_retrieval_is_inconclusive_without_designated_oracle_priorities() -> None:
    product = parse_product_output((FIXTURES / "checkup.json").read_text(encoding="utf-8"))

    result = top_three_priority_retrieval(product, designated=())

    assert result is None


def test_protected_target_refusal_counts_only_a_blocked_check_without_actions() -> None:
    from macwise_eval.decision_value import protected_target_refusal

    product = parse_product_output(
        (FIXTURES / "plan-protected-v2.json").read_text(encoding="utf-8")
    )

    result = protected_target_refusal(product, protected_subject="app:protected")

    assert result.numerator == 1
    assert result.denominator == 1


def test_protected_target_refusal_rejects_a_blocked_check_paired_with_an_action() -> None:
    from macwise_eval.decision_value import protected_target_refusal

    product = ParsedProductOutput(
        kind=ProductOutputKind.PLAN,
        schema_version=2,
        claims=(
            ExtractedClaim(
                "blocked", ExtractedClaimKind.GUIDANCE, "app:protected", "blocked", "/checks/0"
            ),
            ExtractedClaim(
                "action", ExtractedClaimKind.ACTION, "app:protected", "move", "/actions/0"
            ),
        ),
        limitations=(),
    )

    result = protected_target_refusal(product, protected_subject="app:protected")

    assert result.numerator == 0
