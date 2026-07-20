"""Decision-value metrics are derived from parsed priority claims, not hand-entered counts."""

from pathlib import Path

from macwise_eval.decision_value import top_three_priority_retrieval
from macwise_eval.product_output import parse_product_output

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
