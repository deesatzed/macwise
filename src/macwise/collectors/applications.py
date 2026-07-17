"""Read-only collection of macOS application bundle metadata."""

import os
import plistlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol, cast

from macwise.models import (
    CollectorState,
    CollectorStatus,
    EntityType,
    Evidence,
    Reliability,
    SoftwareRecord,
    StorageLocation,
    stable_software_id,
)
from macwise.system import CommandResult, CommandState, ReadCommand, run_read_command

StorageResolver = Callable[[Path], StorageLocation]


class ApplicationRunner(Protocol):
    """The narrow command boundary used for host-only application metadata."""

    def __call__(
        self,
        command: ReadCommand,
        arguments: Sequence[str] = (),
        /,
    ) -> CommandResult: ...


@dataclass(frozen=True, slots=True)
class ApplicationCollection:
    """Application records and the limitations that qualify them."""

    software: tuple[SoftwareRecord, ...]
    status: CollectorStatus


def _unknown_storage(_path: Path) -> StorageLocation:
    return StorageLocation.UNKNOWN


def _string_value(metadata: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _bundle_size(app_path: Path) -> int:
    """Return lstat size without traversing symlinked directories."""
    total = app_path.lstat().st_size
    for current_root, directories, files in os.walk(app_path, followlinks=False):
        root = Path(current_root)
        retained_directories: list[str] = []
        for directory in directories:
            child = root / directory
            total += child.lstat().st_size
            if not child.is_symlink():
                retained_directories.append(directory)
        directories[:] = retained_directories
        for filename in files:
            total += (root / filename).lstat().st_size
    return total


def _bundle_components(app_path: Path) -> tuple[str, ...]:
    """List nested helper/extension bundles without following symlinks."""
    component_suffixes = {".app", ".appex", ".bundle", ".plugin", ".xpc"}
    components: list[str] = []
    for current_root, directories, _files in os.walk(app_path, followlinks=False):
        root = Path(current_root)
        retained: list[str] = []
        for directory in sorted(directories, key=str.casefold):
            candidate = root / directory
            if candidate.is_symlink():
                continue
            if candidate.suffix.casefold() in component_suffixes:
                components.append(candidate.relative_to(app_path).as_posix())
                continue
            retained.append(directory)
        directories[:] = retained
    return tuple(sorted(components, key=str.casefold))


def is_protected_application(app_path: Path) -> bool:
    """Return whether an app is inside Apple's protected system hierarchy."""
    absolute = Path(os.path.abspath(app_path))
    return absolute == Path("/System") or Path("/System") in absolute.parents


def _installation_source(app_path: Path, protected: bool) -> str | None:
    if protected:
        return "apple_system"
    receipt = app_path / "Contents" / "_MASReceipt" / "receipt"
    return "mac_app_store" if receipt.is_file() and not receipt.is_symlink() else None


def _collect_application(
    app_path: Path,
    *,
    collected_at: datetime,
    storage_resolver: StorageResolver,
) -> tuple[SoftwareRecord, tuple[str, ...]]:
    limitations: list[str] = []
    metadata: dict[str, Any] = {}
    plist_path = app_path / "Contents" / "Info.plist"
    if not plist_path.is_file():
        limitations.append(f"The application bundle {app_path} does not contain Info.plist.")
    else:
        try:
            loaded = plistlib.loads(plist_path.read_bytes())
            if isinstance(loaded, dict):
                metadata = cast(dict[str, Any], loaded)
            else:
                limitations.append(f"The application bundle {app_path} metadata could not be read.")
        except (OSError, plistlib.InvalidFileException, ValueError):
            limitations.append(f"The application bundle {app_path} metadata could not be read.")

    bundle_name = app_path.stem
    display_name = _string_value(metadata, "CFBundleDisplayName", "CFBundleName") or bundle_name
    identifier = _string_value(metadata, "CFBundleIdentifier")
    version = _string_value(metadata, "CFBundleShortVersionString", "CFBundleVersion")
    protected = is_protected_application(app_path)
    install_source = _installation_source(app_path, protected)

    try:
        size_bytes = _bundle_size(app_path)
    except OSError:
        size_bytes = None
        limitations.append(f"The application bundle {app_path} size could not be measured.")

    try:
        storage_location = storage_resolver(app_path)
    except OSError:
        storage_location = StorageLocation.UNKNOWN
        limitations.append(f"The application bundle {app_path} storage location is unavailable.")

    try:
        components = _bundle_components(app_path)
    except OSError:
        components = ()
        limitations.append(f"The application bundle {app_path} components could not be read.")

    evidence: list[Evidence] = []
    if metadata:
        evidence.append(
            Evidence(
                kind="application_bundle_metadata",
                value={
                    "bundle_id": identifier,
                    "display_name": display_name,
                    "version": version,
                },
                source=str(plist_path),
                collected_at=collected_at,
                reliability=Reliability.HIGH,
            )
        )
    if size_bytes is not None:
        evidence.append(
            Evidence(
                kind="application_bundle_size",
                value=size_bytes,
                source="filesystem metadata",
                collected_at=collected_at,
                reliability=Reliability.HIGH,
                limitations=("Includes the app bundle only, not related user data.",),
            )
        )
    if components:
        evidence.append(
            Evidence(
                kind="application_components",
                value=list(components),
                source="application bundle layout",
                collected_at=collected_at,
                reliability=Reliability.HIGH,
            )
        )

    resolved_path = str(app_path.resolve(strict=False))
    canonical_key = f"{identifier}\0{resolved_path}" if identifier else resolved_path
    return (
        SoftwareRecord(
            id=stable_software_id(EntityType.APPLICATION, canonical_key),
            entity_type=EntityType.APPLICATION,
            name=bundle_name,
            display_name=display_name,
            identifier=identifier,
            version=version,
            install_path=str(app_path),
            install_source=install_source,
            size_bytes=size_bytes,
            components=components,
            storage_location=storage_location,
            protected=protected,
            evidence=tuple(evidence),
        ),
        tuple(limitations),
    )


def _find_application_bundles(root: Path, limitations: list[str]) -> tuple[Path, ...]:
    app_paths: list[Path] = []

    def record_walk_error(error: OSError) -> None:
        affected_path = error.filename or str(root)
        limitations.append(f"The application folder {affected_path} could not be read.")

    for current_root, directories, _files in os.walk(
        root,
        topdown=True,
        followlinks=False,
        onerror=record_walk_error,
    ):
        current_path = Path(current_root)
        retained_directories: list[str] = []
        for directory in sorted(directories, key=str.casefold):
            candidate = current_path / directory
            if candidate.is_symlink():
                continue
            if candidate.suffix.casefold() == ".app" and candidate.is_dir():
                app_paths.append(candidate)
                continue
            retained_directories.append(directory)
        directories[:] = retained_directories
    return tuple(app_paths)


def collect_applications(
    roots: Sequence[Path],
    *,
    collected_at: datetime,
    storage_resolver: StorageResolver = _unknown_storage,
) -> ApplicationCollection:
    """Collect `.app` bundles within approved roots without entering bundles."""
    records: list[SoftwareRecord] = []
    limitations: list[str] = []

    for root in sorted(roots, key=lambda path: str(path).casefold()):
        if root.is_symlink() or not root.is_dir():
            limitations.append(f"The configured application folder {root} is not available.")
            continue
        for app_path in _find_application_bundles(root, limitations):
            record, item_limitations = _collect_application(
                app_path,
                collected_at=collected_at,
                storage_resolver=storage_resolver,
            )
            records.append(record)
            limitations.extend(item_limitations)

    state = CollectorState.COMPLETE if not limitations else CollectorState.PARTIAL
    return ApplicationCollection(
        software=tuple(records),
        status=CollectorStatus(
            collector="applications",
            state=state,
            collected_at=collected_at,
            records_count=len(records),
            limitations=tuple(limitations),
        ),
    )


def _key_values(text: str) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for line in text.splitlines():
        key, separator, value = line.partition("=")
        if separator and key.strip() and value.strip():
            values.setdefault(key.strip(), []).append(value.strip())
    return values


def _publisher_from_signing_identity(identity: str) -> str:
    prefixes = (
        "Developer ID Application: ",
        "Apple Development: ",
        "Apple Distribution: ",
        "3rd Party Mac Developer Application: ",
    )
    publisher = identity
    for prefix in prefixes:
        if publisher.startswith(prefix):
            publisher = publisher.removeprefix(prefix)
            break
    before_team, separator, _team = publisher.rpartition(" (")
    return before_team if separator and publisher.endswith(")") else publisher


def _architectures(text: str) -> tuple[str, ...]:
    value = text.strip()
    if " are: " in value:
        value = value.rsplit(" are: ", 1)[1]
    elif " architecture: " in value:
        value = value.rsplit(" architecture: ", 1)[1]
    supported_tokens = {"arm64", "arm64e", "i386", "ppc", "ppc64", "x86_64"}
    return tuple(sorted({token for token in value.split() if token in supported_tokens}))


def _safe_executable_path(app_path: Path, metadata: dict[str, Any]) -> Path | None:
    executable_name = _string_value(metadata, "CFBundleExecutable")
    if (
        executable_name is None
        or Path(executable_name).name != executable_name
        or "/" in executable_name
        or "\\" in executable_name
    ):
        return None
    executable = app_path / "Contents" / "MacOS" / executable_name
    if executable.is_symlink() or not executable.is_file():
        return None
    return executable


def _plist_metadata(app_path: Path) -> dict[str, Any]:
    try:
        loaded = plistlib.loads((app_path / "Contents" / "Info.plist").read_bytes())
    except (OSError, plistlib.InvalidFileException, ValueError):
        return {}
    return cast(dict[str, Any], loaded) if isinstance(loaded, dict) else {}


def collect_host_applications(
    roots: Sequence[Path],
    *,
    collected_at: datetime,
    storage_resolver: StorageResolver = _unknown_storage,
    runner: ApplicationRunner = run_read_command,
) -> ApplicationCollection:
    """Collect bundles and enrich them with bounded read-only host metadata."""
    base = collect_applications(
        roots,
        collected_at=collected_at,
        storage_resolver=storage_resolver,
    )
    limitations = list(base.status.limitations)
    process_result = runner(ReadCommand.PS, ("-axo", "comm="))
    process_paths: set[str] | None
    if process_result.state is CommandState.COMPLETE:
        process_paths = {
            line.strip() for line in process_result.stdout.splitlines() if line.strip()
        }
        limitations.extend(process_result.limitations)
    else:
        process_paths = None
        limitations.extend(
            process_result.limitations or ("The ps process metadata is unavailable.",)
        )

    records: list[SoftwareRecord] = []
    for record in base.software:
        if record.install_path is None:
            records.append(record)
            continue
        app_path = Path(record.install_path)
        metadata = _plist_metadata(app_path)
        executable = _safe_executable_path(app_path, metadata)
        item_evidence = list(record.evidence)

        codesign = runner(ReadCommand.CODESIGN, ("-dv", "--verbose=4", str(app_path)))
        publisher: str | None = None
        signing_identity: str | None = None
        team_identifier: str | None = None
        if codesign.state is CommandState.COMPLETE:
            signing_values = _key_values(f"{codesign.stdout}\n{codesign.stderr}")
            authorities = signing_values.get("Authority", [])
            signing_identity = authorities[0] if authorities else None
            publisher = (
                _publisher_from_signing_identity(signing_identity)
                if signing_identity is not None
                else None
            )
            team_values = signing_values.get("TeamIdentifier", [])
            team_identifier = team_values[0] if team_values else None
            if signing_identity is None:
                limitations.append(f"Signing identity for {app_path} is unavailable.")
            else:
                item_evidence.append(
                    Evidence(
                        kind="application_signing",
                        value={
                            "publisher": publisher,
                            "signing_identity": signing_identity,
                            "team_identifier": team_identifier,
                        },
                        source=f"codesign -dv --verbose=4 {app_path}",
                        collected_at=collected_at,
                        reliability=Reliability.HIGH,
                    )
                )
            limitations.extend(codesign.limitations)
        else:
            limitations.extend(
                codesign.limitations or (f"Signing metadata for {app_path} is unavailable.",)
            )

        architecture_values: tuple[str, ...] = ()
        if executable is None:
            limitations.append(f"Executable metadata for {app_path} is unavailable.")
        else:
            lipo = runner(ReadCommand.LIPO, ("-archs", str(executable)))
            if lipo.state is CommandState.COMPLETE:
                architecture_values = _architectures(lipo.stdout)
                if architecture_values:
                    item_evidence.append(
                        Evidence(
                            kind="application_architecture",
                            value=list(architecture_values),
                            source=f"lipo -archs {executable}",
                            collected_at=collected_at,
                            reliability=Reliability.HIGH,
                        )
                    )
                else:
                    limitations.append(f"Architecture metadata for {app_path} is unavailable.")
                limitations.extend(lipo.limitations)
            else:
                limitations.extend(
                    lipo.limitations or (f"Architecture metadata for {app_path} is unavailable.",)
                )

        running = (
            None
            if process_paths is None or executable is None
            else str(executable) in process_paths
        )
        if running is not None:
            item_evidence.append(
                Evidence(
                    kind="application_process_state",
                    value=running,
                    source="ps -axo comm=",
                    collected_at=collected_at,
                    reliability=Reliability.HIGH,
                    limitations=("This is a point-in-time process snapshot.",),
                )
            )

        records.append(
            record.model_copy(
                update={
                    "publisher": publisher,
                    "signing_identity": signing_identity,
                    "team_identifier": team_identifier,
                    "architectures": architecture_values,
                    "running": running,
                    "evidence": tuple(item_evidence),
                }
            )
        )

    return ApplicationCollection(
        software=tuple(records),
        status=base.status.model_copy(
            update={
                "state": CollectorState.COMPLETE if not limitations else CollectorState.PARTIAL,
                "limitations": tuple(limitations),
            }
        ),
    )
