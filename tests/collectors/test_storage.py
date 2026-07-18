from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from macwise.collectors.storage import (
    collect_storage,
    parse_apfs_topology,
    parse_time_machine_destinations,
    parse_time_machine_exclusions,
    parse_volume_info,
    resolve_storage_location,
)
from macwise.models import CollectorState, StorageLocation
from macwise.system import CommandResult, CommandState, ReadCommand

COLLECTED_AT = datetime(2026, 7, 17, 16, 0, tzinfo=UTC)
FIXTURES = Path(__file__).parents[1] / "fixtures" / "diskutil"
TMUTIL_FIXTURES = Path(__file__).parents[1] / "fixtures" / "tmutil"


def fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_parses_internal_volume_capacity_security_and_health() -> None:
    volume = parse_volume_info(fixture_bytes("info-internal.plist"), collected_at=COLLECTED_AT)

    assert volume.device_identifier == "disk1s1"
    assert volume.parent_device_identifier == "disk0"
    assert volume.whole_disk is False
    assert volume.content == "Apple_APFS"
    assert volume.apfs_container_identifier == "disk1"
    assert volume.physical_store_identifiers == ("disk0s2",)
    assert volume.name == "System"
    assert volume.mount_point == "/"
    assert volume.filesystem == "APFS"
    assert volume.capacity_bytes == 1_000_000
    assert volume.free_bytes == 400_000
    assert volume.location is StorageLocation.INTERNAL
    assert volume.removable is False
    assert volume.read_only is False
    assert volume.encrypted is True
    assert volume.protocol == "Apple Fabric"
    assert volume.smart_status == "Verified"
    assert volume.ownership_enabled is True
    assert volume.id.startswith("volume:")


def test_mounted_apfs_volume_uses_container_free_when_free_space_is_zero() -> None:
    metadata = (
        fixture_bytes("info-internal.plist")
        .decode()
        .replace(
            "<key>FreeSpace</key><integer>400000</integer>",
            "<key>FreeSpace</key><integer>0</integer>\n"
            "  <key>APFSContainerFree</key><integer>375000</integer>",
        )
    )

    volume = parse_volume_info(metadata, collected_at=COLLECTED_AT)

    assert volume.mount_point == "/"
    assert volume.free_bytes == 375_000


def test_parses_apfs_topology_destinations_and_exclusions() -> None:
    topology = parse_apfs_topology(fixture_bytes("apfs-list.plist"))
    destinations = parse_time_machine_destinations(
        (TMUTIL_FIXTURES / "destinationinfo.plist").read_bytes()
    )
    exclusions = parse_time_machine_exclusions(
        (TMUTIL_FIXTURES / "exclusions.txt").read_text(encoding="utf-8")
    )

    assert topology["disk1s1"].container_identifier == "disk1"
    assert topology["disk1s1"].physical_store_identifiers == ("disk0s2",)
    assert topology["disk1s1"].roles == ("System",)
    assert topology["disk2s1"].roles == ("Backup",)
    assert destinations == ("/Volumes/Archive",)
    assert exclusions == {"/": False, "/Volumes/Archive": True}


def test_parses_external_and_unmounted_volumes_without_guessing() -> None:
    external = parse_volume_info(fixture_bytes("info-external.plist"), collected_at=COLLECTED_AT)
    unmounted = parse_volume_info(fixture_bytes("info-unmounted.plist"), collected_at=COLLECTED_AT)

    assert external.location is StorageLocation.EXTERNAL
    assert external.mount_point == "/Volumes/Archive"
    assert external.removable is True
    assert unmounted.location is StorageLocation.EXTERNAL
    assert unmounted.mount_point is None
    assert unmounted.free_bytes is None
    assert unmounted.read_only is False
    assert unmounted.encrypted is None


