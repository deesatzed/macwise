"""Read-only storage inventory from structured diskutil output."""

import os
import plistlib
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol, cast

from macwise.models import (
    CollectorState,
    CollectorStatus,
    Evidence,
    Reliability,
    StorageLocation,
    VolumeRecord,
    stable_volume_id,
)
from macwise.system import CommandResult, CommandState, ReadCommand, run_read_command

DISK_IDENTIFIER = re.compile(r"^disk[0-9]+(?:s[0-9]+)*$")


class StorageRunner(Protocol):
    """The narrow command boundary needed by the storage collector."""

    def __call__(
        self,
        command: ReadCommand,
        arguments: Sequence[str] = (),
        /,
    ) -> CommandResult: ...


@dataclass(frozen=True, slots=True)
class StorageCollection:
    """Volume records and the limitations that qualify them."""

    volumes: tuple[VolumeRecord, ...]
    status: CollectorStatus


@dataclass(frozen=True, slots=True)
class APFSVolumeTopology:
    """Validated APFS relationships for one volume identifier."""

    container_identifier: str
    physical_store_identifiers: tuple[str, ...]
    roles: tuple[str, ...]


def _mapping_from_plist(data: bytes | str) -> dict[str, Any]:
    loaded = plistlib.loads(data.encode() if isinstance(data, str) else data)
    if not isinstance(loaded, dict):
        raise ValueError("Property list root is not a dictionary")
    return cast(dict[str, Any], loaded)


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _integer(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _boolean(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _read_only(metadata: dict[str, Any]) -> bool | None:
    values = (
        _boolean(cast(object, metadata.get("ReadOnlyMedia"))),
        _boolean(cast(object, metadata.get("ReadOnlyVolume"))),
    )
    known = tuple(value for value in values if value is not None)
    return any(known) if known else None


def _device_identifier(value: object) -> str | None:
    identifier = _text(value)
    return identifier if identifier is not None and DISK_IDENTIFIER.fullmatch(identifier) else None


def _identifier_values(value: object, key: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    identifiers: list[str] = []
    for raw_item in cast(list[object], value):
        item = cast(dict[str, Any], raw_item) if isinstance(raw_item, dict) else None
        identifier = _device_identifier(item.get(key)) if item is not None else None
        if identifier is not None:
            identifiers.append(identifier)
    return tuple(dict.fromkeys(identifiers))


def parse_apfs_topology(data: bytes | str) -> dict[str, APFSVolumeTopology]:
    """Parse `diskutil apfs list -plist` into validated volume relationships."""
    metadata = _mapping_from_plist(data)
    raw_containers: object = metadata.get("Containers", [])
    if not isinstance(raw_containers, list):
        raise ValueError("APFS metadata does not contain a container list")
    topology: dict[str, APFSVolumeTopology] = {}
    for raw_container in cast(list[object], raw_containers):
        if not isinstance(raw_container, dict):
            continue
        container = cast(dict[str, Any], raw_container)
        container_identifier = _device_identifier(container.get("ContainerReference"))
        if container_identifier is None:
            continue
        physical_stores = _identifier_values(container.get("PhysicalStores"), "DeviceIdentifier")
        raw_volumes: object = container.get("Volumes", [])
        if not isinstance(raw_volumes, list):
            continue
        for raw_volume in cast(list[object], raw_volumes):
            if not isinstance(raw_volume, dict):
                continue
            volume = cast(dict[str, Any], raw_volume)
            volume_identifier = _device_identifier(volume.get("DeviceIdentifier"))
            if volume_identifier is None:
                continue
            raw_roles: object = volume.get("Roles", [])
            roles = (
                tuple(
                    dict.fromkeys(
                        role
                        for raw_role in cast(list[object], raw_roles)
                        if (role := _text(raw_role)) is not None
                    )
                )
                if isinstance(raw_roles, list)
                else ()
            )
            topology[volume_identifier] = APFSVolumeTopology(
                container_identifier=container_identifier,
                physical_store_identifiers=physical_stores,
                roles=roles,
            )
    return topology


def parse_time_machine_destinations(data: bytes | str) -> tuple[str, ...]:
    """Parse configured Time Machine destination mount points from plist output."""
    metadata = _mapping_from_plist(data)
    raw_destinations: object = metadata.get("Destinations", [])
    if not isinstance(raw_destinations, list):
        raise ValueError("Time Machine metadata does not contain a destination list")
    mount_points: list[str] = []
    for raw_destination in cast(list[object], raw_destinations):
        if not isinstance(raw_destination, dict):
            continue
        destination = cast(dict[str, Any], raw_destination)
        mount_point = _text(destination.get("MountPoint"))
        if mount_point is not None and mount_point.startswith("/") and "\n" not in mount_point:
            mount_points.append(mount_point)
    return tuple(sorted(dict.fromkeys(mount_points), key=str.casefold))


def parse_time_machine_exclusions(text: str) -> dict[str, bool]:
    """Parse `tmutil isexcluded` lines into path-to-excluded state."""
    exclusions: dict[str, bool] = {}
    pattern = re.compile(r"^\[(Excluded|Included)\]\s{2}(.+)$")
    for line in text.splitlines():
        match = pattern.fullmatch(line)
        if match is not None:
            exclusions[match.group(2)] = match.group(1) == "Excluded"
    return exclusions


def parse_volume_info(data: bytes | str, *, collected_at: datetime) -> VolumeRecord:
    """Normalize one `diskutil info -plist` document."""
    metadata = _mapping_from_plist(data)
    device_identifier = _text(cast(object, metadata.get("DeviceIdentifier")))
    if device_identifier is None or not DISK_IDENTIFIER.fullmatch(device_identifier):
        raise ValueError("Volume metadata does not contain a safe device identifier")

    internal = _boolean(cast(object, metadata.get("Internal")))
    parent_device_identifier = _device_identifier(metadata.get("ParentWholeDisk"))
    whole_disk = _boolean(cast(object, metadata.get("WholeDisk")))
    content = _text(cast(object, metadata.get("Content")))
    apfs_container_identifier = _device_identifier(metadata.get("APFSContainerReference"))
    physical_store_identifiers = _identifier_values(
        metadata.get("APFSPhysicalStores"),
        "APFSPhysicalStore",
    )
    location = (
        StorageLocation.INTERNAL
        if internal is True
        else StorageLocation.EXTERNAL
        if internal is False
        else StorageLocation.UNKNOWN
    )
    encrypted = _boolean(cast(object, metadata.get("Encrypted")))
    if encrypted is None:
        encrypted = _boolean(cast(object, metadata.get("FileVault")))

    name = _text(cast(object, metadata.get("VolumeName"))) or device_identifier
    mount_point = _text(cast(object, metadata.get("MountPoint")))
    filesystem = _text(cast(object, metadata.get("FilesystemName"))) or _text(
        cast(object, metadata.get("FilesystemType"))
    )
    capacity = _integer(cast(object, metadata.get("TotalSize")))
    free = _integer(cast(object, metadata.get("FreeSpace")))
    removable = _boolean(cast(object, metadata.get("RemovableMedia")))
    protocol = _text(cast(object, metadata.get("BusProtocol")))
    smart_status = _text(cast(object, metadata.get("SMARTStatus")))
    read_only = _read_only(metadata)
    ownership_enabled = _boolean(cast(object, metadata.get("GlobalPermissionsEnabled")))

    return VolumeRecord(
        id=stable_volume_id(device_identifier),
        name=name,
        device_identifier=device_identifier,
        parent_device_identifier=parent_device_identifier,
        whole_disk=whole_disk,
        content=content,
        apfs_container_identifier=apfs_container_identifier,
        physical_store_identifiers=physical_store_identifiers,
        mount_point=mount_point,
        location=location,
        filesystem=filesystem,
        capacity_bytes=capacity,
        free_bytes=free,
        read_only=read_only,
        encrypted=encrypted,
        removable=removable,
        protocol=protocol,
        smart_status=smart_status,
        ownership_enabled=ownership_enabled,
        evidence=(
            Evidence(
                kind="diskutil_volume_metadata",
                value={
                    "capacity_bytes": capacity,
                    "device_identifier": device_identifier,
                    "parent_device_identifier": parent_device_identifier,
                    "whole_disk": whole_disk,
                    "content": content,
                    "apfs_container_identifier": apfs_container_identifier,
                    "physical_store_identifiers": list(physical_store_identifiers),
                    "encrypted": encrypted,
                    "free_bytes": free,
                    "internal": internal,
                    "mount_point": mount_point,
                    "read_only": read_only,
                    "removable": removable,
                    "ownership_enabled": ownership_enabled,
                },
                source=f"diskutil info -plist {device_identifier}",
                collected_at=collected_at,
                reliability=Reliability.HIGH,
            ),
        ),
    )


def _listed_identifiers(data: str) -> tuple[str, ...]:
    metadata = _mapping_from_plist(data)
    raw_identifiers: object = metadata.get("AllDisks", [])
    if not isinstance(raw_identifiers, list):
        raise ValueError("diskutil list metadata does not contain AllDisks")
    identifiers: list[str] = []
    for raw_identifier in cast(list[object], raw_identifiers):
        identifier = _text(raw_identifier)
        if identifier is None or not DISK_IDENTIFIER.fullmatch(identifier):
            continue
        identifiers.append(identifier)
    return tuple(dict.fromkeys(identifiers))


def collect_storage(
    *,
    collected_at: datetime,
    runner: StorageRunner = run_read_command,
) -> StorageCollection:
    """Collect disk and volume metadata through read-only diskutil plist commands."""
    listed = runner(ReadCommand.DISKUTIL, ("list", "-plist"))
    if listed.state is not CommandState.COMPLETE:
        state = (
            CollectorState.UNAVAILABLE
            if listed.state is CommandState.UNAVAILABLE
            else CollectorState.PARTIAL
        )
        return StorageCollection(
            volumes=(),
            status=CollectorStatus(
                collector="storage",
                state=state,
                collected_at=collected_at,
                records_count=0,
                limitations=listed.limitations,
            ),
        )

    try:
        identifiers = _listed_identifiers(listed.stdout)
    except (plistlib.InvalidFileException, ValueError, UnicodeError):
        return StorageCollection(
            volumes=(),
            status=CollectorStatus(
                collector="storage",
                state=CollectorState.PARTIAL,
                collected_at=collected_at,
                records_count=0,
                limitations=("The disk list metadata could not be read.",),
            ),
        )

    volumes: list[VolumeRecord] = []
    limitations: list[str] = list(listed.limitations)
    apfs_result = runner(ReadCommand.DISKUTIL, ("apfs", "list", "-plist"))
    topology: dict[str, APFSVolumeTopology] = {}
    if apfs_result.state is CommandState.COMPLETE:
        try:
            topology = parse_apfs_topology(apfs_result.stdout)
        except (plistlib.InvalidFileException, ValueError, UnicodeError):
            limitations.append("The APFS topology metadata could not be read.")
        limitations.extend(apfs_result.limitations)
    else:
        limitations.extend(
            apfs_result.limitations or ("The APFS topology metadata is unavailable.",)
        )

    for identifier in identifiers:
        info = runner(ReadCommand.DISKUTIL, ("info", "-plist", identifier))
        if info.state is not CommandState.COMPLETE:
            limitations.extend(info.limitations or (f"Metadata for {identifier} is unavailable.",))
            continue
        try:
            volume = parse_volume_info(info.stdout, collected_at=collected_at)
            apfs = topology.get(identifier)
            if apfs is not None:
                topology_evidence = Evidence(
                    kind="diskutil_apfs_topology",
                    value={
                        "container_identifier": apfs.container_identifier,
                        "physical_store_identifiers": list(apfs.physical_store_identifiers),
                        "roles": list(apfs.roles),
                    },
                    source="diskutil apfs list -plist",
                    collected_at=collected_at,
                    reliability=Reliability.HIGH,
                )
                volume = volume.model_copy(
                    update={
                        "apfs_container_identifier": apfs.container_identifier,
                        "physical_store_identifiers": apfs.physical_store_identifiers,
                        "time_machine_role": "Backup" if "Backup" in apfs.roles else None,
                        "evidence": (*volume.evidence, topology_evidence),
                    }
                )
            volumes.append(volume)
        except (plistlib.InvalidFileException, ValueError, UnicodeError):
            limitations.append(f"Metadata for {identifier} could not be read.")

    destination_result = runner(ReadCommand.TMUTIL, ("destinationinfo", "-X"))
    destinations: tuple[str, ...] | None = None
    if destination_result.state is CommandState.COMPLETE:
        try:
            destinations = parse_time_machine_destinations(destination_result.stdout)
        except (plistlib.InvalidFileException, ValueError, UnicodeError):
            limitations.append("The Time Machine destination metadata could not be read.")
        limitations.extend(destination_result.limitations)
    else:
        limitations.extend(
            destination_result.limitations
            or ("The Time Machine destination metadata is unavailable.",)
        )

    mount_points = tuple(
        volume.mount_point
        for volume in volumes
        if volume.mount_point is not None and "\n" not in volume.mount_point
    )
    exclusions: dict[str, bool] | None = None
    if mount_points:
        exclusion_result = runner(ReadCommand.TMUTIL, ("isexcluded", *mount_points))
        if exclusion_result.state is CommandState.COMPLETE:
            exclusions = parse_time_machine_exclusions(exclusion_result.stdout)
            limitations.extend(exclusion_result.limitations)
        else:
            limitations.extend(
                exclusion_result.limitations
                or ("The Time Machine exclusion metadata is unavailable.",)
            )

    enriched_volumes: list[VolumeRecord] = []
    for volume in volumes:
        mount_point = volume.mount_point
        destination = (
            mount_point in destinations
            if mount_point is not None and destinations is not None
            else None
        )
        excluded = exclusions.get(mount_point) if exclusions is not None and mount_point else None
        time_machine_evidence: tuple[Evidence, ...] = ()
        if destination is not None or excluded is not None:
            time_machine_evidence = (
                Evidence(
                    kind="time_machine_volume_metadata",
                    value={
                        "configured_destination": destination,
                        "excluded": excluded,
                        "role": volume.time_machine_role,
                    },
                    source="tmutil destinationinfo -X; tmutil isexcluded",
                    collected_at=collected_at,
                    reliability=Reliability.HIGH,
                    limitations=(
                        "Volume evidence does not prove backup coverage for individual paths.",
                    ),
                ),
            )
        enriched_volumes.append(
            volume.model_copy(
                update={
                    "time_machine_destination": destination,
                    "time_machine_excluded": excluded,
                    "evidence": (*volume.evidence, *time_machine_evidence),
                }
            )
        )

    enriched_volumes.sort(key=lambda volume: volume.device_identifier)
    return StorageCollection(
        volumes=tuple(enriched_volumes),
        status=CollectorStatus(
            collector="storage",
            state=CollectorState.COMPLETE if not limitations else CollectorState.PARTIAL,
            collected_at=collected_at,
            records_count=len(enriched_volumes),
            limitations=tuple(limitations),
        ),
    )


def resolve_storage_location(
    path: Path,
    volumes: Sequence[VolumeRecord],
) -> StorageLocation:
    """Classify a path by its longest known mount-point prefix."""
    absolute_path = Path(os.path.abspath(path))
    matches: list[tuple[int, VolumeRecord]] = []
    for volume in volumes:
        if volume.mount_point is None:
            continue
        mount_point = Path(os.path.abspath(volume.mount_point))
        if absolute_path == mount_point or mount_point in absolute_path.parents:
            matches.append((len(mount_point.parts), volume))
    if not matches:
        return StorageLocation.UNKNOWN
    _, best_match = max(matches, key=lambda match: match[0])
    if best_match.mount_point == "/" and absolute_path.parts[1:2] in {("Volumes",), ("Network",)}:
        return StorageLocation.UNKNOWN
    return best_match.location
