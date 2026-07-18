"""Render aggregate scorecards without exposing raw inventory."""

from macwise.models import MacWiseScorecard, ScoreComponent


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
        f"Opportunity Profile: {scorecard.opportunity_score}/100",
        "This measures review-worthy evidence. A high score does not grade this Mac as bad.",
        "",
    ]
    for component in scorecard.opportunity_components:
        lines.extend(_terminal_component(component))
    lines.extend(
        [
            "",
            f"MacWise Usefulness Score: {scorecard.usefulness_score}/100",
            "This measures the audit result. It does not prove personalized correctness.",
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
        f"## Opportunity Profile: {scorecard.opportunity_score}/100",
        "",
        "This measures review-worthy evidence. A high score does not grade this Mac as bad.",
        "",
        *_markdown_components(scorecard.opportunity_components),
        f"## MacWise Usefulness Score: {scorecard.usefulness_score}/100",
        "",
        "This measures the audit result. It does not prove personalized correctness.",
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
