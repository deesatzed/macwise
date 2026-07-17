import json
from datetime import UTC, datetime

import pytest

from macwise.models import (
    AuditDocument,
    CollectorState,
    CollectorStatus,
    EntityType,
    InstallRole,
    SoftwareRecord,
    StorageLocation,
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
        size_bytes=2048,
        storage_location=StorageLocation.INTERNAL,
    )
    dependency = SoftwareRecord(
        id=stable_software_id(EntityType.HOMEBREW_FORMULA, "openssl@3"),
        entity_type=EntityType.HOMEBREW_FORMULA,
        name="openssl@3",
        display_name="openssl@3",
        version="3.3.1",
        install_role=InstallRole.DEPENDENCY,
        reverse_dependencies=("postgresql@16",),
    )
    volume = VolumeRecord(
        id="volume:internal",
        name="System",
        device_identifier="disk1s1",
        mount_point="/",
        location=StorageLocation.INTERNAL,
        capacity_bytes=1_000_000,
        free_bytes=400_000,
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
    assert '"schema_version": 2' in first
    assert restored == audit


def test_schema_one_json_is_migrated_and_future_versions_are_rejected() -> None:
    legacy = sample_audit().model_dump(mode="json")
    legacy["schema_version"] = 1
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

    assert migrated.schema_version == 2
    assert migrated.software[0].publisher is None
    assert migrated.software[0].architectures == ()
    assert migrated.volumes[0].parent_device_identifier is None

    legacy["schema_version"] = 3
    with pytest.raises(ValueError, match="Unsupported audit schema version 3"):
        parse_json(json.dumps(legacy))


def test_markdown_separates_verified_inventory_limitations_and_unknowns() -> None:
    report = render_markdown(sample_audit())

    assert report.startswith("# MacWise Audit\n")
    assert "## Verified inventory" in report
    assert "### Applications" in report
    assert "**Example App**" in report
    assert "2.0 KiB on internal storage" in report
    assert "### Homebrew software" in report
    assert "**openssl@3** — dependency" in report
    assert "Required by: postgresql@16" in report
    assert "### Storage" in report
    assert "## Collection limitations" in report
    assert "One configured application folder was unavailable." in report
    assert "## Unknown in this phase" in report
    assert "Direct and recent usage evidence has not been collected." in report
    assert "Backup coverage has not been verified." in report
    assert "never used" not in report.lower()
    assert report.endswith("This report is read-only. MacWise did not change this Mac.\n")


def test_markdown_output_is_stable_for_the_same_audit() -> None:
    assert render_markdown(sample_audit()) == render_markdown(sample_audit())
