import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

import macwise.cli as cli
from macwise.models import AuditDocument

runner = CliRunner()


class FakeAuditService:
    def __init__(self, audit: AuditDocument) -> None:
        self.audit = audit
        self.roots: tuple[Path, ...] | None = None
        self.project_roots: tuple[Path, ...] | None = None

    def run(
        self,
        application_roots: tuple[Path, ...],
        *,
        project_roots: tuple[Path, ...] = (),
    ) -> AuditDocument:
        self.roots = tuple(application_roots)
        self.project_roots = tuple(project_roots)
        return self.audit


@pytest.mark.parametrize("output_format", ("json", "markdown", "terminal"))
def test_scan_supports_all_public_formats(
    output_format: str,
    sample_audit: AuditDocument,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = FakeAuditService(sample_audit)
    monkeypatch.setattr(cli, "_service_factory", lambda: service)

    result = runner.invoke(cli.app, ["scan", "--format", output_format])

    assert result.exit_code == 0, result.stdout
    assert service.roots is not None
    if output_format == "json":
        assert json.loads(result.stdout)["schema_version"] == 3
    else:
        assert "MacWise Audit" in result.stdout
        assert "Example App" in result.stdout


def test_scan_appends_only_explicit_deduplicated_application_roots(
    tmp_path: Path,
    sample_audit: AuditDocument,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = FakeAuditService(sample_audit)
    monkeypatch.setattr(cli, "_service_factory", lambda: service)
    approved = tmp_path / "External Apps"

    result = runner.invoke(
        cli.app,
        ["scan", "--app-root", str(approved), "--app-root", str(approved)],
    )

    assert result.exit_code == 0, result.stdout
    roots = service.roots
    assert roots is not None
    assert roots == (
        Path("/Applications"),
        Path.home() / "Applications",
        approved,
    )
    assert all(root != Path("/Volumes") for root in roots)


def test_scan_passes_only_explicit_deduplicated_project_roots(
    tmp_path: Path,
    sample_audit: AuditDocument,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = FakeAuditService(sample_audit)
    monkeypatch.setattr(cli, "_service_factory", lambda: service)
    approved = tmp_path / "approved-project"

    result = runner.invoke(
        cli.app,
        ["scan", "--project-root", str(approved), "--project-root", str(approved)],
    )

    assert result.exit_code == 0, result.stdout
    project_roots = service.project_roots
    assert project_roots == (approved,)
    assert project_roots is not None
    assert Path.home() not in project_roots


def test_scan_writes_only_to_an_explicit_new_output_file(
    tmp_path: Path,
    sample_audit: AuditDocument,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "_service_factory", lambda: FakeAuditService(sample_audit))
    output = tmp_path / "audit.json"

    result = runner.invoke(
        cli.app,
        ["scan", "--format", "json", "--output", str(output)],
    )

    assert result.exit_code == 0
    assert "Saved the read-only audit" in result.stdout
    assert AuditDocument.model_validate_json(output.read_text(encoding="utf-8")) == sample_audit

    second = runner.invoke(
        cli.app,
        ["scan", "--format", "json", "--output", str(output)],
    )
    assert second.exit_code != 0
    assert "already exists" in second.stdout
    assert "--force" in second.stdout


def test_scan_force_explicitly_allows_replacing_an_audit_file(
    tmp_path: Path,
    sample_audit: AuditDocument,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli, "_service_factory", lambda: FakeAuditService(sample_audit))
    output = tmp_path / "audit.md"
    output.write_text("old", encoding="utf-8")

    result = runner.invoke(
        cli.app,
        ["scan", "--format", "markdown", "--output", str(output), "--force"],
    )

    assert result.exit_code == 0
    assert output.read_text(encoding="utf-8").startswith("# MacWise Audit")


@pytest.mark.parametrize("command", (("apply",), ("undo",), ("setup", "codex")))
def test_unavailable_mutating_or_setup_commands_refuse_safely(command: tuple[str, ...]) -> None:
    result = runner.invoke(cli.app, list(command))

    assert result.exit_code == 2
    assert "No changes were made." in result.stdout
    assert "Next:" in result.stdout
