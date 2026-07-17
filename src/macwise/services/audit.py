"""Application service that assembles one truthful, versioned audit."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from macwise.collectors import (
    ApplicationCollection,
    HomebrewCollection,
    StorageCollection,
    collect_homebrew,
    collect_host_applications,
    collect_storage,
    resolve_storage_location,
)
from macwise.collectors.applications import StorageResolver
from macwise.models import (
    AuditDocument,
    CollectorState,
    CollectorStatus,
    EntityType,
    Evidence,
    Reliability,
    SoftwareRecord,
    StorageLocation,
)


class ApplicationCollector(Protocol):
    def __call__(
        self,
        roots: Sequence[Path],
        *,
        collected_at: datetime,
        storage_resolver: StorageResolver,
    ) -> ApplicationCollection: ...


class HomebrewCollector(Protocol):
    def __call__(
        self,
        *,
        collected_at: datetime,
        project_roots: Sequence[Path],
    ) -> HomebrewCollection: ...


class StorageCollector(Protocol):
    def __call__(self, *, collected_at: datetime) -> StorageCollection: ...


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _new_audit_id() -> str:
    return f"audit:{uuid4()}"


def _failed_status(collector: str, collected_at: datetime) -> CollectorStatus:
    public_name = "Homebrew" if collector == "homebrew" else collector.capitalize()
    return CollectorStatus(
        collector=collector,
        state=CollectorState.UNAVAILABLE,
        collected_at=collected_at,
        records_count=0,
        limitations=(f"The {public_name} collector failed unexpectedly.",),
    )


def _correlate_cask_applications(
    software: Sequence[SoftwareRecord],
    *,
    collected_at: datetime,
) -> tuple[SoftwareRecord, ...]:
    applications_by_name: dict[str, list[SoftwareRecord]] = {}
    casks_by_artifact: dict[str, list[tuple[SoftwareRecord, str]]] = {}
    for record in software:
        if record.entity_type is EntityType.APPLICATION and record.install_path is not None:
            applications_by_name.setdefault(Path(record.install_path).name.casefold(), []).append(
                record
            )
        elif record.entity_type is EntityType.HOMEBREW_CASK:
            for artifact in record.app_artifacts:
                if Path(artifact).name != artifact:
                    continue
                casks_by_artifact.setdefault(artifact.casefold(), []).append((record, artifact))

    related_ids: dict[str, set[str]] = {
        record.id: set(record.related_software_ids) for record in software
    }
    inferred_sources: dict[str, str] = {}
    added_evidence: dict[str, list[Evidence]] = {record.id: [] for record in software}
    for key, applications in applications_by_name.items():
        cask_claims = casks_by_artifact.get(key, [])
        if len(applications) != 1 or len(cask_claims) != 1:
            continue
        application = applications[0]
        cask, artifact = cask_claims[0]
        if application.install_source is not None:
            continue
        if (
            application.version is not None
            and cask.version is not None
            and application.version != cask.version
        ):
            continue
        related_ids[application.id].add(cask.id)
        related_ids[cask.id].add(application.id)
        inferred_sources[application.id] = f"homebrew_cask:{cask.name}"
        evidence = Evidence(
            kind="homebrew_cask_application_match",
            value={
                "application_id": application.id,
                "artifact": artifact,
                "cask_id": cask.id,
            },
            source="Homebrew cask artifact and application bundle metadata",
            collected_at=collected_at,
            reliability=Reliability.MEDIUM,
            limitations=("The match requires a unique artifact basename and compatible version.",),
        )
        added_evidence[application.id].append(evidence)
        added_evidence[cask.id].append(evidence)

    return tuple(
        record.model_copy(
            update={
                "install_source": inferred_sources.get(record.id, record.install_source),
                "related_software_ids": tuple(sorted(related_ids[record.id])),
                "evidence": (*record.evidence, *added_evidence[record.id]),
            }
        )
        for record in software
    )


@dataclass(frozen=True, slots=True)
class AuditService:
    """Run read-only collectors and preserve partial results."""

    application_collector: ApplicationCollector = collect_host_applications
    homebrew_collector: HomebrewCollector = collect_homebrew
    storage_collector: StorageCollector = collect_storage
    clock: Callable[[], datetime] = _utc_now
    audit_id_factory: Callable[[], str] = _new_audit_id

    def run(
        self,
        application_roots: Sequence[Path],
        *,
        project_roots: Sequence[Path] = (),
    ) -> AuditDocument:
        """Collect one audit, continuing when an independent collector fails."""
        collected_at = self.clock()
        try:
            storage = self.storage_collector(collected_at=collected_at)
        except Exception:
            storage = StorageCollection(
                volumes=(),
                status=_failed_status("storage", collected_at),
            )

        def storage_resolver(path: Path) -> StorageLocation:
            return resolve_storage_location(path, storage.volumes)

        try:
            applications = self.application_collector(
                application_roots,
                collected_at=collected_at,
                storage_resolver=storage_resolver,
            )
        except Exception:
            applications = ApplicationCollection(
                software=(),
                status=_failed_status("applications", collected_at),
            )

        try:
            homebrew = self.homebrew_collector(
                collected_at=collected_at,
                project_roots=project_roots,
            )
        except Exception:
            homebrew = HomebrewCollection(
                software=(),
                status=_failed_status("homebrew", collected_at),
            )

        homebrew_software = tuple(
            record.model_copy(
                update={
                    "storage_location": storage_resolver(Path(record.install_path))
                    if record.install_path is not None
                    else StorageLocation.UNKNOWN
                }
            )
            for record in homebrew.software
        )

        correlated_software = _correlate_cask_applications(
            (*applications.software, *homebrew_software),
            collected_at=collected_at,
        )
        software = sorted(
            correlated_software,
            key=lambda record: (
                record.entity_type.value,
                record.display_name.casefold(),
                record.id,
            ),
        )
        collectors = sorted(
            (applications.status, homebrew.status, storage.status),
            key=lambda status: status.collector,
        )
        volumes = sorted(storage.volumes, key=lambda volume: volume.device_identifier)
        return AuditDocument(
            audit_id=self.audit_id_factory(),
            collected_at=collected_at,
            software=tuple(software),
            volumes=tuple(volumes),
            collectors=tuple(collectors),
        )
