from datetime import UTC, datetime

from macwise.models import (
    ClaimBasis,
    EntityType,
    Evidence,
    Finding,
    FindingTopic,
    OverlapCategory,
    RecommendationAction,
    Reliability,
    SoftwareRecord,
    UsageLabel,
)
from macwise.services.overlap import analyze_overlaps

COLLECTED_AT = datetime(2026, 7, 17, 22, 0, tzinfo=UTC)


def app(
    subject_id: str,
    name: str,
    *,
    identifier: str | None = None,
    install_path: str | None = None,
    digest: str | None = None,
) -> SoftwareRecord:
    evidence = (
        (
            Evidence(
                kind="content_digest",
                value=digest,
                source="synthetic fixture digest",
                collected_at=COLLECTED_AT,
                reliability=Reliability.HIGH,
            ),
        )
        if digest is not None
        else ()
    )
    return SoftwareRecord(
        id=subject_id,
        entity_type=EntityType.APPLICATION,
        name=name,
        display_name=name,
        identifier=identifier,
        install_path=install_path,
        evidence=evidence,
    )


def formula(
    subject_id: str,
    name: str,
    *,
    executables: tuple[str, ...] = (),
) -> SoftwareRecord:
    return SoftwareRecord(
        id=subject_id,
        entity_type=EntityType.HOMEBREW_FORMULA,
        name=name,
        display_name=name,
        executables=executables,
    )


def usage(subject_id: str, label: UsageLabel) -> Finding:
    basis = (
        ClaimBasis.VERIFIED
        if label in {UsageLabel.ACTIVELY_USED, UsageLabel.RECENTLY_USED}
        else ClaimBasis.INFERRED
    )
    if label is UsageLabel.NO_RELIABLE_EVIDENCE:
        basis = ClaimBasis.UNKNOWN
    if label is UsageLabel.USER_CONFIRMED_UNUSED:
        basis = ClaimBasis.USER_CONFIRMED
    return Finding(
        subject_id=subject_id,
        topic=FindingTopic.USAGE,
        statement=f"Synthetic {label.value} evidence.",
        basis=basis,
        confidence=Reliability.MEDIUM,
        usage_label=label,
    )


def test_explicit_catalog_pairs_cover_every_non_identity_category() -> None:
    records = (
        app("app:docker-desktop", "Docker Desktop", identifier="com.docker.docker"),
        formula("formula:docker", "docker"),
        formula("formula:podman", "podman"),
        app("app:raycast", "Raycast", identifier="com.raycast.macos"),
        app("app:alttab", "AltTab", identifier="com.lwouis.alt-tab-macos"),
        app("app:obsidian", "Obsidian", identifier="md.obsidian"),
        app("app:qlmarkdown", "QLMarkdown"),
        app("app:lm-studio", "LM Studio", identifier="ai.elementlabs.lmstudio"),
        formula("formula:llama", "llama.cpp"),
        formula("formula:mlx", "mlx"),
        app("app:omlx", "oMLX"),
        formula("formula:python-old", "python@3.11"),
        formula("formula:python", "python@3.13"),
    )

    result = analyze_overlaps(records, usage_findings=())

    assert {relation.category for relation in result.relations} == {
        OverlapCategory.STRONG_SUBSTITUTE,
        OverlapCategory.PARTIAL_OVERLAP,
        OverlapCategory.COMPLEMENTARY_TOOLS,
        OverlapCategory.RUNTIME_AND_FRONTEND,
        OverlapCategory.DEPENDENCY_AND_USER_FACING_APP,
        OverlapCategory.LEGACY_AND_SUCCESSOR,
        OverlapCategory.NOT_ACTUALLY_RELATED,
    }
    assert len(result.assessments) == len(records)
    assert all(item.catalog_version for item in result.assessments)


