from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

import macwise.cli as cli
from macwise.models import (
    AuditDocument,
    ClaimBasis,
    EntityType,
    Finding,
    FindingTopic,
    Reliability,
    SoftwareRecord,
    UsageLabel,
)
from macwise.services.overlap import analyze_overlaps

RUNNER = CliRunner()


class StaticAuditService:
    def __init__(self, audit: AuditDocument) -> None:
        self.audit = audit

    def run(self, application_roots: tuple[Path, ...]) -> AuditDocument:
        assert application_roots
        return self.audit


def usage(subject_id: str, label: UsageLabel, basis: ClaimBasis) -> Finding:
    return Finding(
        subject_id=subject_id,
        topic=FindingTopic.USAGE,
        statement=f"Synthetic {label.value} evidence.",
        basis=basis,
        confidence=Reliability.MEDIUM,
        usage_label=label,
    )


def phase_three_audit(base: AuditDocument) -> AuditDocument:
    docker = SoftwareRecord(
        id="application:docker",
        entity_type=EntityType.APPLICATION,
        name="Docker",
        display_name="Docker Desktop",
        identifier="com.docker.docker",
    )
    docker_cli = SoftwareRecord(
        id="homebrew_formula:docker",
        entity_type=EntityType.HOMEBREW_FORMULA,
        name="docker",
        display_name="docker",
    )
    podman = SoftwareRecord(
        id="homebrew_formula:podman",
        entity_type=EntityType.HOMEBREW_FORMULA,
        name="podman",
        display_name="Podman",
    )
    obsidian = SoftwareRecord(
        id="application:obsidian",
        entity_type=EntityType.APPLICATION,
        name="Obsidian",
        display_name="Obsidian",
        identifier="md.obsidian",
    )
    qlmarkdown = SoftwareRecord(
        id="application:qlmarkdown",
        entity_type=EntityType.APPLICATION,
        name="QLMarkdown",
        display_name="QLMarkdown",
    )
    unknown = SoftwareRecord(
        id="application:unknown",
        entity_type=EntityType.APPLICATION,
        name="Unknown Tool",
        display_name="Unknown Tool",
    )
    software = (docker, docker_cli, podman, obsidian, qlmarkdown, unknown)
    findings = (
        usage(docker.id, UsageLabel.ACTIVELY_USED, ClaimBasis.VERIFIED),
        usage(docker_cli.id, UsageLabel.INDIRECTLY_REQUIRED, ClaimBasis.INFERRED),
        usage(podman.id, UsageLabel.POSSIBLY_UNUSED, ClaimBasis.INFERRED),
        usage(obsidian.id, UsageLabel.RECENTLY_USED, ClaimBasis.VERIFIED),
        usage(qlmarkdown.id, UsageLabel.CONFIGURED_BUT_IDLE, ClaimBasis.INFERRED),
        usage(unknown.id, UsageLabel.NO_RELIABLE_EVIDENCE, ClaimBasis.UNKNOWN),
    )
    overlap = analyze_overlaps(software, usage_findings=findings)
    return base.model_copy(
        update={
            "software": software,
            "findings": findings,
            "catalog_assessments": overlap.assessments,
            "overlaps": overlap.relations,
            "recommendations": overlap.recommendations,
            "collected_at": datetime(2026, 7, 17, 23, 0, tzinfo=UTC),
        }
    )


@pytest.fixture
def phase_three_cli(
    sample_audit: AuditDocument,
    monkeypatch: pytest.MonkeyPatch,
) -> AuditDocument:
    audit = phase_three_audit(sample_audit)
    monkeypatch.setattr(cli, "_service_factory", lambda: StaticAuditService(audit))
    return audit


def test_compare_shows_role_category_actual_use_unique_value_and_guarded_guidance(
    phase_three_cli: AuditDocument,
) -> None:
    result = RUNNER.invoke(
        cli.app,
        ["compare", "app:Docker", "formula:podman"],
    )

    assert result.exit_code == 0, result.stdout
    assert "Docker Desktop" in result.stdout
    assert "Podman" in result.stdout
    assert "strong substitute" in result.stdout
    assert "Shared capabilities: containers, images" in result.stdout
    assert "Integrated desktop controls" in result.stdout
    assert "Daemonless container workflow" in result.stdout
    assert "Usage: actively used (verified" in result.stdout
    assert "Usage: possibly unused (inferred" in result.stdout
    assert (
        "Actual-use comparison: Docker Desktop has stronger observed use evidence than Podman."
        in result.stdout
    )
    assert "Learning value:" in result.stdout
    assert "Review consolidation" in result.stdout
    assert "does not authorize removal" in result.stdout
    assert "safe to remove" not in result.stdout.casefold()
    assert "never used" not in result.stdout.casefold()


def test_compare_actual_use_result_is_independent_of_argument_order(
    phase_three_cli: AuditDocument,
) -> None:
    result = RUNNER.invoke(
        cli.app,
        ["compare", "formula:podman", "app:Docker"],
    )

    assert result.exit_code == 0, result.stdout
    assert (
        "Actual-use comparison: Docker Desktop has stronger observed use evidence than Podman."
        in result.stdout
    )


