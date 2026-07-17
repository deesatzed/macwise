from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

import macwise.cli as cli
from macwise.models import (
    AuditDocument,
    BackupStatus,
    ClaimBasis,
    EntityType,
    Finding,
    FindingTopic,
    PathEvidence,
    Reliability,
    SoftwareRecord,
    StartupKind,
    StartupRecord,
    StorageLocation,
    UsageLabel,
    stable_software_id,
)

RUNNER = CliRunner()
COLLECTED_AT = datetime(2026, 7, 17, 17, 0, tzinfo=UTC)


class StaticAuditService:
    def __init__(self, audit: AuditDocument) -> None:
        self.audit = audit

    def run(self, application_roots: tuple[Path, ...]) -> AuditDocument:
        assert application_roots
        return self.audit


def phase_two_audit(base: AuditDocument) -> AuditDocument:
    application, dependency = base.software
    confirmed = SoftwareRecord(
        id=stable_software_id(EntityType.APPLICATION, "org.example.old"),
        entity_type=EntityType.APPLICATION,
        name="Old Utility",
        display_name="Old Utility",
        install_path="/Applications/Old Utility.app",
    )
    return base.model_copy(
        update={
            "software": (*base.software, confirmed),
            "findings": (
                Finding(
                    subject_id=application.id,
                    topic=FindingTopic.USAGE,
                    statement="Only a stale positive last-used timestamp was found.",
                    basis=ClaimBasis.INFERRED,
                    confidence=Reliability.LOW,
                    usage_label=UsageLabel.POSSIBLY_UNUSED,
                    evidence_kinds=("spotlight_last_used",),
                    limitations=("Stale metadata does not prove non-use.",),
                ),
                Finding(
                    subject_id=dependency.id,
                    topic=FindingTopic.USAGE,
                    statement="Another installed package requires this formula.",
                    basis=ClaimBasis.VERIFIED,
                    confidence=Reliability.HIGH,
                    usage_label=UsageLabel.INDIRECTLY_REQUIRED,
                    evidence_kinds=("reverse_dependency",),
                ),
                Finding(
                    subject_id=confirmed.id,
                    topic=FindingTopic.USAGE,
                    statement="The user marked this item unused.",
                    basis=ClaimBasis.USER_CONFIRMED,
                    confidence=Reliability.HIGH,
                    usage_label=UsageLabel.USER_CONFIRMED_UNUSED,
                    evidence_kinds=("user_confirmation",),
                ),
            ),
            "startup": (
                StartupRecord(
                    id="startup:example",
                    label="org.example.safe.agent",
                    kind=StartupKind.LAUNCH_AGENT,
                    source_path="/Users/example/Library/LaunchAgents/org.example.safe.agent.plist",
                    owner_software_ids=(application.id,),
                    enabled=None,
                    running=True,
                ),
                StartupRecord(
                    id="startup:orphan",
                    label="org.example.orphan",
                    kind=StartupKind.LAUNCH_DAEMON,
                    owner_software_ids=(),
                    enabled=None,
                    running=None,
                ),
            ),
            "path_evidence": (
                PathEvidence(
                    id="path:example-support",
                    subject_id=application.id,
                    path="/Users/example/Library/Application Support/Example",
                    kind="application_support",
                    size_bytes=8192,
                    storage_location=StorageLocation.INTERNAL,
                    last_modified_at=datetime(2025, 1, 2, 12, 0, tzinfo=UTC),
                    backup_excluded=False,
                ),
            ),
            "backup": BackupStatus(
                configured=True,
                available_destination_volume_ids=(base.volumes[0].id,),
                last_backup_at=datetime(2026, 7, 16, 23, 15, tzinfo=UTC),
                limitations=("A timestamp does not prove path-level recoverability.",),
            ),
        }
    )


