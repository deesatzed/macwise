"""Pure deterministic scoring of one existing read-only audit."""

from datetime import datetime, timedelta

from macwise.models import (
    AuditDocument,
    ClaimBasis,
    CollectorState,
    EntityType,
    MacWiseScorecard,
    OverlapCategory,
    RecommendationAction,
    Reliability,
    ScoreComponent,
    UsageLabel,
)

_LARGE_APPLICATION_BYTES = 500 * 1024**2
_STALE_BACKUP_AGE = timedelta(days=7)
_NON_USE_LABELS = {UsageLabel.POSSIBLY_UNUSED, UsageLabel.USER_CONFIRMED_UNUSED}
_NON_OPPORTUNITY_OVERLAPS = {
    OverlapCategory.COMPLEMENTARY_TOOLS,
    OverlapCategory.NOT_ACTUALLY_RELATED,
}


def _ratio_points(numerator: int, denominator: int, maximum: int) -> int:
    if denominator <= 0:
        return 0
    return min(maximum, round(maximum * numerator / denominator))


def _component(
    key: str,
    label: str,
    score: int,
    maximum: int,
    observed_count: int,
    reason: str,
    *limitations: str,
) -> ScoreComponent:
    return ScoreComponent(
        key=key,
        label=label,
        score=score,
        maximum=maximum,
        observed_count=observed_count,
        reason=reason,
        limitations=tuple(limitations),
    )


def _opportunity_components(audit: AuditDocument, now: datetime) -> tuple[ScoreComponent, ...]:
    startup_count = len(audit.startup)
    idle_startup = sum(item.running is False or item.enabled is False for item in audit.startup)
    owned_startup = sum(bool(item.owner_software_ids) for item in audit.startup)
    startup_score = min(10, startup_count) + min(5, idle_startup) + min(5, owned_startup)

    actionable_overlaps = tuple(
        item for item in audit.overlaps if item.category not in _NON_OPPORTUNITY_OVERLAPS
    )
    overlap_score = min(20, 4 * len(actionable_overlaps))

    large_apps = tuple(
        item
        for item in audit.software
        if item.entity_type is EntityType.APPLICATION
        and item.size_bytes is not None
        and item.size_bytes >= _LARGE_APPLICATION_BYTES
    )
    low_space_volumes = tuple(
        volume
        for volume in audit.volumes
        if volume.mount_point
        and volume.capacity_bytes
        and volume.free_bytes is not None
        and volume.free_bytes / volume.capacity_bytes <= 0.10
    )
    storage_score = min(15, 2 * len(large_apps)) + min(5, 5 * len(low_space_volumes))

    possible_non_use = tuple(
        finding for finding in audit.findings if finding.usage_label in _NON_USE_LABELS
    )
    non_use_score = min(15, 5 * len(possible_non_use))

    assessed_ids = {item.subject_id for item in audit.catalog_assessments if item.roles}
    unknown_purpose = tuple(
        item for item in audit.software if not item.description and item.id not in assessed_ids
    )
    knowledge_score = min(15, len(unknown_purpose))

    backup = audit.backup
    destination_attention = bool(
        backup is not None
        and (backup.configured is not True or not backup.available_destination_volume_ids)
    )
    age_attention = bool(
        backup is not None
        and (backup.last_backup_at is None or now - backup.last_backup_at > _STALE_BACKUP_AGE)
    )
    backup_limitations = len(backup.limitations) if backup is not None else 0
    backup_score = (4 if destination_attention else 0) + (4 if age_attention else 0)
    backup_score += 2 if backup_limitations else 0

    return (
        _component(
            "startup_attention",
            "Startup attention",
            startup_score,
            20,
            startup_count,
            f"Found {startup_count} startup items; {idle_startup} appeared idle and {owned_startup} had a matched owner.",
            "A startup item is not automatically unnecessary.",
        ),
        _component(
            "tool_overlap",
            "Tool overlap",
            overlap_score,
            20,
            len(actionable_overlaps),
            f"Found {len(actionable_overlaps)} role-aware relations worth comparison.",
            "Complementary and unrelated pairs do not add opportunity points.",
        ),
        _component(
            "storage_review",
            "Storage review",
            storage_score,
            20,
            len(large_apps) + len(low_space_volumes),
            f"Found {len(large_apps)} measured applications at least 500 MiB and {len(low_space_volumes)} mounted low-free-space volumes.",
            "Application size is not a reclaimable-space estimate and excludes related data.",
        ),
        _component(
            "possible_non_use",
            "Possible non-use",
            non_use_score,
            15,
            len(possible_non_use),
            f"Found {len(possible_non_use)} items with supported cautious non-use evidence.",
            "Missing evidence alone never earns points in this component.",
        ),
        _component(
            "knowledge_gaps",
            "Knowledge gaps",
            knowledge_score,
            15,
            len(unknown_purpose),
            f"Found {len(unknown_purpose)} installed records without a known purpose in local evidence or the bundled catalog.",
            "An unknown purpose is a research prompt, not a removal recommendation.",
        ),
        _component(
            "backup_attention",
            "Backup attention",
            backup_score,
            10,
            int(destination_attention) + int(age_attention) + int(bool(backup_limitations)),
            "Checked destination availability, last-verifiable backup age, and recorded limitations.",
            "Backup configuration and non-exclusion do not prove recoverability.",
        ),
    )