def test_compare_actual_use_calls_ties_and_missing_evidence_unresolved(
    phase_three_cli: AuditDocument,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tied_findings = tuple(
        finding.model_copy(
            update={
                "usage_label": UsageLabel.RECENTLY_USED,
                "basis": ClaimBasis.VERIFIED,
            }
        )
        if finding.subject_id in {"application:docker", "homebrew_formula:podman"}
        else finding
        for finding in phase_three_cli.findings
    )
    tied = phase_three_cli.model_copy(update={"findings": tied_findings})
    monkeypatch.setattr(cli, "_service_factory", lambda: StaticAuditService(tied))
    tie_result = RUNNER.invoke(cli.app, ["compare", "app:Docker", "formula:podman"])

    missing = phase_three_cli.model_copy(
        update={
            "findings": tuple(
                finding
                for finding in phase_three_cli.findings
                if finding.subject_id != "homebrew_formula:podman"
            )
        }
    )
    monkeypatch.setattr(cli, "_service_factory", lambda: StaticAuditService(missing))
    missing_result = RUNNER.invoke(cli.app, ["compare", "app:Docker", "formula:podman"])

    assert tie_result.exit_code == 0, tie_result.stdout
    assert (
        "Actual-use comparison: unresolved; the strongest observed-use evidence is tied."
        in tie_result.stdout
    )
    assert missing_result.exit_code == 0, missing_result.stdout
    assert (
        "Actual-use comparison: unresolved because usage evidence is missing."
        in missing_result.stdout
    )


def test_compare_requires_two_distinct_unambiguous_installed_items(
    phase_three_cli: AuditDocument,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    too_few = RUNNER.invoke(cli.app, ["compare", "app:Docker"])
    same = RUNNER.invoke(cli.app, ["compare", "app:Docker", "app:Docker"])

    cask = SoftwareRecord(
        id="homebrew_cask:docker",
        entity_type=EntityType.HOMEBREW_CASK,
        name="Docker",
        display_name="Docker Desktop",
    )
    ambiguous = phase_three_cli.model_copy(update={"software": (*phase_three_cli.software, cask)})
    monkeypatch.setattr(cli, "_service_factory", lambda: StaticAuditService(ambiguous))
    collision = RUNNER.invoke(cli.app, ["compare", "Docker", "formula:podman"])

    assert too_few.exit_code == 2
    assert "at least two" in too_few.stdout
    assert same.exit_code == 2
    assert "distinct installed items" in same.stdout
    assert collision.exit_code == 2
    assert "more than one possible match" in collision.stdout


def test_compare_keeps_unknown_relationship_unknown(
    phase_three_cli: AuditDocument,
) -> None:
    result = RUNNER.invoke(
        cli.app,
        ["compare", "app:Docker", "app:Unknown Tool"],
    )

    assert result.exit_code == 0, result.stdout
    assert "Relationship unknown" in result.stdout
    assert "MacWise will not infer a category from names alone" in result.stdout


def test_review_duplicates_groups_overlap_without_calling_every_pair_duplicate(
    phase_three_cli: AuditDocument,
) -> None:
    result = RUNNER.invoke(cli.app, ["review", "duplicates"])

    assert result.exit_code == 0, result.stdout
    assert "Overlap candidates — not all are duplicates" in result.stdout
    assert "Strong substitute" in result.stdout
    assert "Complementary tools" in result.stdout
    assert "Docker Desktop" in result.stdout
    assert "Podman" in result.stdout
    assert "Obsidian" in result.stdout
    assert "QLMarkdown" in result.stdout
    assert "Not actually related" not in result.stdout
    assert "Role-aware overlap analysis is not available" not in result.stdout


def test_overlap_is_a_discoverable_alias_for_duplicate_review(
    phase_three_cli: AuditDocument,
) -> None:
    alias = RUNNER.invoke(cli.app, ["overlap"])
    nested = RUNNER.invoke(cli.app, ["review", "duplicates"])
    root_help = RUNNER.invoke(cli.app, ["--help"])

    assert alias.exit_code == 0, alias.stdout
    assert alias.stdout == nested.stdout
    assert "overlap" in root_help.stdout


def test_explain_adds_catalog_roles_learning_value_and_related_overlap(
    phase_three_cli: AuditDocument,
) -> None:
    result = RUNNER.invoke(cli.app, ["explain", "app:Docker"])

    assert result.exit_code == 0, result.stdout
    assert "Catalog roles: container desktop, container runtime bundle" in result.stdout
    assert "Unique capabilities: integrated desktop controls" in result.stdout
    assert "Learning value: moderate" in result.stdout
    assert "Related overlap: Podman — strong substitute" in result.stdout
    assert "Guarded guidance: review consolidation" in result.stdout
    assert "does not authorize removal" in result.stdout
