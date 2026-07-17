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


def test_collect_homebrew_uses_only_machine_readable_read_commands(tmp_path: Path) -> None:
    calls: list[tuple[ReadCommand, tuple[str, ...]]] = []
    prefix = tmp_path / "homebrew"
    cellar = prefix / "Cellar"
    caskroom = prefix / "Caskroom"
    project = tmp_path / "approved-project"
    for path in (
        cellar / "postgresql@16",
        cellar / "openssl@3",
        caskroom / "example-app",
        project,
    ):
        path.mkdir(parents=True)
    (project / "Brewfile").write_text('brew "postgresql@16"\n', encoding="utf-8")

    def runner(command: ReadCommand, arguments: Sequence[str] = ()) -> CommandResult:
        calls.append((command, tuple(arguments)))
        if arguments == ("info", "--json=v2", "--installed"):
            info = fixture_text("formulae.json")
            casks = fixture_text("casks.json")
            info = info.replace('"casks": []', f'"casks": {casks.split('"casks": ', 1)[1][:-2]}')
            stdout = info
        elif arguments == ("leaves",):
            stdout = fixture_text("leaves.txt")
        elif arguments == ("services", "list", "--json"):
            stdout = fixture_text("services.json")
        elif arguments == ("--prefix",):
            stdout = f"{prefix}\n"
        elif arguments == ("--cellar",):
            stdout = f"{cellar}\n"
        elif arguments == ("--caskroom",):
            stdout = f"{caskroom}\n"
        else:
            raise AssertionError(arguments)
        return CommandResult(
            command=command,
            state=CommandState.COMPLETE,
            stdout=stdout,
            stderr="",
            return_code=0,
            duration_seconds=0.01,
        )

    result = collect_homebrew(
        collected_at=COLLECTED_AT,
        runner=runner,
        project_roots=(project,),
    )

    assert result.status.state is CollectorState.COMPLETE
    assert calls == [
        (ReadCommand.BREW, ("info", "--json=v2", "--installed")),
        (ReadCommand.BREW, ("leaves",)),
        (ReadCommand.BREW, ("services", "list", "--json")),
        (ReadCommand.BREW, ("--prefix",)),
        (ReadCommand.BREW, ("--cellar",)),
        (ReadCommand.BREW, ("--caskroom",)),
    ]
    records = {record.name: record for record in result.software}
    assert records["postgresql@16"].install_path == str(cellar / "postgresql@16")
    assert records["postgresql@16"].project_references == ("Brewfile",)


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


def test_info_output_limitation_marks_an_otherwise_parseable_inventory_partial() -> None:
    def limited(command: ReadCommand, arguments: Sequence[str] = ()) -> CommandResult:
        if arguments == ("info", "--json=v2", "--installed"):
            stdout = fixture_text("formulae.json")
            limitations = ("Command output was truncated.",)
        elif arguments == ("leaves",):
            stdout = fixture_text("leaves.txt")
            limitations = ()
        else:
            stdout = fixture_text("services.json")
            limitations = ()
        return CommandResult(
            command=command,
            state=CommandState.COMPLETE,
            stdout=stdout,
            stderr="",
            return_code=0,
            duration_seconds=0.01,
            limitations=limitations,
        )

    result = collect_homebrew(collected_at=COLLECTED_AT, runner=limited)

    assert result.status.state is CollectorState.PARTIAL
    assert "Command output was truncated." in result.status.limitations


def test_enriches_installation_size_executables_state_caveats_and_project_references(
    tmp_path: Path,
) -> None:
    cellar = tmp_path / "Cellar"
    caskroom = tmp_path / "Caskroom"
    project = tmp_path / "sample-project"
    psql = cellar / "postgresql@16" / "16.3" / "bin" / "psql"
    openssl = cellar / "openssl@3" / "3.3.1" / "bin" / "openssl"
    cask_payload = caskroom / "example-app" / "2.4.1" / "Example.app" / "payload"
    for path in (psql, openssl, cask_payload):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"synthetic installed payload")
    project.mkdir()
    (project / "Brewfile").write_text(
        'brew "postgresql@16"\ncask "example-app"\n',
        encoding="utf-8",
    )

    result = parse_homebrew_inventory(
        formulae_json=fixture_text("formulae.json"),
        casks_json=fixture_text("casks.json"),
        leaves_text=fixture_text("leaves.txt"),
        services_json=fixture_text("services.json"),
        collected_at=COLLECTED_AT,
        cellar_root=cellar,
        caskroom_root=caskroom,
        project_roots=(project,),
    )

    records = {record.name: record for record in result.software}
    postgres = records["postgresql@16"]
    dependency = records["openssl@3"]
    cask = records["example-app"]
    assert result.status.state is CollectorState.COMPLETE
    assert postgres.install_path == str(cellar / "postgresql@16")
    assert postgres.size_bytes is not None and postgres.size_bytes > 0
    assert postgres.executables == ("psql",)
    assert postgres.linked is True
    assert postgres.pinned is False
    assert postgres.caveats == "A synthetic database caveat."
    assert postgres.project_references == ("Brewfile",)
    assert dependency.executables == ("openssl",)
    assert dependency.linked is False
    assert dependency.pinned is True
    assert dependency.project_references == ()
    assert cask.install_path == str(caskroom / "example-app")
    assert cask.size_bytes is not None and cask.size_bytes > 0
    assert cask.executables == ("example-cli",)
    assert cask.pinned is True
    assert cask.caveats == "A synthetic application caveat."
    assert cask.project_references == ("Brewfile",)


def test_install_roots_reject_traversal_names_and_symlink_directories(tmp_path: Path) -> None:
    cellar = tmp_path / "Cellar"
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret").write_text("not inventory", encoding="utf-8")
    cellar.mkdir()
    (cellar / "linked").symlink_to(outside, target_is_directory=True)
    formulae = """{
      "formulae": [
        {"name": "../../outside", "installed": [{"version": "1"}]},
        {"name": "linked", "installed": [{"version": "1"}]}
      ],
      "casks": []
    }"""

    result = parse_homebrew_inventory(
        formulae_json=formulae,
        casks_json='{"formulae": [], "casks": []}',
        leaves_text="",
        services_json="[]",
        collected_at=COLLECTED_AT,
        cellar_root=cellar,
    )

    records = {record.name: record for record in result.software}
    assert records["../../outside"].install_path is None
    assert records["../../outside"].size_bytes is None
    assert records["linked"].install_path is None
    assert records["linked"].size_bytes is None
    assert result.status.state is CollectorState.PARTIAL
    assert any("unsafe installed path" in item for item in result.status.limitations)
    assert any("symbolic link" in item for item in result.status.limitations)
