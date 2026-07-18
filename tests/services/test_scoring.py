from datetime import UTC, datetime, timedelta

from macwise.models import (
    AuditDocument,
    BackupStatus,
    CatalogAssessment,
    ClaimBasis,
    CollectorState,
    CollectorStatus,
    EntityType,
    Finding,
    FindingTopic,
    GuardedRecommendation,
    LearningValue,
    MacWiseScorecard,
    OverlapCategory,
    OverlapRelation,
    RecommendationAction,
    Reliability,
    ScoreComponent,
    SoftwareRecord,
    StartupKind,
    StartupRecord,
    StorageLocation,
    UsageLabel,
    VolumeRecord,
    stable_software_id,
)
from macwise.services import score_audit

NOW = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)


def app(index: int, *, described: bool = True, size_gib: int | None = 1) -> SoftwareRecord:
    return SoftwareRecord(
        id=stable_software_id(EntityType.APPLICATION, f"org.example.{index}"),
        entity_type=EntityType.APPLICATION,
        name=f"app-{index}",
        display_name=f"App {index}",
        description="A fictional application." if described else None,
        size_bytes=size_gib * 1024**3 if size_gib is not None else None,
        storage_location=StorageLocation.INTERNAL,
    )


def component(scorecard: MacWiseScorecard, key: str) -> ScoreComponent:
    groups = (scorecard.opportunity_components, scorecard.usefulness_components)
    return next(item for group in groups for item in group if item.key == key)


def test_empty_audit_scores_zero_opportunity_and_explains_missing_coverage() -> None:
    scorecard = score_audit(AuditDocument(audit_id="empty", collected_at=NOW), now=NOW)

    assert scorecard.opportunity_score == 0
    assert component(scorecard, "evidence_coverage").score == 0
    assert component(scorecard, "decision_yield").score == 0
    assert any("collector status is missing" in item.casefold() for item in scorecard.limitations)


def test_opportunity_components_cap_and_ignore_unsafe_non_use_or_complements() -> None:
    applications = tuple(app(index, described=False) for index in range(20))
    startup = tuple(
        StartupRecord(
            id=f"startup:{index}",
            label=f"agent-{index}",
            kind=StartupKind.LAUNCH_AGENT,
            owner_software_ids=(applications[index].id,) if index < 10 else (),
            running=False,
        )
        for index in range(20)
    )
    findings = tuple(
        Finding(
            subject_id=item.id,
            topic=FindingTopic.USAGE,
            statement="No reliable use evidence was available.",
            basis=ClaimBasis.UNKNOWN,
            confidence=Reliability.UNKNOWN,
            usage_label=UsageLabel.NO_RELIABLE_EVIDENCE,
            limitations=("Missing evidence is not proof of non-use.",),
        )
        for item in applications
    )
    complementary = OverlapRelation(
        id="overlap:complementary",
        left_subject_id=applications[0].id,
        right_subject_id=applications[1].id,
        category=OverlapCategory.COMPLEMENTARY_TOOLS,
        statement="The fictional tools work together.",
        basis=ClaimBasis.INFERRED,
        confidence=Reliability.MEDIUM,
    )
    audit = AuditDocument(
        audit_id="capped",
        collected_at=NOW,
        software=applications,
        startup=startup,
        findings=findings,
        overlaps=(complementary,),
        backup=BackupStatus(
            configured=True,
            last_backup_at=NOW - timedelta(days=30),
            limitations=("Coverage is not verified.",),
        ),
        volumes=(
            VolumeRecord(
                id="volume:low",
                name="Disk",
                device_identifier="disk1",
                mount_point="/",
                location=StorageLocation.INTERNAL,
                capacity_bytes=100,
                free_bytes=5,
            ),
        ),
    )

    scorecard = score_audit(audit, now=NOW)

    assert component(scorecard, "startup_attention").score == 20
    assert component(scorecard, "storage_review").score == 20
    assert component(scorecard, "knowledge_gaps").score == 15
    assert component(scorecard, "possible_non_use").score == 0
    assert component(scorecard, "tool_overlap").score == 0
    assert component(scorecard, "backup_attention").score == 10


def test_usefulness_rewards_covered_explained_decisions_but_surfaces_partial_collection() -> None:
    applications = (app(1), app(2))
    statuses = (
        CollectorStatus(
            collector="applications",
            state=CollectorState.COMPLETE,
            collected_at=NOW,
            records_count=2,
        ),
        CollectorStatus(
            collector="startup",
            state=CollectorState.PARTIAL,
            collected_at=NOW,
            records_count=1,
            limitations=("One source was unavailable.",),
        ),
    )
    assessment = CatalogAssessment(
        subject_id=applications[0].id,
        catalog_key="example",
        catalog_version="1",
        catalog_source="bundled",
        roles=("editor",),
        learning_statement="A fictional role.",
        basis=ClaimBasis.INFERRED,
        confidence=Reliability.MEDIUM,
    )
    finding = Finding(
        subject_id=applications[0].id,
        topic=FindingTopic.USAGE,
        statement="Recently used.",
        basis=ClaimBasis.VERIFIED,
        confidence=Reliability.MEDIUM,
        usage_label=UsageLabel.RECENTLY_USED,
        evidence_kinds=("spotlight",),
        limitations=("Metadata may be stale.",),
    )
    relation = OverlapRelation(
        id="overlap:substitute",
        left_subject_id=applications[0].id,
        right_subject_id=applications[1].id,
        category=OverlapCategory.STRONG_SUBSTITUTE,
        statement="Both edit fictional files.",
        basis=ClaimBasis.INFERRED,
        confidence=Reliability.MEDIUM,
        limitations=("Roles do not prove interchangeability.",),
    )
    recommendation = GuardedRecommendation(
        id="recommendation:review",
        subject_ids=(applications[0].id, applications[1].id),
        action=RecommendationAction.REVIEW_CONSOLIDATION,
        statement="Review unique workflows.",
        basis=ClaimBasis.INFERRED,
        confidence=Reliability.MEDIUM,
        learning_value=LearningValue.MODERATE,
        prerequisites=("Confirm unique data.",),
        limitations=("This does not authorize removal.",),
    )
    audit = AuditDocument(
        audit_id="useful",
        collected_at=NOW,
        software=applications,
        collectors=statuses,
        findings=(finding,),
        catalog_assessments=(assessment,),
        overlaps=(relation,),
        recommendations=(recommendation,),
    )

    scorecard = score_audit(audit, now=NOW)

    assert component(scorecard, "decision_yield").score > 0
    assert component(scorecard, "explanation_quality").score == 20
    assert component(scorecard, "safety_integrity").score == 20
    assert component(scorecard, "evidence_coverage").score < 25
    assert any("partial" in item.casefold() for item in scorecard.limitations)
