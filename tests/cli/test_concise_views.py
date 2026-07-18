from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

import macwise.cli as cli
from macwise.models import (
    AuditDocument,
    BackupStatus,
    EntityType,
    PathEvidence,
    SoftwareRecord,
    StartupKind,
    StartupRecord,
    StorageLocation,
    stable_software_id,
)

RUNNER = CliRunner()


class StaticAuditService:
    def __init__(self, audit: AuditDocument) -> None:
        self.audit = audit

    def run(self, application_roots: tuple[Path, ...]) -> AuditDocument:
        assert application_roots
        return self.audit


def expanded_audit(base: AuditDocument) -> AuditDocument:
    applications = tuple(
        SoftwareRecord(
            id=stable_software_id(EntityType.APPLICATION, f"org.example.app-{index:02d}"),
            entity_type=EntityType.APPLICATION,
            name=f"App {index:02d}",
            display_name=f"App {index:02d}",
            install_path=f"/Applications/App {index:02d}.app",
            size_bytes=(index + 1) * 1024**3,
            storage_location=StorageLocation.INTERNAL,
        )
        for index in range(25)
    )
    formulae = tuple(
        SoftwareRecord(
            id=stable_software_id(EntityType.HOMEBREW_FORMULA, f"formula-{index:02d}"),
            entity_type=EntityType.HOMEBREW_FORMULA,
            name=f"formula-{index:02d}",
            display_name=f"Formula {index:02d}",
        )
        for index in range(25)
    )
    startup = tuple(
        StartupRecord(
            id=f"startup:{index:02d}",
            label=f"org.example.agent-{index:02d}",
            kind=StartupKind.LAUNCH_AGENT,
        )
        for index in range(25)
    )
    paths = tuple(
        PathEvidence(
            id=f"path:{index:02d}",
            subject_id=applications[index].id,
            path=f"/Users/example/Library/Application Support/App {index:02d}",
            kind="application_support",
            backup_excluded=False,
        )
        for index in range(25)
    )
    return base.model_copy(
        update={
            "software": (*applications, *formulae),
            "startup": startup,
            "path_evidence": paths,
            "backup": BackupStatus(
                configured=True,
                available_destination_volume_ids=(base.volumes[0].id,),
                last_backup_at=datetime(2026, 6, 30, 12, 24, 1, tzinfo=UTC),
            ),
        }
    )


@pytest.fixture
def concise_cli(sample_audit: AuditDocument, monkeypatch: pytest.MonkeyPatch) -> AuditDocument:
    audit = expanded_audit(sample_audit)
    monkeypatch.setattr(cli, "_service_factory", lambda: StaticAuditService(audit))
    monkeypatch.setattr(
        cli,
        "_now",
        lambda: datetime(2026, 7, 18, 12, 0, tzinfo=UTC),
        raising=False,
    )
    return audit


@pytest.mark.parametrize(
    ("command", "hidden_text", "recovery"),
    [
        (["review", "brew"], "Formula 24", "macwise review brew --all"),
        (["startup"], "org.example.agent-24", "macwise startup --all"),
        (["review", "unknown"], "App 24", "macwise review unknown --all"),
    ],
)
def test_long_views_are_bounded_and_name_the_full_detail_command(
    concise_cli: AuditDocument,
    command: list[str],
    hidden_text: str,
    recovery: str,
) -> None:
    del concise_cli
    result = RUNNER.invoke(cli.app, command)

    assert result.exit_code == 0, result.stdout
    assert hidden_text not in result.stdout
    assert recovery in result.stdout

    full = RUNNER.invoke(cli.app, [*command, "--all"])
    assert full.exit_code == 0, full.stdout
    assert hidden_text in full.stdout


def test_largest_view_is_bounded_and_uses_readable_sizes(
    concise_cli: AuditDocument,
) -> None:
    del concise_cli
    result = RUNNER.invoke(cli.app, ["review", "largest"])

    assert result.exit_code == 0, result.stdout
    assert "25.0 GiB" in result.stdout
    assert "- App 00: 1.0 GiB" not in result.stdout
    assert "macwise review largest --all" in result.stdout

    full = RUNNER.invoke(cli.app, ["review", "largest", "--all"])
    assert full.exit_code == 0, full.stdout
    assert "- App 00: 1.0 GiB" in full.stdout


def test_backups_default_prioritizes_age_and_hides_path_observations(
    concise_cli: AuditDocument,
) -> None:
    del concise_cli
    result = RUNNER.invoke(cli.app, ["backups"])

    assert result.exit_code == 0, result.stdout
    assert "18 days ago" in result.stdout
    assert "This backup evidence may be stale" in result.stdout
    assert "/Users/example/Library/Application Support" not in result.stdout
    assert "macwise backups --all" in result.stdout

    full = RUNNER.invoke(cli.app, ["backups", "--all"])
    assert full.exit_code == 0, full.stdout
    assert "/Users/example/Library/Application Support/App 24" in full.stdout
