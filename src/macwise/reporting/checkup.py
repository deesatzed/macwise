"""Novice terminal rendering for one fresh read-only checkup."""

from textwrap import wrap

from macwise.models import CheckupPriority, CheckupSummary

_WIDTH = 96


def _wrapped(label: str, value: str, *, indent: str = "") -> list[str]:
    prefix = f"{indent}{label}"
    return wrap(
        value,
        width=_WIDTH,
        initial_indent=prefix,
        subsequent_indent=" " * len(prefix),
        break_long_words=False,
        break_on_hyphens=False,
    )


def render_checkup_terminal(summary: CheckupSummary) -> str:
    """Render a bounded summary without names, paths, or mutation language."""
    lines = [
        "Fresh read-only checkup",
        f"Collected: {summary.collected_at.isoformat()}",
        *_wrapped(
            "", "This is fresh evidence collected for this command. It was not silently saved."
        ),
        "",
        "What deserves attention first",
    ]
    if not summary.priorities:
        lines.extend(
            [
                "",
                "MacWise found no supported priority in the evidence it could collect.",
                "That does not prove there is nothing to review.",
            ]
        )
    for index, priority in enumerate(summary.priorities, start=1):
        lines.extend(_priority_lines(index, priority))
    lines.extend(
        [
            "",
            f"Confidence in this report: {summary.report_confidence}/100",
            summary.confidence_limitation,
            *_wrapped("Largest missing evidence: ", summary.largest_missing_evidence),
            "",
            "MacWise changed nothing on this Mac.",
        ]
    )
    return f"{'\n'.join(lines)}\n"


def render_checkup_focus(priority: CheckupPriority) -> str:
    """Render one selected priority within the same terminal width contract."""
    lines = [
        "Focused review",
        "",
        priority.title,
        f"- Observed: {priority.observed_count}",
        *_wrapped("- Evidence: ", priority.evidence),
        *_wrapped("- Why it may matter: ", priority.benefit),
        *_wrapped("- Important limit: ", priority.limitation),
        *_wrapped("- Continue later with: ", priority.next_command),
    ]
    return f"{'\n'.join(lines)}\n"


def _priority_lines(index: int, priority: CheckupPriority) -> list[str]:
    return [
        "",
        f"{index}. {priority.title} ({priority.observed_count} observed)",
        *_wrapped("Why: ", priority.reason, indent="   "),
        *_wrapped("Evidence: ", priority.evidence, indent="   "),
        *_wrapped("Possible benefit: ", priority.benefit, indent="   "),
        *_wrapped("What this does not prove: ", priority.limitation, indent="   "),
        *_wrapped("Safest next step: ", priority.next_command, indent="   "),
    ]
