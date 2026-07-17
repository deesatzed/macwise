from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from shutil import copytree

from macwise.collectors.applications import collect_applications, collect_host_applications
from macwise.models import CollectorState, EntityType, StorageLocation
from macwise.system import CommandResult, CommandState, ReadCommand

COLLECTED_AT = datetime(2026, 7, 17, 14, 0, tzinfo=UTC)
FIXTURE_APP = Path(__file__).parents[1] / "fixtures" / "apps" / "Example.app"


def test_collects_bundle_metadata_size_and_volume_location(tmp_path: Path) -> None:
    applications_root = tmp_path / "Applications"
    app_path = applications_root / "Example.app"
    copytree(FIXTURE_APP, app_path)

    result = collect_applications(
        (applications_root,),
        collected_at=COLLECTED_AT,
        storage_resolver=lambda _path: StorageLocation.EXTERNAL,
    )

    assert result.status.state is CollectorState.COMPLETE
    assert result.status.records_count == 1
    record = result.software[0]
    assert record.entity_type is EntityType.APPLICATION
    assert record.name == "Example"
    assert record.display_name == "Example"
    assert record.identifier == "org.example.safe-app"
    assert record.version == "2.4.1"
    assert record.install_path == str(app_path)
    assert record.size_bytes is not None and record.size_bytes > 0
    assert record.storage_location is StorageLocation.EXTERNAL
    assert record.id.startswith("application:")
    assert {evidence.kind for evidence in record.evidence} == {
        "application_bundle_metadata",
        "application_bundle_size",
    }


def test_same_bundle_identifier_at_two_paths_keeps_distinct_instance_ids(
    tmp_path: Path,
) -> None:
    primary_root = tmp_path / "Applications"
    secondary_root = tmp_path / "External Applications"
    copytree(FIXTURE_APP, primary_root / "Example.app")
    copytree(FIXTURE_APP, secondary_root / "Example.app")

    result = collect_applications(
        (primary_root, secondary_root),
        collected_at=COLLECTED_AT,
    )

    assert len(result.software) == 2
    assert {record.identifier for record in result.software} == {"org.example.safe-app"}
    assert len({record.id for record in result.software}) == 2


def test_malformed_and_missing_plists_become_partial_limitations(tmp_path: Path) -> None:
    applications_root = tmp_path / "Applications"
    malformed = applications_root / "Broken.app" / "Contents"
    missing = applications_root / "Unknown.app" / "Contents"
    malformed.mkdir(parents=True)
    missing.mkdir(parents=True)
    (malformed / "Info.plist").write_text("not a plist", encoding="utf-8")

    result = collect_applications((applications_root,), collected_at=COLLECTED_AT)

    assert result.status.state is CollectorState.PARTIAL
    assert result.status.records_count == 2
    assert {record.display_name for record in result.software} == {"Broken", "Unknown"}
    assert any("could not be read" in limitation for limitation in result.status.limitations)
    assert any(
        "does not contain Info.plist" in limitation for limitation in result.status.limitations
    )


def test_collector_never_executes_bundle_programs_or_follows_app_symlinks(
    tmp_path: Path,
) -> None:
    applications_root = tmp_path / "Applications"
    app_path = applications_root / "Example.app"
    copytree(FIXTURE_APP, app_path)
    marker = tmp_path / "executed.txt"
    executable = app_path / "Contents" / "MacOS" / "ExampleExecutable"
    executable.parent.mkdir()
    executable.write_text(f"#!/bin/sh\ntouch {marker}\n", encoding="utf-8")
    executable.chmod(0o755)

    outside_app = tmp_path / "Outside.app"
    copytree(FIXTURE_APP, outside_app)
    (applications_root / "Linked.app").symlink_to(outside_app, target_is_directory=True)

    result = collect_applications((applications_root,), collected_at=COLLECTED_AT)

    assert not marker.exists()
    assert [record.display_name for record in result.software] == ["Example"]


def test_collects_apps_nested_in_ordinary_subfolders(tmp_path: Path) -> None:
    applications_root = tmp_path / "Applications"
    nested_app = applications_root / "Vendor" / "Example.app"
    copytree(FIXTURE_APP, nested_app)

    result = collect_applications((applications_root,), collected_at=COLLECTED_AT)

    assert [record.install_path for record in result.software] == [str(nested_app)]


def test_storage_resolver_failure_preserves_unknown_location(tmp_path: Path) -> None:
    applications_root = tmp_path / "Applications"
    copytree(FIXTURE_APP, applications_root / "Example.app")

    def unavailable_storage(_path: Path) -> StorageLocation:
        raise OSError("volume metadata unavailable")

    result = collect_applications(
        (applications_root,),
        collected_at=COLLECTED_AT,
        storage_resolver=unavailable_storage,
    )

    assert result.status.state is CollectorState.PARTIAL
    assert result.software[0].storage_location is StorageLocation.UNKNOWN
    assert any("storage location" in limitation for limitation in result.status.limitations)


def test_missing_configured_root_is_reported_without_crashing(tmp_path: Path) -> None:
    missing_root = tmp_path / "Applications"

    def resolver(_path: Path) -> StorageLocation:
        return StorageLocation.INTERNAL

    result = collect_applications(
        (missing_root,),
        collected_at=COLLECTED_AT,
        storage_resolver=resolver,
    )

    assert result.software == ()
    assert result.status.state is CollectorState.PARTIAL
    assert result.status.limitations == (
        f"The configured application folder {missing_root} is not available.",
    )


