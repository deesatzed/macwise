from pathlib import Path

ROOT = Path(__file__).parents[2]
CANONICAL = ROOT / "skills" / "macwise" / "references" / "workflows.md"
PACKAGED = (
    ROOT
    / "src"
    / "macwise"
    / "codex_payload"
    / "macwise"
    / "skills"
    / "macwise"
    / "references"
    / "workflows.md"
)


def test_ai_overlap_workflow_uses_typed_local_evidence_in_required_order() -> None:
    workflow = CANONICAL.read_text(encoding="utf-8")
    section = workflow.split("## Explain AI-app overlap", maxsplit=1)[1].split("##", maxsplit=1)[0]

    assert section.index("`audit_mac`") < section.index("`find_overlaps`")
    assert section.index("`find_overlaps`") < section.index("`inspect_software`")
    assert "actually use" in section.casefold()
    assert "no reliable use evidence" in section.casefold()
    assert "verified facts" in section.casefold()
    assert "unknowns" in section.casefold()


def test_cleanup_workflow_routes_every_state_change_to_standalone_cli() -> None:
    workflow = CANONICAL.read_text(encoding="utf-8")
    section = workflow.split("## Cleanup question", maxsplit=1)[1]

    assert "`get_removal_preview`" in section
    assert "`macwise plan`" in section
    assert "`macwise apply`" in section
    assert "never generate" in section.casefold()
    assert "fingerprint" in section.casefold()


def test_workflow_reference_is_identical_in_packaged_skill() -> None:
    assert CANONICAL.read_bytes() == PACKAGED.read_bytes()