@pytest.fixture
def phase_two_cli(
    sample_audit: AuditDocument,
    monkeypatch: pytest.MonkeyPatch,
) -> AuditDocument:
    audit = phase_two_audit(sample_audit)
    monkeypatch.setattr(cli, "_service_factory", lambda: StaticAuditService(audit))
    return audit


def test_explain_separates_basis_and_links_usage_startup_data_and_backup(
    phase_two_cli: AuditDocument,
) -> None:
    result = RUNNER.invoke(cli.app, ["explain", "app:Example"])

    assert result.exit_code == 0, result.stdout
    assert "Verified facts" in result.stdout
    assert "Inferred findings" in result.stdout
    assert "User-confirmed findings" in result.stdout
    assert "Unknowns and limitations" in result.stdout
    assert "Usage: possibly unused" in result.stdout
    assert "Only a stale positive last-used timestamp was found." in result.stdout
    assert "Launch agent: org.example.safe.agent" in result.stdout
    assert "Running: yes" in result.stdout
    assert "Enabled: unknown" in result.stdout
    assert "8.0 KiB on internal storage" in result.stdout
    assert "not excluded from Time Machine" in result.stdout
    assert "Backup coverage: Not verified." in result.stdout
    assert "Recommendation: Not available" in result.stdout
    assert "never used" not in result.stdout.casefold()


def test_explain_requires_qualification_for_an_exact_cross_type_collision(
    phase_two_cli: AuditDocument,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    application = phase_two_cli.software[0]
    cask = SoftwareRecord(
        id=stable_software_id(EntityType.HOMEBREW_CASK, "example"),
        entity_type=EntityType.HOMEBREW_CASK,
        name="Example",
        display_name="Example App",
    )
    ambiguous = phase_two_cli.model_copy(update={"software": (*phase_two_cli.software, cask)})
    monkeypatch.setattr(cli, "_service_factory", lambda: StaticAuditService(ambiguous))

    result = RUNNER.invoke(cli.app, ["explain", "Example"])
    qualified = RUNNER.invoke(cli.app, ["explain", "app:Example"])

    assert result.exit_code == 2
    assert "more than one possible match" in result.stdout
    assert "app:NAME, cask:NAME, or formula:NAME" in result.stdout
    assert qualified.exit_code == 0
    assert application.display_name in qualified.stdout


def test_review_unused_lists_only_supported_cautious_labels(
    phase_two_cli: AuditDocument,
) -> None:
    result = RUNNER.invoke(cli.app, ["review", "unused"])

    assert result.exit_code == 0, result.stdout
    assert "Example App" in result.stdout
    assert "possibly unused" in result.stdout
    assert "Old Utility" in result.stdout
    assert "user confirmed unused" in result.stdout
    assert "openssl@3" not in result.stdout
    assert "Missing evidence alone never qualifies an item" in result.stdout
    assert "never used" not in result.stdout.casefold()


def test_startup_lists_owner_and_tri_state_without_claiming_enabled(
    phase_two_cli: AuditDocument,
) -> None:
    result = RUNNER.invoke(cli.app, ["startup"])

    assert result.exit_code == 0, result.stdout
    assert "org.example.safe.agent" in result.stdout
    assert "Owner: Example App" in result.stdout
    assert "Enabled: unknown" in result.stdout
    assert "Running: yes" in result.stdout
    assert "org.example.orphan" in result.stdout
    assert "Owner: unknown" in result.stdout


def test_backups_reports_facts_and_explicitly_refuses_coverage(
    phase_two_cli: AuditDocument,
) -> None:
    result = RUNNER.invoke(cli.app, ["backups"])

    assert result.exit_code == 0, result.stdout
    assert "Configured: yes" in result.stdout
    assert "Available destination: System" in result.stdout
    assert "2026-07-16T23:15:00+00:00" in result.stdout
    assert "not excluded" in result.stdout
    assert "does not prove coverage" in result.stdout
    assert "A timestamp does not prove path-level recoverability." in result.stdout
    assert "Backup coverage: Not verified." in result.stdout
    assert "No changes were made" not in result.stdout