def _usefulness_components(audit: AuditDocument) -> tuple[ScoreComponent, ...]:
    complete_collectors = sum(
        status.state is CollectorState.COMPLETE for status in audit.collectors
    )
    collector_points = _ratio_points(complete_collectors, len(audit.collectors), 10)
    assessed_ids = {item.subject_id for item in audit.catalog_assessments if item.roles}
    known_purpose = sum(
        bool(item.description) or item.id in assessed_ids for item in audit.software
    )
    purpose_points = _ratio_points(known_purpose, len(audit.software), 5)
    apps = tuple(item for item in audit.software if item.entity_type is EntityType.APPLICATION)
    measured_apps = sum(item.size_bytes is not None for item in apps)
    size_points = _ratio_points(measured_apps, len(apps), 5)
    owned_startup = sum(bool(item.owner_software_ids) for item in audit.startup)
    stated_startup = sum(
        item.enabled is not None or item.running is not None for item in audit.startup
    )
    startup_points = _ratio_points(owned_startup, len(audit.startup), 3)
    startup_points += _ratio_points(stated_startup, len(audit.startup), 2)
    coverage_score = collector_points + purpose_points + size_points + startup_points

    actionable_recommendations = tuple(
        item
        for item in audit.recommendations
        if item.action is not RecommendationAction.NO_RECOMMENDATION
    )
    actionable_overlaps = tuple(
        item for item in audit.overlaps if item.category not in _NON_OPPORTUNITY_OVERLAPS
    )
    large_apps = sum(
        item.entity_type is EntityType.APPLICATION
        and item.size_bytes is not None
        and item.size_bytes >= _LARGE_APPLICATION_BYTES
        for item in audit.software
    )
    decision_score = min(10, 2 * len(actionable_recommendations))
    decision_score += min(5, 2 * len(actionable_overlaps))
    decision_score += min(5, large_apps)
    decision_score += min(5, owned_startup)
    decision_count = (
        len(actionable_recommendations) + len(actionable_overlaps) + large_apps + owned_startup
    )

    explained_findings = sum(
        item.basis is not ClaimBasis.UNKNOWN
        and item.confidence is not Reliability.UNKNOWN
        and bool(item.evidence_kinds)
        and bool(item.limitations)
        for item in audit.findings
    )
    finding_points = _ratio_points(explained_findings, len(audit.findings), 10)
    explained_recommendations = sum(
        item.basis is not ClaimBasis.UNKNOWN
        and item.confidence is not Reliability.UNKNOWN
        and bool(item.prerequisites or item.limitations)
        for item in audit.recommendations
    )
    recommendation_points = _ratio_points(explained_recommendations, len(audit.recommendations), 10)
    explanation_score = finding_points + recommendation_points

    explicit_health = bool(audit.collectors)
    non_use_is_typed = all(
        finding.usage_label not in _NON_USE_LABELS or finding.basis is not ClaimBasis.UNKNOWN
        for finding in audit.findings
    )
    safety_score = 5 * sum((explicit_health, True, True, non_use_is_typed))
    review_domains = sum(
        (
            bool(audit.software),
            bool(audit.volumes),
            bool(audit.startup),
            bool(audit.overlaps or audit.recommendations),
            audit.backup is not None,
        )
    )
    efficiency_score = 2 * review_domains

    return (
        _component(
            "evidence_coverage",
            "Evidence coverage",
            coverage_score,
            25,
            complete_collectors,
            f"{complete_collectors} of {len(audit.collectors)} collectors completed; purpose, application-size, and startup coverage also contribute.",
            "Collector completion does not make every field known.",
        ),
        _component(
            "decision_yield",
            "Decision yield",
            decision_score,
            25,
            decision_count,
            f"Found {decision_count} evidence-backed recommendation, comparison, storage, or owned-startup review signals.",
            "Decision signals invite review and do not authorize cleanup.",
        ),
        _component(
            "explanation_quality",
            "Explanation quality",
            explanation_score,
            20,
            explained_findings + explained_recommendations,
            f"{explained_findings} of {len(audit.findings)} findings and {explained_recommendations} of {len(audit.recommendations)} recommendations retained the required explanation structure.",
            "This structural metric does not prove that prose is personally helpful.",
        ),
        _component(
            "safety_integrity",
            "Safety integrity",
            safety_score,
            20,
            safety_score // 5,
            "Checked collector health visibility, closed recommendation actions, guarded backup interpretation, and typed non-use evidence.",
            "A full score is a contract check, not proof against every platform edge case.",
        ),
        _component(
            "review_efficiency",
            "Review efficiency",
            efficiency_score,
            10,
            review_domains,
            f"{review_domains} of 5 focused review domains contained collected results.",
            "Efficiency measures available review paths, not time saved for every user.",
        ),
    )


def score_audit(audit: AuditDocument, *, now: datetime) -> MacWiseScorecard:
    """Return two transparent scores without I/O, persistence, or host mutation."""
    opportunity = _opportunity_components(audit, now)
    usefulness = _usefulness_components(audit)
    partial = tuple(
        status.collector
        for status in audit.collectors
        if status.state is not CollectorState.COMPLETE
    )
    limitations = [
        "Opportunity points identify review topics; they do not grade this Mac or authorize removal.",
        "Usefulness measures this audit result; it does not prove personalized correctness or outcomes.",
    ]
    if not audit.collectors:
        limitations.append("Collector status is missing, so evidence coverage is unverified.")
    if partial:
        limitations.append(f"{len(partial)} partial or unavailable collectors limit this score.")
    return MacWiseScorecard(
        opportunity_score=sum(item.score for item in opportunity),
        opportunity_components=opportunity,
        usefulness_score=sum(item.score for item in usefulness),
        usefulness_components=usefulness,
        limitations=tuple(limitations),
    )
