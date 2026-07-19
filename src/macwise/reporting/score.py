"""Render aggregate scorecards without exposing raw inventory."""

from macwise.models import MacWiseScorecard, ScoreComponent


def _opportunity_level(score: int) -> str:
    if score >= 70:
        return "High"
    if score >= 35:
        return "Moderate"
    return "Low"


def _largest_missing_evidence(scorecard: MacWiseScorecard) -> str:
    weakest = min(
        scorecard.usefulness_components,
        key=lambda item: (item.score / item.maximum, item.key),
    )
    return f"{weakest.label}. {weakest.limitations[0]}"


def render_score_json(scorecard: MacWiseScorecard) -> str:
    """Return deterministic structured scorecard JSON."""
    return f"{scorecard.model_dump_json(indent=2)}\n"


def _terminal_component(component: ScoreComponent) -> list[str]:
    lines = [
        f"- {component.label}: {component.score}/{component.maximum} "
        f"({component.observed_count} observed)",
        f"  Why: {component.reason}",
    ]
    lines.extend(f"  Limitation: {item}" for item in component.limitations)
    return lines


def render_score_terminal(scorecard: MacWiseScorecard) -> str:
    """Return a compact novice-facing terminal scorecard."""
    lines = [
        "MacWise scorecard",
        "",
        f"Review opportunities found: {_opportunity_level(scorecard.opportunity_score)} "
        f"({scorecard.opportunity_score}/100 detail score)",
        "This counts supported topics worth reviewing. It does not grade this Mac or its owner.",
        "",
    ]
    for component in scorecard.opportunity_components:
        lines.extend(_terminal_component(component))
    lines.extend(
        [
            "",
            f"Confidence in this report: {scorecard.usefulness_score}/100",
            "This measures evidence coverage and explanation structure. It does not prove personalized correctness.",
            f"Largest missing evidence: {_largest_missing_evidence(scorecard)}",
            "",
        ]
    )
    for component in scorecard.usefulness_components:
        lines.extend(_terminal_component(component))
    lines.extend(["", "Important limitations"])
    lines.extend(f"- {item}" for item in scorecard.limitations)
    lines.extend(
        [
            "",
            "Next:",
            "  macwise startup",
            "  macwise overlap",
            "  macwise review largest",
            "  macwise review unknown",
            "",
            "This command is read-only. MacWise did not change this Mac.",
        ]
    )
    return f"{'\n'.join(lines)}\n"


def _markdown_components(components: tuple[ScoreComponent, ...]) -> list[str]:
    lines: list[str] = []
    for component in components:
        lines.extend(
            [
                f"### {component.label}: {component.score}/{component.maximum}",
                "",
                f"Observed count: {component.observed_count}",
                "",
                f"Why: {component.reason}",
                "",
            ]
        )
        lines.extend(f"- Limitation: {item}" for item in component.limitations)
        lines.append("")
    return lines


def render_score_markdown(scorecard: MacWiseScorecard) -> str:
    """Return a standalone Markdown score report."""
    lines = [
        "# MacWise scorecard",
        "",
        f"## Review opportunities found: {_opportunity_level(scorecard.opportunity_score)} ({scorecard.opportunity_score}/100 detail score)",
        "",
        "This counts supported topics worth reviewing. It does not grade this Mac or its owner.",
        "",
        *_markdown_components(scorecard.opportunity_components),
        f"## Confidence in this report: {scorecard.usefulness_score}/100",
        "",
        "This measures evidence coverage and explanation structure. It does not prove personalized correctness.",
        "",
        f"Largest missing evidence: {_largest_missing_evidence(scorecard)}",
        "",
        *_markdown_components(scorecard.usefulness_components),
        "## Important limitations",
        "",
        *(f"- {item}" for item in scorecard.limitations),
        "",
        "This report is read-only. MacWise did not change this Mac.",
        "",
    ]
    return "\n".join(lines)
