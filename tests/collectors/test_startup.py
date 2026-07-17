from datetime import UTC, datetime
from pathlib import Path

from macwise.collectors.startup import StartupRoot, collect_startup, parse_launch_plist
from macwise.models import (
    CollectorState,
    EntityType,
    SoftwareRecord,
    StartupKind,
)

COLLECTED_AT = datetime(2026, 7, 17, 23, 0, tzinfo=UTC)
FIXTURES = Path(__file__).parents[1] / "fixtures" / "startup"


def test_parses_launch_plist_without_claiming_unverified_enabled_state() -> None:
    agent = parse_launch_plist(
        (FIXTURES / "agent.plist").read_bytes(),
        source_path=Path("/Library/LaunchAgents/org.example.safe.agent.plist"),
        kind=StartupKind.LAUNCH_AGENT,
        collected_at=COLLECTED_AT,
    )
    daemon = parse_launch_plist(
        (FIXTURES / "daemon.plist").read_bytes(),
        source_path=Path("/Library/LaunchDaemons/org.example.daemon.plist"),
        kind=StartupKind.LAUNCH_DAEMON,
        collected_at=COLLECTED_AT,
    )

    assert agent.label == "org.example.safe.agent"
    assert agent.program == "/Applications/Example.app/Contents/MacOS/Example"
    assert agent.bundle_identifier == "org.example.safe"
    assert agent.enabled is None
    assert agent.running is None
    assert daemon.enabled is False
    assert daemon.program == "/Library/PrivilegedHelperTools/org.example.daemon"


def test_collects_launch_items_and_homebrew_services_with_conservative_owners(
    tmp_path: Path,
) -> None:
    agents = tmp_path / "LaunchAgents"
    daemons = tmp_path / "LaunchDaemons"
    agents.mkdir()
    daemons.mkdir()
    (agents / "org.example.safe.agent.plist").write_bytes((FIXTURES / "agent.plist").read_bytes())
    (daemons / "org.example.daemon.plist").write_bytes((FIXTURES / "daemon.plist").read_bytes())
    (agents / "broken.plist").write_text("not a plist", encoding="utf-8")
    (agents / "linked.plist").symlink_to(FIXTURES / "agent.plist")
    app = SoftwareRecord(
        id="application:example",
        entity_type=EntityType.APPLICATION,
        name="Example",
        display_name="Example",
        identifier="org.example.safe",
        install_path="/Applications/Example.app",
    )
    formula = SoftwareRecord(
        id="homebrew_formula:postgres",
        entity_type=EntityType.HOMEBREW_FORMULA,
        name="postgresql@16",
        display_name="postgresql@16",
        service_status="started",
    )

    result = collect_startup(
        (app, formula),
        roots=(
            StartupRoot(StartupKind.LAUNCH_AGENT, agents),
            StartupRoot(StartupKind.LAUNCH_DAEMON, daemons),
        ),
        collected_at=COLLECTED_AT,
    )

    assert result.status.state is CollectorState.PARTIAL
    assert result.status.records_count == 3
    records = {record.label: record for record in result.startup}
    agent = records["org.example.safe.agent"]
    assert agent.owner_software_ids == (app.id,)
    assert agent.kind is StartupKind.LAUNCH_AGENT
    daemon = records["org.example.daemon"]
    assert daemon.owner_software_ids == ()
    assert daemon.enabled is False
    service = records["postgresql@16"]
    assert service.kind is StartupKind.HOMEBREW_SERVICE
    assert service.owner_software_ids == (formula.id,)
    assert service.running is True
    assert any("could not be read" in item for item in result.status.limitations)
    assert any("symbolic link" in item for item in result.status.limitations)


def test_program_path_traversal_does_not_create_a_false_owner(tmp_path: Path) -> None:
    agents = tmp_path / "LaunchAgents"
    agents.mkdir()
    hostile = """<?xml version="1.0" encoding="UTF-8"?>
    <plist version="1.0"><dict>
      <key>Label</key><string>org.example.hostile</string>
      <key>Program</key><string>/Applications/Example.app/../Other.app/tool</string>
    </dict></plist>"""
    (agents / "hostile.plist").write_text(hostile, encoding="utf-8")
    app = SoftwareRecord(
        id="application:example",
        entity_type=EntityType.APPLICATION,
        name="Example",
        display_name="Example",
        install_path="/Applications/Example.app",
    )

    result = collect_startup(
        (app,),
        roots=(StartupRoot(StartupKind.LAUNCH_AGENT, agents),),
        collected_at=COLLECTED_AT,
    )

    assert result.startup[0].owner_software_ids == ()
