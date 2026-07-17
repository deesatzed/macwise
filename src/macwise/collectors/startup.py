"""Read-only startup plist and Homebrew service inventory."""

import os
import plistlib
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from macwise.models import (
    CollectorState,
    CollectorStatus,
    EntityType,
    Evidence,
    Reliability,
    SoftwareRecord,
    StartupKind,
    StartupRecord,
    stable_startup_id,
)


@dataclass(frozen=True, slots=True)
class StartupRoot:
    """One explicitly configured launch plist directory and its item kind."""

    kind: StartupKind
    path: Path


@dataclass(frozen=True, slots=True)
class StartupCollection:
    """Startup records and limitations that qualify them."""

    startup: tuple[StartupRecord, ...]
    status: CollectorStatus


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _program(metadata: dict[str, Any]) -> str | None:
    direct = _text(metadata.get("Program"))
    if direct is not None:
        return direct
    arguments: object = metadata.get("ProgramArguments", [])
    if isinstance(arguments, list) and arguments:
        return _text(cast(list[object], arguments)[0])
    return None


def _bundle_identifier(metadata: dict[str, Any]) -> str | None:
    direct = _text(metadata.get("BundleIdentifier"))
    if direct is not None:
        return direct
    associated: object = metadata.get("AssociatedBundleIdentifiers", [])
    if isinstance(associated, list):
        for raw_value in cast(list[object], associated):
            if (value := _text(raw_value)) is not None:
                return value
    return None


def parse_launch_plist(
    data: bytes | str,
    *,
    source_path: Path,
    kind: StartupKind,
    collected_at: datetime,
) -> StartupRecord:
    """Normalize one launchd plist without loading or executing it."""
    loaded = plistlib.loads(data.encode() if isinstance(data, str) else data)
    if not isinstance(loaded, dict):
        raise ValueError("Launch plist root is not a dictionary")
    metadata = cast(dict[str, Any], loaded)
    label = _text(metadata.get("Label"))
    if label is None:
        raise ValueError("Launch plist does not contain a label")
    disabled = metadata.get("Disabled")
    enabled = not disabled if isinstance(disabled, bool) else None
    program = _program(metadata)
    bundle_identifier = _bundle_identifier(metadata)
    return StartupRecord(
        id=stable_startup_id(kind, label),
        label=label,
        kind=kind,
        source_path=str(source_path),
        program=program,
        bundle_identifier=bundle_identifier,
        enabled=enabled,
        evidence=(
            Evidence(
                kind="launch_plist_metadata",
                value={
                    "bundle_identifier": bundle_identifier,
                    "enabled": enabled,
                    "label": label,
                    "program": program,
                },
                source=str(source_path),
                collected_at=collected_at,
                reliability=Reliability.HIGH,
                limitations=(
                    "The plist does not prove current launchd override or running state.",
                ),
            ),
        ),
    )


def _application_owner_ids(
    startup: StartupRecord,
    software: Sequence[SoftwareRecord],
) -> tuple[str, ...]:
    candidates: set[str] = set()
    normalized_program = (
        Path(os.path.abspath(startup.program))
        if startup.program and startup.program.startswith("/")
        else None
    )
    for record in software:
        if record.entity_type is not EntityType.APPLICATION:
            continue
        if startup.bundle_identifier and record.identifier == startup.bundle_identifier:
            candidates.add(record.id)
        if record.identifier and startup.label == record.identifier:
            candidates.add(record.id)
        if normalized_program is not None and record.install_path is not None:
            app_path = Path(os.path.abspath(record.install_path))
            if normalized_program == app_path or app_path in normalized_program.parents:
                candidates.add(record.id)
    return tuple(candidates) if len(candidates) == 1 else ()


def _homebrew_service_records(
    software: Sequence[SoftwareRecord],
    *,
    collected_at: datetime,
) -> tuple[StartupRecord, ...]:
    records: list[StartupRecord] = []
    for item in software:
        if item.entity_type is not EntityType.HOMEBREW_FORMULA or item.service_status is None:
            continue
        status = item.service_status.casefold()
        running = True if status == "started" else False if status in {"none", "stopped"} else None
        records.append(
            StartupRecord(
                id=stable_startup_id(StartupKind.HOMEBREW_SERVICE, item.name),
                label=item.name,
                kind=StartupKind.HOMEBREW_SERVICE,
                owner_software_ids=(item.id,),
                running=running,
                evidence=(
                    Evidence(
                        kind="homebrew_service_status",
                        value={"name": item.name, "status": item.service_status},
                        source="brew services list --json",
                        collected_at=collected_at,
                        reliability=Reliability.HIGH,
                    ),
                ),
            )
        )
    return tuple(records)


def collect_startup(
    software: Sequence[SoftwareRecord],
    *,
    roots: Sequence[StartupRoot],
    collected_at: datetime,
) -> StartupCollection:
    """Collect launch plist and Homebrew service records without loading them."""
    records: list[StartupRecord] = []
    limitations: list[str] = []
    for root in roots:
        if not root.path.exists():
            continue
        if root.path.is_symlink() or not root.path.is_dir():
            limitations.append(f"The startup folder {root.path} is not safely readable.")
            continue
        for path in sorted(root.path.glob("*.plist"), key=lambda item: str(item).casefold()):
            if path.is_symlink():
                limitations.append(f"The startup plist {path} is a symbolic link and was skipped.")
                continue
            try:
                parsed = parse_launch_plist(
                    path.read_bytes(),
                    source_path=path,
                    kind=root.kind,
                    collected_at=collected_at,
                )
            except (OSError, plistlib.InvalidFileException, ValueError):
                limitations.append(f"The startup plist {path} could not be read.")
                continue
            records.append(
                parsed.model_copy(
                    update={"owner_software_ids": _application_owner_ids(parsed, software)}
                )
            )
    records.extend(_homebrew_service_records(software, collected_at=collected_at))
    records.sort(key=lambda item: (item.kind.value, item.label.casefold(), item.id))
    return StartupCollection(
        startup=tuple(records),
        status=CollectorStatus(
            collector="startup",
            state=CollectorState.COMPLETE if not limitations else CollectorState.PARTIAL,
            collected_at=collected_at,
            records_count=len(records),
            limitations=tuple(limitations),
        ),
    )
