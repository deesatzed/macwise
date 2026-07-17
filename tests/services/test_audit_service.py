from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path

from macwise.collectors import (
    ApplicationCollection,
    BackupCollection,
    HomebrewCollection,
    StartupCollection,
    StartupRoot,
    StorageCollection,
    UsageCollection,
    UsageSignal,
)
from macwise.models import (
    AuditDocument,
    BackupStatus,
    CollectorState,
    CollectorStatus,
    EntityType,
    Evidence,
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


def empty_usage_collector(
    software: Sequence[SoftwareRecord],
    *,
    home_library: Path,
    collected_at: datetime,
    storage_resolver: Callable[[Path], StorageLocation],
) -> UsageCollection:
    del software, home_library, storage_resolver
    return UsageCollection(
        signals=(),
        path_evidence=(),
        status=CollectorStatus(
            collector="usage",
            state=CollectorState.COMPLETE,
            collected_at=collected_at,
            records_count=0,
        ),
    )


def empty_startup_collector(
    software: Sequence[SoftwareRecord],
    *,
    roots: Sequence[StartupRoot],
    collected_at: datetime,
) -> StartupCollection:
    del software, roots
    return StartupCollection(
        startup=(),
        status=CollectorStatus(
            collector="startup",
            state=CollectorState.COMPLETE,
            collected_at=collected_at,
            records_count=0,
        ),
    )


def empty_backup_collector(
    *,
    volumes: Sequence[VolumeRecord],
    path_evidence: Sequence[PathEvidence],
    collected_at: datetime,
) -> BackupCollection:
    del volumes
    return BackupCollection(
        backup=BackupStatus(),
        path_evidence=tuple(path_evidence),
        status=CollectorStatus(
            collector="backups",
            state=CollectorState.COMPLETE,
            collected_at=collected_at,
            records_count=1,
        ),
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

    def homebrew_collector(
        *,
        collected_at: datetime,
        project_roots: Sequence[Path],
    ) -> HomebrewCollection:
        assert collected_at == COLLECTED_AT
        assert tuple(project_roots) == (Path("/Projects/Approved"),)
        calls.append("homebrew")
        record = SoftwareRecord(
            id=stable_software_id(EntityType.HOMEBREW_FORMULA, "alpha"),
            entity_type=EntityType.HOMEBREW_FORMULA,
            name="alpha",
            display_name="alpha",
            install_path="/Volumes/Archive/homebrew/Cellar/alpha",
        )
        return HomebrewCollection(
            software=(record,),
            status=status("homebrew", CollectorState.COMPLETE, 1),
        )

    def usage_collector(
        software: Sequence[SoftwareRecord],
        *,
        home_library: Path,
        collected_at: datetime,
        storage_resolver: Callable[[Path], StorageLocation],
    ) -> UsageCollection:
        assert collected_at == COLLECTED_AT
        assert home_library == Path("/Users/example/Library")
        assert storage_resolver(Path("/Volumes/Archive/data")) is StorageLocation.EXTERNAL
        calls.append("usage")
        application = next(
            record for record in software if record.entity_type is EntityType.APPLICATION
        )
        return UsageCollection(
            signals=(
                UsageSignal(
                    subject_id=application.id,
                    last_used_at=COLLECTED_AT,
                    evidence=(
                        Evidence(
                            kind="spotlight_last_used",
                            value=COLLECTED_AT.isoformat(),
                            source="synthetic mdls",
                            collected_at=COLLECTED_AT,
                            reliability=Reliability.MEDIUM,
                        ),
                    ),
                ),
            ),
            path_evidence=(),
            status=status("usage", CollectorState.COMPLETE, 1),
        )

    def startup_collector(
        software: Sequence[SoftwareRecord],
        *,
        roots: Sequence[StartupRoot],
        collected_at: datetime,
    ) -> StartupCollection:
        assert collected_at == COLLECTED_AT
        assert tuple(roots) == (StartupRoot(StartupKind.LAUNCH_AGENT, Path("/LaunchAgents")),)
        calls.append("startup")
        formula = next(
            record for record in software if record.entity_type is EntityType.HOMEBREW_FORMULA
        )
        return StartupCollection(
            startup=(
                StartupRecord(
                    id="startup:alpha",
                    label="alpha",
                    kind=StartupKind.HOMEBREW_SERVICE,
                    owner_software_ids=(formula.id,),
                    running=True,
                ),
            ),
            status=status("startup", CollectorState.COMPLETE, 1),
        )

    def backup_collector(
        *,
        volumes: Sequence[VolumeRecord],
        path_evidence: Sequence[PathEvidence],
        collected_at: datetime,
    ) -> BackupCollection:
        assert collected_at == COLLECTED_AT
        assert tuple(volumes) == (external,)
        assert tuple(path_evidence) == ()
        calls.append("backups")
        return BackupCollection(
            backup=BackupStatus(
                configured=True,
                available_destination_volume_ids=(external.id,),
                last_backup_at=COLLECTED_AT,
            ),
            path_evidence=(),
            status=status("backups", CollectorState.COMPLETE, 1),
        )

    audit = AuditService(
        application_collector=application_collector,
        backup_collector=backup_collector,
        homebrew_collector=homebrew_collector,
        storage_collector=storage_collector,
        startup_collector=startup_collector,
        usage_collector=usage_collector,
        clock=lambda: COLLECTED_AT,
        audit_id_factory=lambda: "audit:test",
    ).run(
        (Path("/Applications"),),
        project_roots=(Path("/Projects/Approved"),),
        home_library=Path("/Users/example/Library"),
        startup_roots=(StartupRoot(StartupKind.LAUNCH_AGENT, Path("/LaunchAgents")),),
    )

    assert calls == [
        "storage",
        "applications",
        "homebrew",
        "startup",
        "usage",
        "backups",
    ]
    assert audit.audit_id == "audit:test"
    assert audit.schema_version == 3
    assert [record.entity_type for record in audit.software] == [
        EntityType.APPLICATION,
        EntityType.HOMEBREW_FORMULA,
    ]
    formula = next(
        record for record in audit.software if record.entity_type is EntityType.HOMEBREW_FORMULA
    )
    assert formula.storage_location is StorageLocation.EXTERNAL
    assert [collector.collector for collector in audit.collectors] == [
        "applications",
        "backups",
        "homebrew",
        "startup",
        "storage",
        "usage",
    ]
    assert audit.startup[0].owner_software_ids == (formula.id,)
    assert audit.backup is not None and audit.backup.configured is True
    app_record = next(
        record for record in audit.software if record.entity_type is EntityType.APPLICATION
    )
    assert any(item.kind == "spotlight_last_used" for item in app_record.evidence)
    findings = {finding.subject_id: finding for finding in audit.findings}
    assert findings[app_record.id].usage_label is UsageLabel.RECENTLY_USED
    assert findings[formula.id].usage_label is UsageLabel.ACTIVELY_USED
    storage_status = next(item for item in audit.collectors if item.collector == "storage")
    assert storage_status.state is CollectorState.PARTIAL


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

    def broken_homebrew(
        *,
        collected_at: datetime,
        project_roots: Sequence[Path],
    ) -> HomebrewCollection:
        del collected_at, project_roots
        raise RuntimeError("private implementation detail")

    audit = AuditService(
        application_collector=application_collector,
        backup_collector=empty_backup_collector,
        homebrew_collector=broken_homebrew,
        storage_collector=storage_collector,
        startup_collector=empty_startup_collector,
        usage_collector=empty_usage_collector,
        clock=lambda: COLLECTED_AT,
        audit_id_factory=lambda: "audit:partial",
    ).run(())

    homebrew_status = next(item for item in audit.collectors if item.collector == "homebrew")
    assert homebrew_status.state is CollectorState.UNAVAILABLE
    assert homebrew_status.limitations == ("The Homebrew collector failed unexpectedly.",)
    assert "private implementation detail" not in homebrew_status.model_dump_json()


def test_unique_cask_artifact_and_version_link_the_same_application() -> None:
    application = SoftwareRecord(
        id=stable_software_id(EntityType.APPLICATION, "org.example.app"),
        entity_type=EntityType.APPLICATION,
        name="Example",
        display_name="Example",
        version="2.4.1",
        install_path="/Applications/Example.app",
    )
    cask = SoftwareRecord(
        id=stable_software_id(EntityType.HOMEBREW_CASK, "example-app"),
        entity_type=EntityType.HOMEBREW_CASK,
        name="example-app",
        display_name="Example",
        version="2.4.1",
        install_source="homebrew",
        app_artifacts=("Example.app",),
    )

    audit = _relationship_audit((application,), (cask,))
    records = {record.entity_type: record for record in audit.software}
    linked_app = records[EntityType.APPLICATION]
    linked_cask = records[EntityType.HOMEBREW_CASK]

    assert linked_app.install_source == "homebrew_cask:example-app"
    assert linked_app.related_software_ids == (linked_cask.id,)
    assert linked_cask.related_software_ids == (linked_app.id,)
    assert any(item.kind == "homebrew_cask_application_match" for item in linked_app.evidence)


def test_ambiguous_or_independently_sourced_apps_are_not_linked_to_a_cask() -> None:
    first = SoftwareRecord(
        id=stable_software_id(EntityType.APPLICATION, "org.example.first"),
        entity_type=EntityType.APPLICATION,
        name="Example",
        display_name="Example",
        version="2.4.1",
        install_path="/Applications/Example.app",
    )
    duplicate = first.model_copy(
        update={
            "id": stable_software_id(EntityType.APPLICATION, "org.example.duplicate"),
            "install_path": "/Volumes/Tools/Example.app",
        }
    )
    app_store = first.model_copy(
        update={
            "id": stable_software_id(EntityType.APPLICATION, "org.example.store"),
            "install_path": "/Applications/Store.app",
            "install_source": "mac_app_store",
        }
    )
    cask = SoftwareRecord(
        id=stable_software_id(EntityType.HOMEBREW_CASK, "example-app"),
        entity_type=EntityType.HOMEBREW_CASK,
        name="example-app",
        display_name="Example",
        version="2.4.1",
        app_artifacts=("Example.app", "Store.app"),
    )

    audit = _relationship_audit((first, duplicate, app_store), (cask,))

    apps = [record for record in audit.software if record.entity_type is EntityType.APPLICATION]
    linked_cask = next(
        record for record in audit.software if record.entity_type is EntityType.HOMEBREW_CASK
    )
    assert all(record.related_software_ids == () for record in apps)
    assert all(record.install_source != "homebrew_cask:example-app" for record in apps)
    assert linked_cask.related_software_ids == ()


def _relationship_audit(
    applications: tuple[SoftwareRecord, ...],
    casks: tuple[SoftwareRecord, ...],
) -> AuditDocument:
    def storage_collector(*, collected_at: datetime) -> StorageCollection:
        return StorageCollection(
            volumes=(),
            status=status("storage", CollectorState.COMPLETE, 0),
        )

    def application_collector(
        roots: Sequence[Path],
        *,
        collected_at: datetime,
        storage_resolver: Callable[[Path], StorageLocation],
    ) -> ApplicationCollection:
        del roots, collected_at, storage_resolver
        return ApplicationCollection(
            software=applications,
            status=status("applications", CollectorState.COMPLETE, len(applications)),
        )

    def homebrew_collector(
        *,
        collected_at: datetime,
        project_roots: Sequence[Path],
    ) -> HomebrewCollection:
        del collected_at, project_roots
        return HomebrewCollection(
            software=casks,
            status=status("homebrew", CollectorState.COMPLETE, len(casks)),
        )

    return AuditService(
        application_collector=application_collector,
        backup_collector=empty_backup_collector,
        homebrew_collector=homebrew_collector,
        storage_collector=storage_collector,
        startup_collector=empty_startup_collector,
        usage_collector=empty_usage_collector,
        clock=lambda: COLLECTED_AT,
        audit_id_factory=lambda: "audit:relationship",
    ).run(())
