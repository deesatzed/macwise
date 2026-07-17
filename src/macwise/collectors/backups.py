"""Read-only Time Machine summary and related-path exclusion evidence."""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, tzinfo
from pathlib import Path
from typing import Protocol

from macwise.collectors.storage import parse_time_machine_exclusions
from macwise.models import (
    BackupStatus,
    CollectorState,
    CollectorStatus,
    Evidence,
    PathEvidence,
    Reliability,
    VolumeRecord,
)
from macwise.system import CommandResult, CommandState, ReadCommand, run_read_command

BACKUP_COMPONENT = re.compile(r"^(\d{4}-\d{2}-\d{2}-\d{6})\.backup$")
MAX_BACKUP_PATHS = 200


class BackupRunner(Protocol):
    """The fixed Time Machine command boundary used by this collector."""

    def __call__(
        self,
        command: ReadCommand,
        arguments: Sequence[str] = (),
        /,
    ) -> CommandResult: ...


@dataclass(frozen=True, slots=True)
class BackupCollection:
    """Backup summary, updated path facts, and collection status."""

    backup: BackupStatus
    path_evidence: tuple[PathEvidence, ...]
    status: CollectorStatus


def parse_latest_backup(text: str, *, timezone: tzinfo) -> datetime | None:
    """Parse the last timestamped `.backup` component in a tmutil path."""
    value = text.strip()
    if not value.startswith("/") or "\n" in value:
        return None
    matches = [
        match.group(1)
        for component in Path(value).parts
        if (match := BACKUP_COMPONENT.fullmatch(component)) is not None
    ]
    if not matches:
        return None
    try:
        return datetime.strptime(matches[-1], "%Y-%m-%d-%H%M%S").replace(tzinfo=timezone)
    except ValueError:
        return None


def collect_backups(
    *,
    volumes: Sequence[VolumeRecord],
    path_evidence: Sequence[PathEvidence],
    collected_at: datetime,
    runner: BackupRunner = run_read_command,
) -> BackupCollection:
    """Collect configuration/date/exclusion facts without inferring recoverability."""
    known_configuration = [
        volume.time_machine_destination
        for volume in volumes
        if volume.time_machine_destination is not None
    ]
    configured = any(known_configuration) if known_configuration else None
    available_destination_ids = tuple(
        sorted(
            volume.id
            for volume in volumes
            if volume.time_machine_destination is True and volume.mount_point is not None
        )
    )
    limitations: list[str] = []
    evidence: list[Evidence] = []
    last_backup_at: datetime | None = None

    if configured is not False:
        latest = runner(ReadCommand.TMUTIL, ("latestbackup", "-m"))
        if latest.state is CommandState.COMPLETE:
            timezone = collected_at.tzinfo
            if timezone is None:
                raise ValueError("collected_at must be timezone-aware")
            last_backup_at = parse_latest_backup(latest.stdout, timezone=timezone)
            if last_backup_at is not None:
                evidence.append(
                    Evidence(
                        kind="time_machine_latest_backup",
                        value=last_backup_at.isoformat(),
                        source="tmutil latestbackup -m",
                        collected_at=collected_at,
                        reliability=Reliability.MEDIUM,
                        limitations=(
                            "The timestamp does not prove any specific related path is recoverable.",
                        ),
                    )
                )
            elif latest.stdout.strip():
                limitations.append("The latest Time Machine backup timestamp could not be read.")
            limitations.extend(latest.limitations)
        else:
            limitations.extend(
                latest.limitations or ("Time Machine latest-backup metadata is unavailable.",)
            )

    safe_paths = [
        item.path for item in path_evidence if "\n" not in item.path and "\0" not in item.path
    ]
    if len(safe_paths) > MAX_BACKUP_PATHS:
        limitations.append(
            f"Time Machine exclusion checks stopped at {MAX_BACKUP_PATHS} related paths."
        )
        safe_paths = safe_paths[:MAX_BACKUP_PATHS]

    exclusions: dict[str, bool] = {}
    if safe_paths:
        excluded = runner(ReadCommand.TMUTIL, ("isexcluded", *safe_paths))
        if excluded.state is CommandState.COMPLETE:
            exclusions = parse_time_machine_exclusions(excluded.stdout)
            limitations.extend(excluded.limitations)
        else:
            limitations.extend(
                excluded.limitations or ("Time Machine path-exclusion metadata is unavailable.",)
            )

    updated_paths = tuple(
        item.model_copy(update={"backup_excluded": exclusions[item.path]})
        if item.path in exclusions
        else item
        for item in path_evidence
    )
    configuration_evidence = Evidence(
        kind="time_machine_configuration",
        value={
            "available_destination_volume_ids": list(available_destination_ids),
            "configured": configured,
        },
        source="diskutil and tmutil destination metadata",
        collected_at=collected_at,
        reliability=Reliability.HIGH if configured is not None else Reliability.UNKNOWN,
        limitations=("Configuration does not prove path-level backup coverage.",),
    )
    backup = BackupStatus(
        configured=configured,
        available_destination_volume_ids=available_destination_ids,
        last_backup_at=last_backup_at,
        evidence=(configuration_evidence, *evidence),
        limitations=tuple(limitations),
    )
    return BackupCollection(
        backup=backup,
        path_evidence=updated_paths,
        status=CollectorStatus(
            collector="backups",
            state=CollectorState.COMPLETE if not limitations else CollectorState.PARTIAL,
            collected_at=collected_at,
            records_count=1 + len(updated_paths),
            limitations=tuple(limitations),
        ),
    )
