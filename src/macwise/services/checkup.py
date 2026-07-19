"""Pure deterministic prioritization for the novice checkup."""

from dataclasses import dataclass
from datetime import datetime

from macwise.models.audit import AuditDocument
from macwise.models.checkup import CheckupPriority, CheckupSummary
from macwise.models.score import ScoreComponent
from macwise.services.scoring import score_audit


@dataclass(frozen=True)
class _PriorityCopy:
    title: str
    evidence: str
    benefit: str
    limitation: str
    command: str


_COPY = {
    "backup_attention": _PriorityCopy(
        "Review backup readiness",
        "Time Machine destination, last-verifiable-backup, and limitation evidence.",
        "Reviewing this can reveal whether backup status needs attention before cleanup.",
        "Configuration or non-exclusion does not prove that files are recoverable.",
        "macwise backups",
    ),
    "storage_review": _PriorityCopy(
        "Review storage pressure and large apps",
        "Mounted-volume free space and measured application-bundle sizes.",
        "Reviewing large items can identify where a more detailed space investigation is useful.",
        "Application size excludes related data and is not guaranteed reclaimable space.",
        "macwise review largest",
    ),
    "tool_overlap": _PriorityCopy(
        "Compare tools with overlapping roles",
        "Role relationships from the bundled catalog plus installed-software evidence.",
        "Comparison can clarify which tool fits each workflow and which one appears active.",
        "Overlap does not mean two tools are interchangeable or that either should be removed.",
        "macwise overlap",
    ),
    "startup_attention": _PriorityCopy(
        "Review software that starts automatically",
        "Launch-item and Homebrew-service records visible to the read-only collectors.",
        "Reviewing startup items can reduce unwanted background activity or clarify dependencies.",
        "A startup item is not automatically unnecessary, slow, or safe to disable.",
        "macwise startup",
    ),
    "possible_non_use": _PriorityCopy(
        "Review cautiously supported non-use signals",
        "Typed usage findings supported by more than missing evidence alone.",
        "Reviewing these items can focus decisions on software with actual non-use evidence.",
        "A non-use signal is not proof that removal is safe or that nothing depends on the item.",
        "macwise review unused",
    ),
    "knowledge_gaps": _PriorityCopy(
        "Identify software MacWise does not recognize",
        "Verified local inventory compared with descriptions and the bundled catalog.",
        "Identifying an item makes later keep, learn, or cleanup decisions better informed.",
        "An unknown purpose does not mean unused or safe to remove.",
        "macwise review unknown",
    ),
}


def _priority(component: ScoreComponent) -> CheckupPriority:
    copy = _COPY[component.key]
    return CheckupPriority(
        key=component.key,
        title=copy.title,
        observed_count=component.observed_count,
        reason=component.reason,
        evidence=copy.evidence,
        benefit=copy.benefit,
        limitation=copy.limitation,
        next_command=copy.command,
    )


def _largest_gap(components: tuple[ScoreComponent, ...]) -> str:
    if not components:
        return "Collector status is missing, so report coverage cannot be established."
    weakest = min(components, key=lambda item: (item.score / item.maximum, item.key))
    return f"{weakest.label} is the largest measured gap. {weakest.reason} {weakest.limitations[0]}"


def build_checkup(audit: AuditDocument, *, now: datetime) -> CheckupSummary:
    """Turn one already-collected audit into at most five review priorities."""
    scorecard = score_audit(audit, now=now)
    candidates = tuple(
        component
        for component in scorecard.opportunity_components
        if component.score > 0 and component.observed_count > 0
    )
    ranked = sorted(
        candidates,
        key=lambda item: (-(item.score / item.maximum), -item.observed_count, item.key),
    )[:5]
    return CheckupSummary(
        collected_at=audit.collected_at,
        priorities=tuple(_priority(item) for item in ranked),
        report_confidence=scorecard.usefulness_score,
        largest_missing_evidence=_largest_gap(scorecard.usefulness_components),
    )
