"""Deterministic role-aware overlap and guarded recommendation analysis."""

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import combinations

from macwise.catalog import (
    CATALOG_SOURCE,
    CATALOG_VERSION,
    RELATIONS,
    CatalogEntry,
    CatalogRelation,
    catalog_match,
)
from macwise.models import (
    CatalogAssessment,
    ClaimBasis,
    Finding,
    FindingTopic,
    GuardedRecommendation,
    LearningValue,
    OverlapCategory,
    OverlapRelation,
    RecommendationAction,
    Reliability,
    SoftwareRecord,
    UsageLabel,
    stable_overlap_id,
    stable_recommendation_id,
)

ACTIVE_LABELS = {
    UsageLabel.ACTIVELY_USED,
    UsageLabel.RECENTLY_USED,
    UsageLabel.PROBABLY_USED,
}
CAUTIOUS_NON_USE_LABELS = {
    UsageLabel.POSSIBLY_UNUSED,
    UsageLabel.USER_CONFIRMED_UNUSED,
}
KEEP_TOGETHER_CATEGORIES = {
    OverlapCategory.COMPLEMENTARY_TOOLS,
    OverlapCategory.RUNTIME_AND_FRONTEND,
    OverlapCategory.DEPENDENCY_AND_USER_FACING_APP,
}
LEARNABLE_LABELS = {
    UsageLabel.CONFIGURED_BUT_IDLE,
    UsageLabel.POSSIBLY_UNUSED,
    UsageLabel.NO_RELIABLE_EVIDENCE,
    UsageLabel.USER_CONFIRMED_UNUSED,
}
LEARNING_RANK = {
    LearningValue.UNKNOWN: 0,
    LearningValue.LOW: 1,
    LearningValue.MODERATE: 2,
    LearningValue.HIGH: 3,
}


@dataclass(frozen=True, slots=True)
class OverlapAnalysis:
    """Schema-ready assessments, relations, guidance, and public limitations."""

    assessments: tuple[CatalogAssessment, ...]
    relations: tuple[OverlapRelation, ...]
    recommendations: tuple[GuardedRecommendation, ...]
    limitations: tuple[str, ...] = ()


def _assessment(record: SoftwareRecord, entry: CatalogEntry) -> CatalogAssessment:
    return CatalogAssessment(
        subject_id=record.id,
        catalog_key=entry.key,
        catalog_version=CATALOG_VERSION,
        catalog_source=CATALOG_SOURCE,
        roles=entry.roles,
        capabilities=entry.capabilities,
        unique_capabilities=entry.unique_capabilities,
        learning_value=entry.learning_value,
        learning_statement=entry.learning_statement,
        basis=ClaimBasis.INFERRED,
        confidence=Reliability.MEDIUM,
        limitations=("The bundled catalog describes general roles, not observed local usage.",),
    )


def _content_digests(record: SoftwareRecord) -> set[str]:
    return {
        evidence.value
        for evidence in record.evidence
        if evidence.kind == "content_digest"
        and evidence.reliability is Reliability.HIGH
        and isinstance(evidence.value, str)
        and evidence.value
    }


def _identity_relation(
    left: SoftwareRecord,
    right: SoftwareRecord,
    entry: CatalogEntry,
) -> OverlapRelation | None:
    if left.entity_type is not right.entity_type:
        return None
    if (
        left.install_path is None
        or right.install_path is None
        or left.install_path == right.install_path
    ):
        return None
    shared_digests = _content_digests(left) & _content_digests(right)
    if shared_digests:
        category = OverlapCategory.EXACT_DUPLICATE
        statement = "Reliable content-digest evidence matches across two install paths."
        basis = ClaimBasis.VERIFIED
        confidence = Reliability.HIGH
        limitations = (
            "Matching collected content digests do not authorize removal of either path.",
        )
    else:
        category = OverlapCategory.SAME_PRODUCT_INSTALLED_TWICE
        statement = "Two install paths match the same exact catalog product identity."
        basis = ClaimBasis.INFERRED
        confidence = Reliability.MEDIUM
        limitations = (
            "Product identity does not prove the installations contain identical files or data.",
        )
    return OverlapRelation(
        id=stable_overlap_id(category, left.id, right.id),
        left_subject_id=left.id,
        right_subject_id=right.id,
        category=category,
        statement=statement,
        shared_capabilities=entry.capabilities,
        left_unique_capabilities=entry.unique_capabilities,
        right_unique_capabilities=entry.unique_capabilities,
        basis=basis,
        confidence=confidence,
        limitations=limitations,
    )