def test_identity_rules_require_strong_evidence_and_distinct_installations() -> None:
    first = app(
        "app:docker-one",
        "Docker Desktop",
        identifier="com.docker.docker",
        install_path="/Applications/Docker.app",
        digest="same-digest",
    )
    second = app(
        "app:docker-two",
        "Docker Desktop",
        identifier="com.docker.docker",
        install_path="/Volumes/Tools/Docker.app",
        digest="same-digest",
    )

    exact = analyze_overlaps((first, second), usage_findings=())
    same_product = analyze_overlaps(
        (
            first.model_copy(update={"evidence": ()}),
            second.model_copy(update={"evidence": ()}),
        ),
        usage_findings=(),
    )

    assert [item.category for item in exact.relations] == [OverlapCategory.EXACT_DUPLICATE]
    assert exact.relations[0].basis is ClaimBasis.VERIFIED
    assert [item.category for item in same_product.relations] == [
        OverlapCategory.SAME_PRODUCT_INSTALLED_TWICE
    ]
    assert same_product.relations[0].basis is ClaimBasis.INFERRED


def test_fuzzy_or_unknown_identity_produces_no_catalog_conclusion() -> None:
    result = analyze_overlaps(
        (app("app:preview", "Docker Desktop Preview"),),
        usage_findings=(),
    )

    assert result.assessments == ()
    assert result.relations == ()
    assert result.recommendations == ()


def test_ambiguous_catalog_identity_stays_unknown_and_surfaces_public_limitation() -> None:
    result = analyze_overlaps(
        (formula("formula:custom", "custom runtime", executables=("python3",)),),
        usage_findings=(),
    )

    assert result.assessments == ()
    assert result.relations == ()
    assert result.recommendations == ()
    assert result.limitations == (
        "One or more software records matched multiple catalog roles; those roles remain unknown.",
    )
    assert "custom" not in result.limitations[0].casefold()


def test_active_substitute_and_cautious_non_use_yield_review_not_removal() -> None:
    docker = app("app:docker", "Docker Desktop", identifier="com.docker.docker")
    podman = formula("formula:podman", "podman")

    result = analyze_overlaps(
        (docker, podman),
        usage_findings=(
            usage(docker.id, UsageLabel.ACTIVELY_USED),
            usage(podman.id, UsageLabel.POSSIBLY_UNUSED),
        ),
    )

    recommendation = next(
        item
        for item in result.recommendations
        if item.action is RecommendationAction.REVIEW_CONSOLIDATION
    )
    assert set(recommendation.subject_ids) == {docker.id, podman.id}
    assert recommendation.prerequisites
    assert "unique" in " ".join(recommendation.prerequisites).casefold()
    rendered = recommendation.model_dump_json().casefold()
    assert "authorize removal" in rendered
    assert "safe to remove" not in rendered


def test_complements_stay_together_and_unknown_high_value_item_can_be_learned() -> None:
    obsidian = app("app:obsidian", "Obsidian", identifier="md.obsidian")
    qlmarkdown = app("app:qlmarkdown", "QLMarkdown")
    pyenv = formula("formula:pyenv", "pyenv")

    result = analyze_overlaps(
        (obsidian, qlmarkdown, pyenv),
        usage_findings=(
            usage(obsidian.id, UsageLabel.RECENTLY_USED),
            usage(qlmarkdown.id, UsageLabel.CONFIGURED_BUT_IDLE),
            usage(pyenv.id, UsageLabel.NO_RELIABLE_EVIDENCE),
        ),
    )

    actions = {item.action for item in result.recommendations}
    assert RecommendationAction.KEEP_TOGETHER in actions
    learned = next(
        item
        for item in result.recommendations
        if item.action is RecommendationAction.LEARN and item.subject_ids == (pyenv.id,)
    )
    assert learned.learning_value.value == "high"
    assert all("never used" not in item.statement.casefold() for item in result.recommendations)


def test_neutral_pair_guidance_does_not_hide_non_conflicting_learning_value() -> None:
    docker = app("app:docker", "Docker Desktop", identifier="com.docker.docker")
    podman = formula("formula:podman", "podman")

    result = analyze_overlaps(
        (docker, podman),
        usage_findings=(
            usage(docker.id, UsageLabel.NO_RELIABLE_EVIDENCE),
            usage(podman.id, UsageLabel.NO_RELIABLE_EVIDENCE),
        ),
    )

    assert any(
        item.action is RecommendationAction.NO_RECOMMENDATION
        and set(item.subject_ids) == {docker.id, podman.id}
        for item in result.recommendations
    )
    learned_subjects = {
        item.subject_ids[0]
        for item in result.recommendations
        if item.action is RecommendationAction.LEARN and len(item.subject_ids) == 1
    }
    assert {docker.id, podman.id} <= learned_subjects
