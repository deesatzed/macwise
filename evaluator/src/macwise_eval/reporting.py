"""Deterministic evaluator reports that expose hard failures before metrics."""

from macwise_eval.io import canonical_json
from macwise_eval.models import EvaluationReport


def render_json(report: EvaluationReport) -> str:
    """Render the stable machine-readable evaluator report."""
    return canonical_json(report)


def _label(name: str) -> str:
    return name.replace("_", " ").capitalize()


def render_markdown(report: EvaluationReport) -> str:
    """Render a concise review report without a combined or compensating score."""
    lines = [
        "# MacWise evaluation",
        "",
        f"Final verdict: **{report.final_verdict.value.upper()}**",
        "",
        "## Safety and policy status",
        "",
    ]
    lines.extend(f"- {limitation}" for limitation in report.limitations)
    lines.extend(("", "## Metrics", ""))
    if report.axes:
        lines.extend(
            f"- {_label(axis.name)}: {axis.numerator}/{axis.denominator} ({axis.rate:.1%})"
            for axis in report.axes
        )
    else:
        lines.append("- No metrics were calculated because the product output was inconclusive.")
    lines.extend(("", "## Traceability", ""))
    lines.extend(
        (
            f"- Capsule: `{report.capsule_id}`",
            f"- Oracle version: `{report.oracle_version}`",
            f"- Contract digest: `{report.contract_digest}`",
            "",
        )
    )
    return "\n".join(lines)