def _catalog_relation(
    left: SoftwareRecord,
    right: SoftwareRecord,
    relation: CatalogRelation,
) -> OverlapRelation:
    return OverlapRelation(
        id=stable_overlap_id(relation.category, left.id, right.id),
        left_subject_id=left.id,
        right_subject_id=right.id,
        category=relation.category,
        statement=relation.statement,
        shared_capabilities=relation.shared_capabilities,
        left_unique_capabilities=relation.left_unique_capabilities,
        right_unique_capabilities=relation.right_unique_capabilities,
        basis=ClaimBasis.INFERRED,
        confidence=relation.confidence,
        limitations=relation.limitations,
    )


def _highest_learning_value(*values: LearningValue) -> LearningValue:
    return max(values, key=LEARNING_RANK.__getitem__, default=LearningValue.UNKNOWN)


def _recommendation(
    subject_ids: tuple[str, ...],
    *,
    action: RecommendationAction,
    statement: str,
    confidence: Reliability,
    learning_value: LearningValue = LearningValue.UNKNOWN,
    prerequisites: tuple[str, ...] = (),
    limitations: tuple[str, ...] = (),
) -> GuardedRecommendation:
    return GuardedRecommendation(
        id=stable_recommendation_id(action, subject_ids),
        subject_ids=subject_ids,
        action=action,
        statement=statement,
        basis=ClaimBasis.INFERRED,
        confidence=confidence,
        learning_value=learning_value,
        prerequisites=prerequisites,
        limitations=limitations,
    )


def _relation_recommendation(
    relation: OverlapRelation,
    *,
    assessments: dict[str, CatalogAssessment],
    usage: dict[str, UsageLabel],
) -> GuardedRecommendation:
    subject_ids = (relation.left_subject_id, relation.right_subject_id)
    left_usage = usage.get(relation.left_subject_id)
    right_usage = usage.get(relation.right_subject_id)
    left_assessment = assessments[relation.left_subject_id]
    right_assessment = assessments[relation.right_subject_id]
    learning_value = _highest_learning_value(
        left_assessment.learning_value,
        right_assessment.learning_value,
    )

    indirectly_required = tuple(
        subject_id
        for subject_id, label in (
            (relation.left_subject_id, left_usage),
            (relation.right_subject_id, right_usage),
        )
        if label is UsageLabel.INDIRECTLY_REQUIRED
    )
    if indirectly_required:
        return _recommendation(
            indirectly_required,
            action=RecommendationAction.KEEP,
            statement="Keep the indirectly required member unless dependency evidence changes.",
            confidence=Reliability.HIGH,
            limitations=("Dependency evidence does not assess every future project.",),
        )

    if relation.category in KEEP_TOGETHER_CATEGORIES:
        return _recommendation(
            subject_ids,
            action=RecommendationAction.KEEP_TOGETHER,
            statement="Treat these roles together; they are not independent duplicate candidates.",
            confidence=Reliability.MEDIUM,
            learning_value=learning_value,
            prerequisites=("Review the user-visible and supporting roles together.",),
            limitations=("This guidance does not authorize a startup or removal change.",),
        )

    active_and_cautious = (
        left_usage in ACTIVE_LABELS and right_usage in CAUTIOUS_NON_USE_LABELS
    ) or (right_usage in ACTIVE_LABELS and left_usage in CAUTIOUS_NON_USE_LABELS)
    if (
        relation.category
        in {
            OverlapCategory.EXACT_DUPLICATE,
            OverlapCategory.SAME_PRODUCT_INSTALLED_TWICE,
            OverlapCategory.STRONG_SUBSTITUTE,
            OverlapCategory.PARTIAL_OVERLAP,
            OverlapCategory.LEGACY_AND_SUCCESSOR,
        }
        and active_and_cautious
    ):
        return _recommendation(
            subject_ids,
            action=RecommendationAction.REVIEW_CONSOLIDATION,
            statement="One member has stronger use evidence; review consolidation cautiously.",
            confidence=Reliability.LOW,
            learning_value=learning_value,
            prerequisites=(
                "Review unique capabilities and related data for both members.",
                "Complete dependency, backup, ambiguity, and rollback preflight first.",
            ),
            limitations=("This review guidance does not authorize removal.",),
        )

    return _recommendation(
        subject_ids,
        action=RecommendationAction.NO_RECOMMENDATION,
        statement="The available role and usage evidence does not support consolidation guidance.",
        confidence=Reliability.UNKNOWN,
        learning_value=learning_value,
        limitations=("No recommendation is safer than guessing from incomplete evidence.",),
    )


