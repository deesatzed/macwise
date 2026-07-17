from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from macwise.collectors.backups import collect_backups, parse_latest_backup
from macwise.models import (
    CollectorState,
    PathEvidence,
    StorageLocation,
    VolumeRecord,
)
from macwise.system import CommandResult, CommandState, ReadCommand

COLLECTED_AT = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)
FIXTURES = Path(__file__).parents[1] / "fixtures" / "tmutil"


def test_parses_last_verifiable_backup_timestamp_from_tmutil_path() -> None:
    parsed = parse_latest_backup(
        (FIXTURES / "latestbackup.txt").read_text(encoding="utf-8"),
        timezone=UTC,
    )

    assert parsed == datetime(2026, 7, 16, 23, 15, tzinfo=UTC)
    assert parse_latest_backup("not a backup path", timezone=UTC) is None


def test_collects_configuration_last_backup_and_path_exclusions_without_coverage_claim() -> None:
    volume = VolumeRecord(
        id="volume:backup",
        name="Backup",
        device_identifier="disk2s1",
        mount_point="/Volumes/Backup",
        location=StorageLocation.EXTERNAL,
        time_machine_destination=True,
    )
    paths = (
        PathEvidence(
            id="path:support",
            subject_id="application:example",
            path="/Users/example/Library/Application Support/Example",
            kind="application_support",
        ),
        PathEvidence(
            id="path:cache",
            subject_id="application:example",
            path="/Users/example/Library/Caches/org.example.safe",
            kind="cache",
        ),
    )
    calls: list[tuple[ReadCommand, tuple[str, ...]]] = []

    def runner(command: ReadCommand, arguments: Sequence[str] = ()) -> CommandResult:
        calls.append((command, tuple(arguments)))
        stdout = (
            (FIXTURES / "latestbackup.txt").read_text(encoding="utf-8")
            if arguments == ("latestbackup", "-m")
            else (FIXTURES / "path-exclusions.txt").read_text(encoding="utf-8")
        )
        return CommandResult(command, CommandState.COMPLETE, stdout, "", 0, 0.01)

    result = collect_backups(
        volumes=(volume,),
        path_evidence=paths,
        collected_at=COLLECTED_AT,
        runner=runner,
    )

    assert result.status.state is CollectorState.COMPLETE
    assert result.backup.configured is True
    assert result.backup.available_destination_volume_ids == (volume.id,)
    assert result.backup.last_backup_at == datetime(2026, 7, 16, 23, 15, tzinfo=UTC)
    updated = {item.id: item for item in result.path_evidence}
    assert updated["path:support"].backup_excluded is False
    assert updated["path:cache"].backup_excluded is True
    assert "covered" not in result.backup.model_dump_json().casefold()
    assert calls == [
        (ReadCommand.TMUTIL, ("latestbackup", "-m")),
        (
            ReadCommand.TMUTIL,
            (
                "isexcluded",
                "/Users/example/Library/Application Support/Example",
                "/Users/example/Library/Caches/org.example.safe",
            ),
        ),
    ]


def test_backup_command_failure_preserves_unknowns_and_paths_as_partial() -> None:
    volume = VolumeRecord(
        id="volume:backup",
        name="Backup",
        device_identifier="disk2s1",
        time_machine_destination=True,
    )
    path = PathEvidence(
        id="path:unknown",
        subject_id="application:example",
        path="/Users/example/Library/Application Support/Example",
        kind="application_support",
        backup_excluded=False,
    )

    def failing(command: ReadCommand, arguments: Sequence[str] = ()) -> CommandResult:
        del arguments
        return CommandResult(
            command,
            CommandState.FAILED,
            "",
            "synthetic failure",
            1,
            0.01,
            ("Time Machine metadata is unavailable.",),
        )

    result = collect_backups(
        volumes=(volume,),
        path_evidence=(path,),
        collected_at=COLLECTED_AT,
        runner=failing,
    )

    assert result.status.state is CollectorState.PARTIAL
    assert result.backup.configured is True
    assert result.backup.last_backup_at is None
    assert result.path_evidence[0].backup_excluded is False
    assert result.status.limitations.count("Time Machine metadata is unavailable.") == 2
