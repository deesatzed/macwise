from datetime import UTC, datetime
from pathlib import Path
from shutil import copytree

from macwise.collectors.applications import collect_applications
from macwise.models import CollectorState, EntityType, StorageLocation

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