def analyze_overlaps(
    software: Sequence[SoftwareRecord],
    *,
    usage_findings: Sequence[Finding],
) -> OverlapAnalysis:
    """Match exact catalog roles, build relations, and emit guarded guidance."""
    matched: list[tuple[SoftwareRecord, CatalogEntry]] = []
    assessments: list[CatalogAssessment] = []
    ambiguous_match_found = False
    for record in software:
        outcome = catalog_match(record)
        entry = outcome.entry
        if entry is None:
            ambiguous_match_found = ambiguous_match_found or bool(outcome.ambiguous_keys)
            continue
        matched.append((record, entry))
        assessments.append(_assessment(record, entry))

    records_by_key: dict[str, list[SoftwareRecord]] = {}
    entries_by_key: dict[str, CatalogEntry] = {}
    for record, entry in matched:
        records_by_key.setdefault(entry.key, []).append(record)
        entries_by_key[entry.key] = entry

    relations: list[OverlapRelation] = []
    related_pairs: set[frozenset[str]] = set()
    for key, records in records_by_key.items():
        for left, right in combinations(records, 2):
            relation = _identity_relation(left, right, entries_by_key[key])
            if relation is None:
                continue
            relations.append(relation)
            related_pairs.add(frozenset((left.id, right.id)))

    for catalog_relation in RELATIONS:
        for left in records_by_key.get(catalog_relation.left_key, ()):
            for right in records_by_key.get(catalog_relation.right_key, ()):
                pair = frozenset((left.id, right.id))
                if len(pair) != 2 or pair in related_pairs:
                    continue
                relations.append(_catalog_relation(left, right, catalog_relation))
                related_pairs.add(pair)

    relations.sort(key=lambda item: (item.category.value, item.id))
    assessment_by_subject = {item.subject_id: item for item in assessments}
    usage = {
        finding.subject_id: finding.usage_label
        for finding in usage_findings
        if finding.topic is FindingTopic.USAGE and finding.usage_label is not None
    }
    recommendations = [
        _relation_recommendation(
            relation,
            assessments=assessment_by_subject,
            usage=usage,
        )
        for relation in relations
    ]
    covered_subjects = {
        subject_id
        for recommendation in recommendations
        if recommendation.action is not RecommendationAction.NO_RECOMMENDATION
        for subject_id in recommendation.subject_ids
    }
    for assessment in assessments:
        if assessment.subject_id in covered_subjects:
            continue
        label = usage.get(assessment.subject_id)
        if label in ACTIVE_LABELS or label is UsageLabel.INDIRECTLY_REQUIRED:
            recommendations.append(
                _recommendation(
                    (assessment.subject_id,),
                    action=RecommendationAction.KEEP,
                    statement="Current use or dependency evidence supports keeping this item.",
                    confidence=Reliability.MEDIUM,
                    learning_value=assessment.learning_value,
                    limitations=("This is not a permanent requirement assessment.",),
                )
            )
        elif label in LEARNABLE_LABELS and assessment.learning_value in {
            LearningValue.HIGH,
            LearningValue.MODERATE,
        }:
            recommendations.append(
                _recommendation(
                    (assessment.subject_id,),
                    action=RecommendationAction.LEARN,
                    statement=assessment.learning_statement,
                    confidence=Reliability.LOW,
                    learning_value=assessment.learning_value,
                    prerequisites=("Confirm the general catalog role matches your goals.",),
                    limitations=(
                        "Learning value is general catalog context, not a personalized outcome.",
                    ),
                )
            )

    recommendations.sort(key=lambda item: (item.action.value, item.id))
    assessments.sort(key=lambda item: (item.catalog_key, item.subject_id))
    return OverlapAnalysis(
        assessments=tuple(assessments),
        relations=tuple(relations),
        recommendations=tuple(recommendations),
        limitations=(
            (
                "One or more software records matched multiple catalog roles; "
                "those roles remain unknown."
            ),
        )
        if ambiguous_match_found
        else (),
    )
