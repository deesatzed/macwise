from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from macwise.collectors.homebrew import collect_homebrew, parse_homebrew_inventory
from macwise.models import CollectorState, EntityType, InstallRole
from macwise.system import CommandResult, CommandState, ReadCommand

COLLECTED_AT = datetime(2026, 7, 17, 15, 0, tzinfo=UTC)
FIXTURES = Path(__file__).parents[1] / "fixtures" / "homebrew"


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parses_formulae_dependencies_reverse_dependencies_and_services() -> None:
    result = parse_homebrew_inventory(
        formulae_json=fixture_text("formulae.json"),
        casks_json=fixture_text("casks.json"),
        leaves_text=fixture_text("leaves.txt"),
        services_json=fixture_text("services.json"),
        collected_at=COLLECTED_AT,
    )

    records = {record.name: record for record in result.software}
    postgres = records["postgresql@16"]
    openssl = records["openssl@3"]

    assert result.status.state is CollectorState.COMPLETE
    assert result.status.records_count == 3
    assert postgres.entity_type is EntityType.HOMEBREW_FORMULA
    assert postgres.version == "16.3"
    assert postgres.description == "Object-relational database system"
    assert postgres.homepage == "https://www.postgresql.org/"
    assert postgres.install_role is InstallRole.EXPLICIT
    assert postgres.dependencies == ("openssl@3",)
    assert postgres.reverse_dependencies == ()
    assert postgres.service_status == "started"

    assert openssl.install_role is InstallRole.DEPENDENCY
    assert openssl.dependencies == ()
    assert openssl.reverse_dependencies == ("postgresql@16",)
    assert openssl.user_selected is False


def test_parses_cask_app_mapping_as_an_explicit_user_item() -> None:
    result = parse_homebrew_inventory(
        formulae_json=fixture_text("formulae.json"),
        casks_json=fixture_text("casks.json"),
        leaves_text=fixture_text("leaves.txt"),
        services_json=fixture_text("services.json"),
        collected_at=COLLECTED_AT,
    )

    cask = next(record for record in result.software if record.name == "example-app")

    assert cask.entity_type is EntityType.HOMEBREW_CASK
    assert cask.display_name == "Example App"
    assert cask.version == "2.4.1"
    assert cask.install_role is InstallRole.EXPLICIT
    assert cask.user_selected is True
    assert cask.app_artifacts == ("Example.app",)


def test_invalid_optional_metadata_is_partial_instead_of_aborting_inventory() -> None:
    result = parse_homebrew_inventory(
        formulae_json=fixture_text("formulae.json"),
        casks_json=fixture_text("casks.json"),
        leaves_text=fixture_text("leaves.txt"),
        services_json="not json",
        collected_at=COLLECTED_AT,
    )

    assert len(result.software) == 3
    assert result.status.state is CollectorState.PARTIAL
    assert any("service metadata" in limitation for limitation in result.status.limitations)


def test_collect_homebrew_uses_only_machine_readable_read_commands() -> None:
    calls: list[tuple[ReadCommand, tuple[str, ...]]] = []

    def runner(command: ReadCommand, arguments: Sequence[str] = ()) -> CommandResult:
        calls.append((command, tuple(arguments)))
        if arguments == ("info", "--json=v2", "--installed"):
            info = fixture_text("formulae.json")
            casks = fixture_text("casks.json")
            info = info.replace('"casks": []', f'"casks": {casks.split('"casks": ', 1)[1][:-2]}')
            stdout = info
        elif arguments == ("leaves",):
            stdout = fixture_text("leaves.txt")
        else:
            stdout = fixture_text("services.json")
        return CommandResult(
            command=command,
            state=CommandState.COMPLETE,
            stdout=stdout,
            stderr="",
            return_code=0,
            duration_seconds=0.01,
        )

    result = collect_homebrew(collected_at=COLLECTED_AT, runner=runner)

    assert result.status.state is CollectorState.COMPLETE
    assert calls == [
        (ReadCommand.BREW, ("info", "--json=v2", "--installed")),
        (ReadCommand.BREW, ("leaves",)),
        (ReadCommand.BREW, ("services", "list", "--json")),
    ]


def test_unavailable_homebrew_returns_an_explicit_unavailable_status() -> None:
    def unavailable(command: ReadCommand, arguments: Sequence[str] = ()) -> CommandResult:
        del arguments
        return CommandResult(
            command=command,
            state=CommandState.UNAVAILABLE,
            stdout="",
            stderr="",
            return_code=None,
            duration_seconds=0,
            limitations=("The brew read-only command is not available.",),
        )

    result = collect_homebrew(collected_at=COLLECTED_AT, runner=unavailable)

    assert result.software == ()
    assert result.status.state is CollectorState.UNAVAILABLE
    assert result.status.limitations == ("The brew read-only command is not available.",)