def test_collects_each_listed_disk_and_reports_unavailable_info_as_partial() -> None:
    calls: list[tuple[ReadCommand, tuple[str, ...]]] = []
    info_by_identifier = {
        "disk1s1": fixture_bytes("info-internal.plist"),
        "disk2s1": fixture_bytes("info-external.plist"),
        "disk2s2": fixture_bytes("info-unmounted.plist"),
    }

    def runner(command: ReadCommand, arguments: Sequence[str] = ()) -> CommandResult:
        calls.append((command, tuple(arguments)))
        if arguments == ("list", "-plist"):
            stdout = fixture_bytes("list.plist").decode()
            state = CommandState.COMPLETE
            limitations: tuple[str, ...] = ()
        elif arguments == ("apfs", "list", "-plist"):
            stdout = fixture_bytes("apfs-list.plist").decode()
            state = CommandState.COMPLETE
            limitations = ()
        elif command is ReadCommand.TMUTIL and arguments == ("destinationinfo", "-X"):
            stdout = (TMUTIL_FIXTURES / "destinationinfo.plist").read_text(encoding="utf-8")
            state = CommandState.COMPLETE
            limitations = ()
        elif command is ReadCommand.TMUTIL and arguments[0] == "isexcluded":
            stdout = (TMUTIL_FIXTURES / "exclusions.txt").read_text(encoding="utf-8")
            state = CommandState.COMPLETE
            limitations = ()
        else:
            identifier = arguments[-1]
            if identifier not in info_by_identifier:
                return CommandResult(
                    command=command,
                    state=CommandState.FAILED,
                    stdout="",
                    stderr="Synthetic unavailable disk",
                    return_code=1,
                    duration_seconds=0.01,
                    limitations=(f"Metadata for {identifier} is unavailable.",),
                )
            stdout = info_by_identifier[identifier].decode()
            state = CommandState.COMPLETE
            limitations = ()
        return CommandResult(
            command=command,
            state=state,
            stdout=stdout,
            stderr="",
            return_code=0,
            duration_seconds=0.01,
            limitations=limitations,
        )

    result = collect_storage(collected_at=COLLECTED_AT, runner=runner)

    assert result.status.state is CollectorState.PARTIAL
    assert result.status.records_count == 3
    assert {volume.device_identifier for volume in result.volumes} == {
        "disk1s1",
        "disk2s1",
        "disk2s2",
    }
    assert any("disk3s1" in limitation for limitation in result.status.limitations)
    assert calls[0] == (ReadCommand.DISKUTIL, ("list", "-plist"))
    assert calls[1] == (ReadCommand.DISKUTIL, ("apfs", "list", "-plist"))
    assert calls[-2] == (ReadCommand.TMUTIL, ("destinationinfo", "-X"))
    assert calls[-1] == (
        ReadCommand.TMUTIL,
        ("isexcluded", "/", "/Volumes/Archive"),
    )
    volumes = {volume.device_identifier: volume for volume in result.volumes}
    internal = volumes["disk1s1"]
    external = volumes["disk2s1"]
    assert internal.apfs_container_identifier == "disk1"
    assert internal.physical_store_identifiers == ("disk0s2",)
    assert internal.time_machine_role is None
    assert internal.time_machine_destination is False
    assert internal.time_machine_excluded is False
    assert external.apfs_container_identifier == "disk2"
    assert external.physical_store_identifiers == ("disk2s3",)
    assert external.time_machine_role == "Backup"
    assert external.time_machine_destination is True
    assert external.time_machine_excluded is True


def test_optional_storage_metadata_failure_preserves_base_volume_as_partial() -> None:
    def runner(command: ReadCommand, arguments: Sequence[str] = ()) -> CommandResult:
        if arguments == ("list", "-plist"):
            list_with_one_disk = """<?xml version="1.0" encoding="UTF-8"?>
            <plist version="1.0"><dict><key>AllDisks</key><array>
            <string>disk1s1</string></array></dict></plist>"""
            return CommandResult(command, CommandState.COMPLETE, list_with_one_disk, "", 0, 0.01)
        if arguments == ("info", "-plist", "disk1s1"):
            return CommandResult(
                command,
                CommandState.COMPLETE,
                fixture_bytes("info-internal.plist").decode(),
                "",
                0,
                0.01,
            )
        return CommandResult(
            command,
            CommandState.FAILED,
            "",
            "synthetic unavailable metadata",
            1,
            0.01,
            (f"The {command.value} optional metadata is unavailable.",),
        )

    result = collect_storage(collected_at=COLLECTED_AT, runner=runner)

    assert result.status.records_count == 1
    assert result.status.state is CollectorState.PARTIAL
    assert result.volumes[0].time_machine_destination is None
    assert result.volumes[0].time_machine_excluded is None
    assert any("diskutil optional metadata" in item for item in result.status.limitations)
    assert any("tmutil optional metadata" in item for item in result.status.limitations)


def test_unavailable_diskutil_returns_an_explicit_unavailable_status() -> None:
    def unavailable(command: ReadCommand, arguments: Sequence[str] = ()) -> CommandResult:
        del arguments
        return CommandResult(
            command=command,
            state=CommandState.UNAVAILABLE,
            stdout="",
            stderr="",
            return_code=None,
            duration_seconds=0,
            limitations=("The diskutil read-only command is not available.",),
        )

    result = collect_storage(collected_at=COLLECTED_AT, runner=unavailable)

    assert result.volumes == ()
    assert result.status.state is CollectorState.UNAVAILABLE
    assert result.status.limitations == ("The diskutil read-only command is not available.",)


def test_path_location_uses_the_longest_matching_mounted_volume() -> None:
    internal = parse_volume_info(fixture_bytes("info-internal.plist"), collected_at=COLLECTED_AT)
    external = parse_volume_info(fixture_bytes("info-external.plist"), collected_at=COLLECTED_AT)
    unmounted = parse_volume_info(fixture_bytes("info-unmounted.plist"), collected_at=COLLECTED_AT)
    volumes = (internal, external, unmounted)

    assert (
        resolve_storage_location(Path("/Applications/Example.app"), volumes)
        is StorageLocation.INTERNAL
    )
    assert (
        resolve_storage_location(Path("/Volumes/Archive/Models/model.bin"), volumes)
        is StorageLocation.EXTERNAL
    )
    assert (
        resolve_storage_location(Path("/Volumes/Missing/App.app"), volumes)
        is StorageLocation.UNKNOWN
    )
    assert (
        resolve_storage_location(Path("/Network/Share/App.app"), (external,))
        is StorageLocation.UNKNOWN
    )
