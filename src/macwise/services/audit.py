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
    def __call__(self, *, collected_at: datetime) -> HomebrewCollection: ...


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


@dataclass(frozen=True, slots=True)
class AuditService:
    """Run read-only collectors and preserve partial results."""

    application_collector: ApplicationCollector = collect_host_applications
    homebrew_collector: HomebrewCollector = collect_homebrew
    storage_collector: StorageCollector = collect_storage
    clock: Callable[[], datetime] = _utc_now
    audit_id_factory: Callable[[], str] = _new_audit_id

    def run(self, application_roots: Sequence[Path]) -> AuditDocument:
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
            homebrew = self.homebrew_collector(collected_at=collected_at)
        except Exception:
            homebrew = HomebrewCollection(
                software=(),
                status=_failed_status("homebrew", collected_at),
            )

        software = sorted(
            (*applications.software, *homebrew.software),
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
