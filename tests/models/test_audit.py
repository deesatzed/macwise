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

    assert audit.schema_version == 1
    assert restored == audit
    assert restored.software[0].evidence[0].source == "Info.plist"


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
