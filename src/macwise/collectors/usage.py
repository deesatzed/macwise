"""Read-only last-use and bounded related-data evidence collection."""

import os
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from macwise.models import (
    CollectorState,
    CollectorStatus,
    EntityType,
    Evidence,
    PathEvidence,
    Reliability,
    SoftwareRecord,
    StorageLocation,
    stable_path_evidence_id,
)
from macwise.system import CommandResult, CommandState, ReadCommand, run_read_command

StorageResolver = Callable[[Path], StorageLocation]
BUNDLE_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.-]{0,254}$")
MAX_RELATED_ENTRIES = 10_000


class UsageRunner(Protocol):
    """The fixed read-command boundary needed for usage metadata."""

    def __call__(
        self,
        command: ReadCommand,
        arguments: Sequence[str] = (),
        /,
    ) -> CommandResult: ...


@dataclass(frozen=True, slots=True)
class UsageSignal:
    """Last-use evidence associated with one software record."""

    subject_id: str
    last_used_at: datetime | None
    evidence: tuple[Evidence, ...] = ()


@dataclass(frozen=True, slots=True)
class UsageCollection:
    """Usage signals, related paths, and their collection status."""

    signals: tuple[UsageSignal, ...]
    path_evidence: tuple[PathEvidence, ...]
    status: CollectorStatus


def _unknown_storage(_path: Path) -> StorageLocation:
    return StorageLocation.UNKNOWN


def parse_spotlight_last_used(text: str) -> datetime | None:
    """Parse the stable raw `mdls` date shape, preserving null as unknown."""
    value = text.strip().strip('"')
    if not value or value == "(null)":
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S %z")
    except ValueError:
        return None


def _safe_component(value: str) -> bool:
    return (
        value not in {".", ".."}
        and Path(value).name == value
        and "/" not in value
        and "\\" not in value
        and "\n" not in value
        and "\0" not in value
    )


def _path_size_and_mtime(path: Path) -> tuple[int, datetime]:
    metadata = path.lstat()
    total = metadata.st_size
    latest = metadata.st_mtime
    entries = 1
    if path.is_dir() and not path.is_symlink():
        for current_root, directories, files in os.walk(path, followlinks=False):
            root = Path(current_root)
            retained: list[str] = []
            for directory in directories:
                child = root / directory
                child_metadata = child.lstat()
                entries += 1
                if entries > MAX_RELATED_ENTRIES:
                    raise OSError("related-data entry limit reached")
                total += child_metadata.st_size
                latest = max(latest, child_metadata.st_mtime)
                if not child.is_symlink():
                    retained.append(directory)
            directories[:] = retained
            for filename in files:
                child_metadata = (root / filename).lstat()
                entries += 1
                if entries > MAX_RELATED_ENTRIES:
                    raise OSError("related-data entry limit reached")
                total += child_metadata.st_size
                latest = max(latest, child_metadata.st_mtime)
    return total, datetime.fromtimestamp(latest, tz=UTC)


def _related_candidates(
    record: SoftwareRecord,
    home_library: Path,
    limitations: list[str],
) -> tuple[tuple[str, Path], ...]:
    candidates: list[tuple[str, Path]] = []
    identifier = record.identifier
    if identifier is not None:
        if BUNDLE_IDENTIFIER.fullmatch(identifier):
            candidates.extend(
                (
                    ("cache", home_library / "Caches" / identifier),
                    ("preferences", home_library / "Preferences" / f"{identifier}.plist"),
                    ("container", home_library / "Containers" / identifier),
                )
            )
        else:
            limitations.append(f"Related data for {record.id} has an unsafe bundle identifier.")
    if _safe_component(record.display_name):
        candidates.append(
            ("application_support", home_library / "Application Support" / record.display_name)
        )
    else:
        limitations.append(f"Related data for {record.id} has an unsafe application name.")
    return tuple(candidates)


def collect_usage(
    software: Sequence[SoftwareRecord],
    *,
    home_library: Path,
    collected_at: datetime,
    storage_resolver: StorageResolver = _unknown_storage,
    runner: UsageRunner = run_read_command,
) -> UsageCollection:
    """Collect bounded usage/path facts without launching or reading content."""
    signals: list[UsageSignal] = []
    paths: list[PathEvidence] = []
    limitations: list[str] = []

    for record in software:
        if record.entity_type is not EntityType.APPLICATION or record.install_path is None:
            continue
        mdls = runner(
            ReadCommand.MDLS,
            ("-name", "kMDItemLastUsedDate", "-raw", record.install_path),
        )
        last_used_at: datetime | None = None
        signal_evidence: tuple[Evidence, ...] = ()
        if mdls.state is CommandState.COMPLETE:
            last_used_at = parse_spotlight_last_used(mdls.stdout)
            raw_value = mdls.stdout.strip().strip('"')
            if last_used_at is not None:
                signal_evidence = (
                    Evidence(
                        kind="spotlight_last_used",
                        value=last_used_at.isoformat(),
                        source=f"mdls kMDItemLastUsedDate {record.install_path}",
                        collected_at=collected_at,
                        reliability=Reliability.MEDIUM,
                        limitations=("Spotlight metadata can be absent, stale, or reset.",),
                    ),
                )
            elif raw_value not in {"", "(null)"}:
                limitations.append(f"Spotlight last-use metadata for {record.id} was unreadable.")
            limitations.extend(mdls.limitations)
        else:
            limitations.extend(
                mdls.limitations or (f"Spotlight metadata for {record.id} is unavailable.",)
            )
        signals.append(
            UsageSignal(
                subject_id=record.id,
                last_used_at=last_used_at,
                evidence=signal_evidence,
            )
        )

        for kind, path in _related_candidates(record, home_library, limitations):
            if path.is_symlink() or not path.exists():
                continue
            try:
                size_bytes, last_modified_at = _path_size_and_mtime(path)
                storage_location = storage_resolver(path)
            except OSError:
                limitations.append(f"Related-data metadata for {record.id} could not be read.")
                continue
            evidence = Evidence(
                kind="related_data_path",
                value={
                    "kind": kind,
                    "last_modified_at": last_modified_at.isoformat(),
                    "size_bytes": size_bytes,
                    "storage_location": storage_location.value,
                },
                source="bounded filesystem metadata",
                collected_at=collected_at,
                reliability=Reliability.HIGH,
                limitations=(
                    "This measures one known path and is not a complete related-data inventory.",
                ),
            )
            paths.append(
                PathEvidence(
                    id=stable_path_evidence_id(record.id, str(path)),
                    subject_id=record.id,
                    path=str(path),
                    kind=kind,
                    size_bytes=size_bytes,
                    storage_location=storage_location,
                    last_modified_at=last_modified_at,
                    evidence=(evidence,),
                )
            )

    paths.sort(key=lambda item: (item.subject_id, item.kind, item.path.casefold()))
    return UsageCollection(
        signals=tuple(signals),
        path_evidence=tuple(paths),
        status=CollectorStatus(
            collector="usage",
            state=CollectorState.COMPLETE if not limitations else CollectorState.PARTIAL,
            collected_at=collected_at,
            records_count=len(signals) + len(paths),
            limitations=tuple(limitations),
        ),
    )
