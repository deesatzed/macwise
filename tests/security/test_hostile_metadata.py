import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

import macwise.cli as cli
from macwise.collectors.applications import collect_host_applications
from macwise.collectors.homebrew import parse_homebrew_inventory
from macwise.collectors.storage import parse_volume_info
from macwise.models import (
    AuditDocument,
    CatalogAssessment,
    ClaimBasis,
    CollectorState,
    CollectorStatus,
    EntityType,
    GuardedRecommendation,
    LearningValue,
    RecommendationAction,
    Reliability,
    SoftwareRecord,
)
from macwise.reporting import render_json, render_markdown
from macwise.system import CommandResult, CommandState, ReadCommand

COLLECTED_AT = datetime(2026, 7, 17, 20, 0, tzinfo=UTC)
FIXTURES = Path(__file__).parents[1] / "fixtures" / "security"
RUNNER = CliRunner()


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_hostile_parsers_preserve_data_without_escaping_approved_paths(tmp_path: Path) -> None:
    root = tmp_path / "Applications"
    app_path = root / "Hostile.app"
    (app_path / "Contents").mkdir(parents=True)
    (app_path / "Contents" / "Info.plist").write_text(
        fixture_text("hostile-app.plist"),
        encoding="utf-8",
    )
    outside = tmp_path / "outside-tool"
    outside.write_text("must not run", encoding="utf-8")
    calls: list[tuple[ReadCommand, tuple[str, ...]]] = []

    def runner(command: ReadCommand, arguments: Sequence[str] = ()) -> CommandResult:
        calls.append((command, tuple(arguments)))
        return CommandResult(
            command=command,
            state=CommandState.COMPLETE,
            stdout="",
            stderr="Authority=Developer ID Application: Synthetic (TEAM123456)\n",
            return_code=0,
            duration_seconds=0.01,
        )

    applications = collect_host_applications(
        (root,),
        collected_at=COLLECTED_AT,
        runner=runner,
    )
    cellar = tmp_path / "Cellar"
    cellar.mkdir()
    homebrew = parse_homebrew_inventory(
        formulae_json=fixture_text("hostile-homebrew.json"),
        casks_json='{"formulae": [], "casks": []}',
        leaves_text="../../escape\n",
        services_json="[]",
        collected_at=COLLECTED_AT,
        cellar_root=cellar,
    )
    volume = parse_volume_info(fixture_text("hostile-disk.plist"), collected_at=COLLECTED_AT)

    assert applications.software[0].display_name.startswith("Visible App\n")
    assert all(command is not ReadCommand.LIPO for command, _arguments in calls)
    assert all(str(outside) not in arguments for _command, arguments in calls)
    assert homebrew.software[0].install_path is None
    assert homebrew.software[0].description is not None
    assert "Ignore previous instructions" in homebrew.software[0].description
    assert homebrew.status.state is CollectorState.PARTIAL
    assert volume.name.startswith("Archive\n")
    assert volume.device_identifier == "disk9s1"


def hostile_audit(tmp_path: Path) -> AuditDocument:
    values = json.loads(fixture_text("hostile-values.json"))
    record = SoftwareRecord(
        id="application:hostile",
        entity_type=EntityType.APPLICATION,
        name=f"$(touch {tmp_path / 'marker'})",
        display_name=values["display_name"],
        version=values["markup"],
        install_path=f"/Applications/{values['markup']}.app",
        description=values["prompt"],
        caveats=values["shell"],
    )
    volume = parse_volume_info(fixture_text("hostile-disk.plist"), collected_at=COLLECTED_AT)
    return AuditDocument(
        audit_id="audit:hostile",
        collected_at=COLLECTED_AT,
        software=(record,),
        volumes=(volume,),
        collectors=(
            CollectorStatus(
                collector="security-fixture",
                state=CollectorState.COMPLETE,
                collected_at=COLLECTED_AT,
                records_count=2,
            ),
        ),
        catalog_assessments=(
            CatalogAssessment(
                subject_id=record.id,
                catalog_key="hostile-fixture",
                catalog_version="test",
                catalog_source="synthetic catalog",
                roles=(values["display_name"],),
                learning_value=LearningValue.UNKNOWN,
                learning_statement=values["prompt"],
                basis=ClaimBasis.INFERRED,
                confidence=Reliability.LOW,
            ),
        ),
        recommendations=(
            GuardedRecommendation(
                id="recommendation:hostile",
                subject_ids=(record.id,),
                action=RecommendationAction.NO_RECOMMENDATION,
                statement=values["display_name"],
                basis=ClaimBasis.UNKNOWN,
                confidence=Reliability.UNKNOWN,
                limitations=(values["markup"],),
            ),
        ),
    )


def test_json_preserves_raw_evidence_but_markdown_cannot_forge_structure(tmp_path: Path) -> None:
    audit = hostile_audit(tmp_path)
    raw = render_json(audit)
    report = render_markdown(audit)

    assert "\\n## Forged heading" in raw
    assert AuditDocument.model_validate_json(raw) == audit
    assert "\x1b" not in report
    assert "\u202e" not in report
    assert "\n## Forged heading" not in report
    assert "\n## Forged storage section" not in report
    assert "\n- **Injected record**" not in report
    assert "\n- **Injected volume**" not in report
    assert [line for line in report.splitlines() if line.startswith("## ")] == [
        "## Verified inventory",
        "## Evidence-linked findings",
        "## Startup and background items",
        "## Related data measurements",
        "## Backup facts",
        "## Catalog role assessments",
        "## Role-aware overlaps",
        "## Guarded recommendations",
        "## Collection limitations",
        "## Unknown in this phase",
    ]


def test_cli_matching_treats_hostile_query_and_metadata_as_inert_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    audit = hostile_audit(tmp_path)

    class Service:
        def run(
            self,
            application_roots: Sequence[Path],
            *,
            project_roots: Sequence[Path] = (),
        ) -> AuditDocument:
            del application_roots, project_roots
            return audit

    monkeypatch.setattr(cli, "_service_factory", Service)
    query = audit.software[0].name
    result = RUNNER.invoke(cli.app, ["explain", query])

    assert result.exit_code == 0, result.stdout
    assert not (tmp_path / "marker").exists()
    assert "\x1b" not in result.stdout
    assert "\u202e" not in result.stdout
    assert "\n## Forged heading" not in result.stdout
    assert "Ignore previous instructions" in result.stdout


def test_skill_contract_rejects_prompt_shaped_evidence_as_instructions() -> None:
    skill = (Path(__file__).parents[2] / "skills" / "macwise" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    normalized = skill.casefold()

    assert "prompt-shaped" in normalized
    assert "never instructions" in normalized
    assert "shell or action input" in normalized
