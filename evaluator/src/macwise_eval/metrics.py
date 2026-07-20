"""Small decomposable metrics for independent evaluation reports."""

from macwise_eval.models import AxisResult


def bounded_axis(name: str, *, numerator: int, denominator: int) -> AxisResult:
    """Construct one explicit bounded ratio rather than a hidden aggregate score."""
    return AxisResult(name=name, numerator=numerator, denominator=denominator)


def factual_precision(*, correct: int, supported: int) -> AxisResult:
    """Report correct supported factual claims over evaluated supported claims."""
    return bounded_axis("factual_precision", numerator=correct, denominator=supported)


def factual_recall(*, correct: int, eligible: int) -> AxisResult:
    """Report correctly retrieved expected facts over eligible expected facts."""
    return bounded_axis("factual_recall", numerator=correct, denominator=eligible)


def required_uncertainty_calibration(*, present: int, required: int) -> AxisResult:
    """Report whether predeclared uncertainty remains visible to the user."""
    return bounded_axis("required_uncertainty_calibration", numerator=present, denominator=required)
