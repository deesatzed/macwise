from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from macwise.collectors.usage import collect_usage, parse_spotlight_last_used
from macwise.models import CollectorState, EntityType, SoftwareRecord, StorageLocation
from macwise.system import CommandResult, CommandState, ReadCommand

COLLECTED_AT = datetime(2026, 7, 17, 22, 0, tzinfo=UTC)


def application(
    *,
    identifier: str = "org.example.safe",
    display_name: str = "Example",
    install_path: str = "/Applications/Example.app",
) -> SoftwareRecord:
    return SoftwareRecord(
        id="application:example",
        entity_type=EntityType.APPLICATION,
        name="Example",
        display_name=display_name,
        identifier=identifier,
        install_path=install_path,
    )


def test_parses_spotlight_last_used_dates_and_preserves_null_as_unknown() -> None:
    assert parse_spotlight_last_used("2026-07-01 12:34:56 +0000\n") == datetime(
        2026, 7, 1, 12, 34, 56, tzinfo=UTC
    )
    assert parse_spotlight_last_used('"2026-07-01 12:34:56 +0000"') == datetime(
        2026, 7, 1, 12, 34, 56, tzinfo=UTC
    )
    assert parse_spotlight_last_used("(null)\n") is None
    assert parse_spotlight_last_used("not a date") is None


def test_collects_last_use_and_bounded_related_paths_without_following_symlinks(
    tmp_path: Path,
) -> None:
    library = tmp_path / "Library"
    support = library / "Application Support" / "Example"
    cache = library / "Caches" / "org.example.safe"
    preference = library / "Preferences" / "org.example.safe.plist"
    container = library / "Containers" / "org.example.safe"
    for directory in (support, cache, container):
        directory.mkdir(parents=True)
        (directory / "data.bin").write_bytes(b"synthetic related data")
    preference.parent.mkdir(parents=True)
    preference.write_bytes(b"synthetic preference")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "private.bin").write_bytes(b"must not be measured")
    (support / "linked-outside").symlink_to(outside, target_is_directory=True)
    calls: list[tuple[ReadCommand, tuple[str, ...]]] = []

    def runner(command: ReadCommand, arguments: Sequence[str] = ()) -> CommandResult:
        calls.append((command, tuple(arguments)))
        return CommandResult(
            command=command,
            state=CommandState.COMPLETE,
            stdout="2026-07-01 12:34:56 +0000\n",
            stderr="",
            return_code=0,
            duration_seconds=0.01,
        )

    result = collect_usage(
        (application(),),
        home_library=library,
        collected_at=COLLECTED_AT,
        storage_resolver=lambda _path: StorageLocation.EXTERNAL,
        runner=runner,
    )

    assert result.status.state is CollectorState.COMPLETE
    assert result.signals[0].subject_id == "application:example"
    assert result.signals[0].last_used_at == datetime(2026, 7, 1, 12, 34, 56, tzinfo=UTC)
    assert {item.kind for item in result.signals[0].evidence} == {"spotlight_last_used"}
    assert {item.kind for item in result.path_evidence} == {
        "application_support",
        "cache",
        "container",
        "preferences",
    }
    assert all(item.size_bytes is not None and item.size_bytes > 0 for item in result.path_evidence)
    assert all(item.storage_location is StorageLocation.EXTERNAL for item in result.path_evidence)
    assert (
        sum(item.size_bytes or 0 for item in result.path_evidence) < outside.stat().st_size + 10_000
    )
    assert calls == [
        (
            ReadCommand.MDLS,
            ("-name", "kMDItemLastUsedDate", "-raw", "/Applications/Example.app"),
        )
    ]


def test_failures_and_unsafe_identifiers_degrade_without_escaping_library(tmp_path: Path) -> None:
    library = tmp_path / "Library"
    (library / "Application Support" / "Example").mkdir(parents=True)

    def failing_runner(command: ReadCommand, arguments: Sequence[str] = ()) -> CommandResult:
        del arguments
        return CommandResult(
            command=command,
            state=CommandState.FAILED,
            stdout="",
            stderr="synthetic unavailable metadata",
            return_code=1,
            duration_seconds=0.01,
            limitations=("Spotlight metadata is unavailable.",),
        )

    result = collect_usage(
        (application(identifier="../../escape", display_name="../Escape"),),
        home_library=library,
        collected_at=COLLECTED_AT,
        runner=failing_runner,
    )

    assert result.signals[0].last_used_at is None
    assert result.path_evidence == ()
    assert result.status.state is CollectorState.PARTIAL
    assert "Spotlight metadata is unavailable." in result.status.limitations
    assert any("unsafe bundle identifier" in item for item in result.status.limitations)
    assert any("unsafe application name" in item for item in result.status.limitations)
