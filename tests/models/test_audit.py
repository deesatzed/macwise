from datetime import UTC, datetime

from macwise.models import (
    AuditDocument,
    CollectorState,
    CollectorStatus,
    EntityType,
    Evidence,
    Reliability,
    SoftwareRecord,
    StorageLocation,
    VolumeRecord,
    stable_software_id,
)

COLLECTED_AT = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


def test_stable_software_ids_are_deterministic_and_type_scoped() -> None:
    first = stable_software_id(EntityType.APPLICATION, "org.example.SafeApp")
    second = stable_software_id(EntityType.APPLICATION, "org.example.SafeApp")
    formula = stable_software_id(EntityType.HOMEBREW_FORMULA, "org.example.SafeApp")

    assert first == second
    assert first != formula
    assert first.startswith("application:")


def test_versioned_audit_round_trips_without_losing_provenance() -> None:
    software = SoftwareRecord(
        id=stable_software_id(EntityType.APPLICATION, "org.example.SafeApp"),
        entity_type=EntityType.APPLICATION,
        name="SafeApp",
        display_name="Safe App",
        version="1.2.3",
        install_path="/Applications/Safe App.app",
        evidence=(
            Evidence(
                kind="bundle_metadata",
                value={"bundle_id": "org.example.SafeApp"},
                source="Info.plist",
                collected_at=COLLECTED_AT,
                reliability=Reliability.HIGH,
            ),
        ),
    )
    volume = VolumeRecord(
        id="volume:internal",
        name="Macintosh HD",
        device_identifier="disk1s1",
        mount_point="/",
        location=StorageLocation.INTERNAL,
        capacity_bytes=1_000_000,
        free_bytes=400_000,
    )
    status = CollectorStatus(
        collector="applications",
        state=CollectorState.COMPLETE,
        collected_at=COLLECTED_AT,
        records_count=1,
    )
    audit = AuditDocument(
        audit_id="audit:test",
        collected_at=COLLECTED_AT,
        software=(software,),
        volumes=(volume,),
        collectors=(status,),
    )

    restored = AuditDocument.model_validate_json(audit.model_dump_json())

    assert audit.schema_version == 2
    assert restored == audit
    assert restored.software[0].evidence[0].source == "Info.plist"


def test_expanded_inventory_fields_preserve_unknowns_and_typed_evidence() -> None:
    software = SoftwareRecord(
        id=stable_software_id(EntityType.APPLICATION, "org.example.SafeApp"),
        entity_type=EntityType.APPLICATION,
        name="SafeApp",
        display_name="Safe App",
        publisher="Example Developer ID",
        signing_identity="Developer ID Application: Example (TEAM123456)",
        team_identifier="TEAM123456",
        architectures=("arm64", "x86_64"),
        running=True,
        components=("Contents/PlugIns/Share.appex",),
        executables=("safe-tool",),
        linked=True,
        pinned=False,
        caveats="Synthetic caveat.",
        project_references=("sample/pyproject.toml",),
        related_software_ids=("homebrew_cask:related",),
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
        ownership_enabled=True,
        time_machine_role="Backup",
        time_machine_destination=True,
        time_machine_excluded=False,
    )

    assert software.architectures == ("arm64", "x86_64")
    assert software.running is True
    assert software.project_references == ("sample/pyproject.toml",)
    assert volume.parent_device_identifier == "disk0"
    assert volume.physical_store_identifiers == ("disk0s2",)
    assert volume.time_machine_destination is True

    unknown = SoftwareRecord(
        id=stable_software_id(EntityType.APPLICATION, "org.example.Unknown"),
        entity_type=EntityType.APPLICATION,
        name="Unknown",
        display_name="Unknown",
    )
    assert unknown.publisher is None
    assert unknown.running is None
    assert unknown.architectures == ()
    assert unknown.project_references == ()


def test_partial_collector_records_limitations_without_negative_claims() -> None:
    status = CollectorStatus(
        collector="applications",
        state=CollectorState.PARTIAL,
        collected_at=COLLECTED_AT,
        records_count=0,
        limitations=("The user Applications folder could not be read.",),
    )
    audit = AuditDocument(
        audit_id="audit:partial",
        collected_at=COLLECTED_AT,
        collectors=(status,),
    )

    serialized = audit.model_dump_json()

    assert audit.collectors[0].state is CollectorState.PARTIAL
    assert "could not be read" in serialized
    assert "never used" not in serialized.lower()
