import json
from datetime import UTC, datetime

import pytest

from macwise.models import (
    AuditDocument,
    BackupStatus,
    ClaimBasis,
    CollectorState,
    CollectorStatus,
    EntityType,
    Finding,
    FindingTopic,
    InstallRole,
    PathEvidence,
    Reliability,
    SoftwareRecord,
    StartupKind,
    StartupRecord,
    StorageLocation,
    UsageLabel,
    VolumeRecord,
    stable_software_id,
)
from macwise.reporting import parse_json, render_json, render_markdown

COLLECTED_AT = datetime(2026, 7, 17, 17, 0, tzinfo=UTC)


def sample_audit() -> AuditDocument:
    app = SoftwareRecord(
        id=stable_software_id(EntityType.APPLICATION, "org.example.safe"),
        entity_type=EntityType.APPLICATION,
        name="Example",
        display_name="Example App",
        version="2.4.1",
        install_path="/Applications/Example.app",
        install_source="homebrew_cask:example-app",
        publisher="Example Corp",
        signing_identity="Developer ID Application: Example Corp (TEAM123456)",
        team_identifier="TEAM123456",
        size_bytes=2048,
        architectures=("arm64", "x86_64"),
        running=True,
        components=("Contents/PlugIns/Share.appex",),
        storage_location=StorageLocation.INTERNAL,
    )
    dependency = SoftwareRecord(
        id=stable_software_id(EntityType.HOMEBREW_FORMULA, "openssl@3"),
        entity_type=EntityType.HOMEBREW_FORMULA,
        name="openssl@3",
        display_name="openssl@3",
        version="3.3.1",
        install_path="/opt/homebrew/Cellar/openssl@3",
        size_bytes=4096,
        executables=("openssl",),
        install_role=InstallRole.DEPENDENCY,
        reverse_dependencies=("postgresql@16",),
        linked=False,
        pinned=True,
        caveats="Synthetic caveat.",
        project_references=("Brewfile",),
    )
    volume = VolumeRecord(
        id="volume:internal",
        name="System",
        device_identifier="disk1s1",
        parent_device_identifier="disk0",
        whole_disk=False,
        content="Apple_APFS",
        apfs_container_identifier="disk1",
        physical_store_identifiers=("disk0s2",),
        mount_point="/",
        location=StorageLocation.INTERNAL,
        capacity_bytes=1_000_000,
        free_bytes=400_000,
        ownership_enabled=True,
        time_machine_role="Backup",
        time_machine_destination=True,
        time_machine_excluded=False,
    )
    return AuditDocument(
        audit_id="audit:report",
        collected_at=COLLECTED_AT,
        software=(app, dependency),
        volumes=(volume,),
        collectors=(
            CollectorStatus(
                collector="applications",
                state=CollectorState.PARTIAL,
                collected_at=COLLECTED_AT,
                records_count=1,
                limitations=("One configured application folder was unavailable.",),
            ),
            CollectorStatus(
                collector="homebrew",
                state=CollectorState.COMPLETE,
                collected_at=COLLECTED_AT,
                records_count=1,
            ),
        ),
    )


def test_json_report_is_deterministic_versioned_and_round_trips() -> None:
    audit = sample_audit()

    first = render_json(audit)
    second = render_json(audit)
    restored = AuditDocument.model_validate_json(first)

    assert first == second
    assert first.endswith("\n")
    assert '"schema_version": 4' in first
    assert restored == audit


@pytest.mark.parametrize("legacy_version", (1, 2, 3))
def test_older_json_is_migrated_and_future_versions_are_rejected(
    legacy_version: int,
) -> None:
    legacy = sample_audit().model_dump(mode="json")
    legacy["schema_version"] = legacy_version
    for record in legacy["software"]:
        for field in (
            "publisher",
            "signing_identity",
            "team_identifier",
            "architectures",
            "running",
            "components",
            "executables",
            "linked",
            "pinned",
            "caveats",
            "project_references",
            "related_software_ids",
        ):
            record.pop(field, None)
    for volume in legacy["volumes"]:
        for field in (
            "parent_device_identifier",
            "whole_disk",
            "content",
            "apfs_container_identifier",
            "physical_store_identifiers",
            "ownership_enabled",
            "time_machine_role",
            "time_machine_destination",
            "time_machine_excluded",
        ):
            volume.pop(field, None)

    migrated = parse_json(json.dumps(legacy))

    assert migrated.schema_version == 4
    assert migrated.software[0].publisher is None
    assert migrated.software[0].architectures == ()
    assert migrated.volumes[0].parent_device_identifier is None

    legacy["schema_version"] = 5
    with pytest.raises(ValueError, match="Unsupported audit schema version 5"):
        parse_json(json.dumps(legacy))