def test_host_collection_enriches_signing_architecture_process_components_and_source(
    tmp_path: Path,
) -> None:
    applications_root = tmp_path / "Applications"
    app_path = applications_root / "Example.app"
    copytree(FIXTURE_APP, app_path)
    executable = app_path / "Contents" / "MacOS" / "ExampleExecutable"
    executable.parent.mkdir()
    executable.write_bytes(b"synthetic universal executable")
    (app_path / "Contents" / "PlugIns" / "Share.appex").mkdir(parents=True)
    (app_path / "Contents" / "XPCServices" / "Worker.xpc").mkdir(parents=True)
    (app_path / "Contents" / "Library" / "LoginItems" / "Helper.app").mkdir(parents=True)
    receipt = app_path / "Contents" / "_MASReceipt" / "receipt"
    receipt.parent.mkdir()
    receipt.write_bytes(b"synthetic receipt")
    calls: list[tuple[ReadCommand, tuple[str, ...]]] = []

    def runner(command: ReadCommand, arguments: Sequence[str] = ()) -> CommandResult:
        calls.append((command, tuple(arguments)))
        stdout = ""
        stderr = ""
        if command is ReadCommand.PS:
            stdout = f"{executable}\n"
        elif command is ReadCommand.CODESIGN:
            stderr = "\n".join(
                (
                    "Identifier=org.example.safe-app",
                    "Authority=Developer ID Application: Example Corp (TEAM123456)",
                    "Authority=Developer ID Certification Authority",
                    "TeamIdentifier=TEAM123456",
                )
            )
        elif command is ReadCommand.LIPO:
            stdout = f"Architectures in the fat file: {executable} are: x86_64 arm64\n"
        return CommandResult(
            command=command,
            state=CommandState.COMPLETE,
            stdout=stdout,
            stderr=stderr,
            return_code=0,
            duration_seconds=0.01,
        )

    result = collect_host_applications(
        (applications_root,),
        collected_at=COLLECTED_AT,
        runner=runner,
    )

    assert result.status.state is CollectorState.COMPLETE
    record = result.software[0]
    assert record.publisher == "Example Corp"
    assert record.signing_identity == "Developer ID Application: Example Corp (TEAM123456)"
    assert record.team_identifier == "TEAM123456"
    assert record.architectures == ("arm64", "x86_64")
    assert record.running is True
    assert record.components == (
        "Contents/Library/LoginItems/Helper.app",
        "Contents/PlugIns/Share.appex",
        "Contents/XPCServices/Worker.xpc",
    )
    assert record.install_source == "mac_app_store"
    assert record.protected is False
    assert {item.kind for item in record.evidence}.issuperset(
        {
            "application_architecture",
            "application_components",
            "application_process_state",
            "application_signing",
        }
    )
    assert calls == [
        (ReadCommand.PS, ("-axo", "comm=")),
        (ReadCommand.CODESIGN, ("-dv", "--verbose=4", str(app_path))),
        (ReadCommand.LIPO, ("-archs", str(executable))),
    ]


def test_failed_host_metadata_stays_unknown_and_marks_collection_partial(tmp_path: Path) -> None:
    applications_root = tmp_path / "Applications"
    app_path = applications_root / "Example.app"
    copytree(FIXTURE_APP, app_path)
    executable = app_path / "Contents" / "MacOS" / "ExampleExecutable"
    executable.parent.mkdir()
    executable.write_bytes(b"synthetic executable")

    def failing_runner(command: ReadCommand, arguments: Sequence[str] = ()) -> CommandResult:
        del arguments
        return CommandResult(
            command=command,
            state=CommandState.FAILED,
            stdout="",
            stderr="synthetic failure",
            return_code=1,
            duration_seconds=0.01,
            limitations=(f"The {command.value} metadata is unavailable.",),
        )

    result = collect_host_applications(
        (applications_root,),
        collected_at=COLLECTED_AT,
        runner=failing_runner,
    )

    record = result.software[0]
    assert result.status.state is CollectorState.PARTIAL
    assert record.publisher is None
    assert record.signing_identity is None
    assert record.architectures == ()
    assert record.running is None
    assert any("ps metadata" in item for item in result.status.limitations)
    assert any("codesign metadata" in item for item in result.status.limitations)
    assert any("lipo metadata" in item for item in result.status.limitations)


def test_process_evidence_requires_an_exact_executable_path(tmp_path: Path) -> None:
    applications_root = tmp_path / "Applications"
    app_path = applications_root / "Example.app"
    copytree(FIXTURE_APP, app_path)
    executable = app_path / "Contents" / "MacOS" / "ExampleExecutable"
    executable.parent.mkdir()
    executable.write_bytes(b"synthetic executable")

    def runner(command: ReadCommand, arguments: Sequence[str] = ()) -> CommandResult:
        del arguments
        return CommandResult(
            command=command,
            state=CommandState.COMPLETE,
            stdout=f"{executable}-different\n" if command is ReadCommand.PS else "arm64\n",
            stderr=(
                "Authority=Apple Development: Example Corp (TEAM123456)\n"
                "TeamIdentifier=TEAM123456\n"
                if command is ReadCommand.CODESIGN
                else ""
            ),
            return_code=0,
            duration_seconds=0.01,
        )

    result = collect_host_applications(
        (applications_root,),
        collected_at=COLLECTED_AT,
        runner=runner,
    )

    assert result.software[0].running is False


def test_system_application_paths_are_marked_protected() -> None:
    from macwise.collectors.applications import is_protected_application

    assert is_protected_application(Path("/System/Applications/Safari.app")) is True
    assert is_protected_application(Path("/Applications/Example.app")) is False
