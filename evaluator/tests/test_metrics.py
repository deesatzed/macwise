"""Metric helpers expose counts rather than hiding them in a master score."""

from macwise_eval.metrics import bounded_axis, factual_precision, factual_recall


def test_factual_metrics_keep_explicit_numerators_and_denominators() -> None:
    precision = factual_precision(correct=3, supported=4)
    recall = factual_recall(correct=3, eligible=5)
    abstention = bounded_axis("correct_abstention", numerator=2, denominator=2)

    assert (precision.name, precision.numerator, precision.denominator) == (
        "factual_precision",
        3,
        4,
    )
    assert (recall.name, recall.numerator, recall.denominator) == ("factual_recall", 3, 5)
    assert abstention.rate == 1.0
