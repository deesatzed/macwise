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


@pytest.fixture
def sample_audit() -> AuditDocument:
    collected_at = datetime(2026, 7, 17, 17, 0, tzinfo=UTC)
    return AuditDocument(
        audit_id="audit:cli-test",
        collected_at=collected_at,
        software=(
            SoftwareRecord(
                id=stable_software_id(EntityType.APPLICATION, "org.example.safe"),
                entity_type=EntityType.APPLICATION,
                name="Example",
                display_name="Example App",
                version="2.4.1",
                install_path="/Applications/Example.app",
                size_bytes=2048,
                storage_location=StorageLocation.INTERNAL,
            ),
            SoftwareRecord(
                id=stable_software_id(EntityType.HOMEBREW_FORMULA, "openssl@3"),
                entity_type=EntityType.HOMEBREW_FORMULA,
                name="openssl@3",
                display_name="openssl@3",
                install_role=InstallRole.DEPENDENCY,
            ),
        ),
        volumes=(
            VolumeRecord(
                id="volume:internal",
                name="System",
                device_identifier="disk1s1",
                mount_point="/",
                location=StorageLocation.INTERNAL,
                capacity_bytes=1_000_000,
                free_bytes=400_000,
            ),
        ),
        collectors=(
            CollectorStatus(
                collector="applications",
                state=CollectorState.COMPLETE,
                collected_at=collected_at,
                records_count=1,
            ),
            CollectorStatus(
                collector="homebrew",
                state=CollectorState.COMPLETE,
                collected_at=collected_at,
                records_count=1,
            ),
            CollectorStatus(
                collector="storage",
                state=CollectorState.COMPLETE,
                collected_at=collected_at,
                records_count=1,
            ),
        ),
    )
