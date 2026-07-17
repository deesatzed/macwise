from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path

from macwise.collectors import ApplicationCollection, HomebrewCollection, StorageCollection
from macwise.models import (
    CollectorState,
    CollectorStatus,
    EntityType,
    SoftwareRecord,
    StorageLocation,
    VolumeRecord,
    stable_software_id,
)
from macwise.services.audit import AuditService

COLLECTED_AT = datetime(2026, 7, 17, 17, 0, tzinfo=UTC)


def status(name: str, state: CollectorState, records: int, *limitations: str) -> CollectorStatus:
    return CollectorStatus(
        collector=name,
        state=state,
        collected_at=COLLECTED_AT,
        records_count=records,
        limitations=limitations,
    )


def test_audit_runs_storage_first_aggregates_partial_results_and_sorts_records() -> None:
    calls: list[str] = []
    external = VolumeRecord(
        id="volume:external",
        name="Archive",
        device_identifier="disk2s1",
        mount_point="/Volumes/Archive",
        location=StorageLocation.EXTERNAL,
    )

    def storage_collector(*, collected_at: datetime) -> StorageCollection:
        assert collected_at == COLLECTED_AT
        calls.append("storage")
        return StorageCollection(
            volumes=(external,),
            status=status("storage", CollectorState.PARTIAL, 1, "One disk was unavailable."),
        )

    def application_collector(
        roots: Sequence[Path],
        *,
        collected_at: datetime,
        storage_resolver: Callable[[Path], StorageLocation],
    ) -> ApplicationCollection:
        assert tuple(roots) == (Path("/Applications"),)
        assert collected_at == COLLECTED_AT
        calls.append("applications")
        assert storage_resolver(Path("/Volumes/Archive/Example.app")) is StorageLocation.EXTERNAL
        record = SoftwareRecord(
            id=stable_software_id(EntityType.APPLICATION, "org.example.app"),
            entity_type=EntityType.APPLICATION,
            name="Zed",
            display_name="Zed",
        )
        return ApplicationCollection(
            software=(record,),
            status=status("applications", CollectorState.COMPLETE, 1),
        )

    def homebrew_collector(*, collected_at: datetime) -> HomebrewCollection:
        assert collected_at == COLLECTED_AT
        calls.append("homebrew")
        record = SoftwareRecord(
            id=stable_software_id(EntityType.HOMEBREW_FORMULA, "alpha"),
            entity_type=EntityType.HOMEBREW_FORMULA,
            name="alpha",
            display_name="alpha",
        )
        return HomebrewCollection(
            software=(record,),
            status=status("homebrew", CollectorState.COMPLETE, 1),
        )

    audit = AuditService(
        application_collector=application_collector,
        homebrew_collector=homebrew_collector,
        storage_collector=storage_collector,
        clock=lambda: COLLECTED_AT,
        audit_id_factory=lambda: "audit:test",
    ).run((Path("/Applications"),))

    assert calls == ["storage", "applications", "homebrew"]
    assert audit.audit_id == "audit:test"
    assert audit.schema_version == 1
    assert [record.entity_type for record in audit.software] == [
        EntityType.APPLICATION,
        EntityType.HOMEBREW_FORMULA,
    ]
    assert [collector.collector for collector in audit.collectors] == [
        "applications",
        "homebrew",
        "storage",
    ]
    assert audit.collectors[-1].state is CollectorState.PARTIAL


def test_unexpected_collector_failure_does_not_discard_other_inventory() -> None:
    def storage_collector(*, collected_at: datetime) -> StorageCollection:
        return StorageCollection(
            volumes=(),
            status=CollectorStatus(
                collector="storage",
                state=CollectorState.COMPLETE,
                collected_at=collected_at,
                records_count=0,
            ),
        )

    def application_collector(
        roots: Sequence[Path],
        *,
        collected_at: datetime,
        storage_resolver: Callable[[Path], StorageLocation],
    ) -> ApplicationCollection:
        del roots, storage_resolver
        return ApplicationCollection(
            software=(),
            status=CollectorStatus(
                collector="applications",
                state=CollectorState.COMPLETE,
                collected_at=collected_at,
                records_count=0,
            ),
        )

    def broken_homebrew(*, collected_at: datetime) -> HomebrewCollection:
        del collected_at
        raise RuntimeError("private implementation detail")

    audit = AuditService(
        application_collector=application_collector,
        homebrew_collector=broken_homebrew,
        storage_collector=storage_collector,
        clock=lambda: COLLECTED_AT,
        audit_id_factory=lambda: "audit:partial",
    ).run(())

    homebrew_status = next(item for item in audit.collectors if item.collector == "homebrew")
    assert homebrew_status.state is CollectorState.UNAVAILABLE
    assert homebrew_status.limitations == ("The Homebrew collector failed unexpectedly.",)
    assert "private implementation detail" not in homebrew_status.model_dump_json()
