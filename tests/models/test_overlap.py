from macwise.models import (
    CatalogAssessment,
    ClaimBasis,
    GuardedRecommendation,
    LearningValue,
    OverlapCategory,
    OverlapRelation,
    RecommendationAction,
    Reliability,
    stable_overlap_id,
    stable_recommendation_id,
)


def test_overlap_categories_match_the_complete_product_contract() -> None:
    assert {category.value for category in OverlapCategory} == {
        "exact_duplicate",
        "same_product_installed_twice",
        "strong_substitute",
        "partial_overlap",
        "complementary_tools",
        "runtime_and_frontend",
        "dependency_and_user_facing_app",
        "legacy_and_successor",
        "not_actually_related",
    }
    assert {action.value for action in RecommendationAction} == {
        "keep",
        "learn",
        "keep_together",
        "review_consolidation",
        "no_recommendation",
    }
    assert "remove" not in {action.value for action in RecommendationAction}


def test_catalog_relation_and_guarded_recommendation_keep_basis_and_limits_typed() -> None:
    assessment = CatalogAssessment(
        subject_id="application:docker",
        catalog_key="docker-desktop",
        catalog_version="2026.07",
        catalog_source="MacWise bundled role catalog",
        roles=("container desktop",),
        capabilities=("containers", "virtual machine management"),
        unique_capabilities=("integrated desktop controls",),
        learning_value=LearningValue.MODERATE,
        learning_statement="Useful for learning a bundled local container workflow.",
        basis=ClaimBasis.INFERRED,
        confidence=Reliability.MEDIUM,
        limitations=("Catalog roles are not observed usage.",),
    )
    relation = OverlapRelation(
        id=stable_overlap_id(
            OverlapCategory.STRONG_SUBSTITUTE,
            "application:docker",
            "application:podman",
        ),
        left_subject_id="application:docker",
        right_subject_id="application:podman",
        category=OverlapCategory.STRONG_SUBSTITUTE,
        statement="Both provide a local container workflow.",
        shared_capabilities=("containers",),
        left_unique_capabilities=("integrated desktop controls",),
        right_unique_capabilities=("daemonless workflow",),
        basis=ClaimBasis.INFERRED,
        confidence=Reliability.MEDIUM,
        limitations=("A role match is not proof of interchangeable projects.",),
    )
    recommendation = GuardedRecommendation(
        id=stable_recommendation_id(
            RecommendationAction.REVIEW_CONSOLIDATION,
            (relation.left_subject_id, relation.right_subject_id),
        ),
        subject_ids=(relation.left_subject_id, relation.right_subject_id),
        action=RecommendationAction.REVIEW_CONSOLIDATION,
        statement="Review the unique workflows before considering consolidation.",
        basis=ClaimBasis.INFERRED,
        confidence=Reliability.LOW,
        learning_value=LearningValue.MODERATE,
        prerequisites=("Review unique data and project dependencies.",),
        limitations=("This does not authorize removal.",),
    )

    assert assessment.catalog_version == "2026.07"
    assert relation.category is OverlapCategory.STRONG_SUBSTITUTE
    assert relation.left_subject_id != relation.right_subject_id
    assert recommendation.action is RecommendationAction.REVIEW_CONSOLIDATION
    assert recommendation.prerequisites
    assert recommendation.limitations == ("This does not authorize removal.",)


def test_stable_overlap_and_recommendation_ids_ignore_subject_order() -> None:
    first = stable_overlap_id(
        OverlapCategory.PARTIAL_OVERLAP,
        "application:first",
        "application:second",
    )
    reversed_id = stable_overlap_id(
        OverlapCategory.PARTIAL_OVERLAP,
        "application:second",
        "application:first",
    )
    recommendation = stable_recommendation_id(
        RecommendationAction.KEEP_TOGETHER,
        ("application:second", "application:first"),
    )
    reversed_recommendation = stable_recommendation_id(
        RecommendationAction.KEEP_TOGETHER,
        ("application:first", "application:second"),
    )

    assert first == reversed_id
    assert recommendation == reversed_recommendation