def test_markdown_separates_verified_inventory_limitations_and_unknowns() -> None:
    report = render_markdown(sample_audit())

    assert report.startswith("# MacWise Audit\n")
    assert "## Verified inventory" in report
    assert "### Applications" in report
    assert "**Example App**" in report
    assert "2.0 KiB on internal storage" in report
    assert "Publisher: Example Corp" in report
    assert r"Architectures: arm64, x86\_64" in report
    assert "Running at collection time: yes" in report
    assert r"Install source: homebrew\_cask:example-app" in report
    assert "Components: Contents/PlugIns/Share.appex" in report
    assert "### Homebrew software" in report
    assert "**openssl@3** — dependency" in report
    assert "Required by: postgresql@16" in report
    assert "Executables: openssl" in report
    assert "Linked: no; pinned: yes" in report
    assert "Project references: Brewfile" in report
    assert "Caveats: Synthetic caveat." in report
    assert "### Storage" in report
    assert "Parent disk: disk0; APFS container: disk1" in report
    assert "Physical stores: disk0s2" in report
    assert "Ownership enabled: yes" in report
    assert "Time Machine role: Backup" in report
    assert "Configured Time Machine destination: yes" in report
    assert "Excluded from Time Machine: no" in report
    assert "## Collection limitations" in report
    assert "One configured application folder was unavailable." in report
    assert "## Unknown in this phase" in report
    assert "Direct and recent usage evidence has not been collected." in report
    assert "Backup coverage has not been verified." in report
    assert "never used" not in report.lower()
    assert report.endswith("This report is read-only. MacWise did not change this Mac.\n")


def test_markdown_output_is_stable_for_the_same_audit() -> None:
    assert render_markdown(sample_audit()) == render_markdown(sample_audit())


def test_markdown_renders_phase_two_facts_by_basis_without_backup_coverage_claim() -> None:
    audit = sample_audit()
    application = audit.software[0]
    phase_two = audit.model_copy(
        update={
            "findings": (
                Finding(
                    subject_id=application.id,
                    topic=FindingTopic.USAGE,
                    statement="Only stale positive usage metadata was found.",
                    basis=ClaimBasis.INFERRED,
                    confidence=Reliability.LOW,
                    usage_label=UsageLabel.POSSIBLY_UNUSED,
                    evidence_kinds=("spotlight_last_used",),
                    limitations=("Stale metadata does not prove non-use.",),
                ),
            ),
            "startup": (
                StartupRecord(
                    id="startup:example",
                    label="org.example.agent",
                    kind=StartupKind.LAUNCH_AGENT,
                    owner_software_ids=(application.id,),
                    enabled=None,
                    running=True,
                ),
            ),
            "path_evidence": (
                PathEvidence(
                    id="path:example",
                    subject_id=application.id,
                    path="/Users/example/Library/Application Support/Example",
                    kind="application_support",
                    size_bytes=8192,
                    storage_location=StorageLocation.INTERNAL,
                    backup_excluded=False,
                ),
            ),
            "backup": BackupStatus(
                configured=True,
                available_destination_volume_ids=(audit.volumes[0].id,),
                last_backup_at=datetime(2026, 7, 16, 23, 15, tzinfo=UTC),
                limitations=("A timestamp does not prove path-level recoverability.",),
            ),
        }
    )

    report = render_markdown(phase_two)

    assert "## Evidence-linked findings" in report
    assert "### Inferred" in report
    assert "Usage: possibly unused" in report
    assert "Only stale positive usage metadata was found." in report
    assert "## Startup and background items" in report
    assert "Owner: Example App" in report
    assert "Enabled: unknown; running: yes" in report
    assert "## Related data measurements" in report
    assert "8.0 KiB on internal storage" in report
    assert "not excluded from Time Machine" in report
    assert "## Backup facts" in report
    assert "Configured: yes" in report
    assert "Last verifiable backup: 2026-07-16T23:15:00+00:00" in report
    assert "A timestamp does not prove path-level recoverability." in report
    assert "Backup coverage is not verified." in report
    assert "never used" not in report.casefold()
