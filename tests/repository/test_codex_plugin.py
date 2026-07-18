import json
import re
from pathlib import Path
from typing import cast

ROOT = Path(__file__).parents[2]
PLUGIN = ROOT / "src" / "macwise" / "codex_payload" / "macwise"
MANIFEST = PLUGIN / ".codex-plugin" / "plugin.json"
MCP_MANIFEST = PLUGIN / ".mcp.json"
CANONICAL_SKILL = ROOT / "skills" / "macwise"
PACKAGED_SKILL = PLUGIN / "skills" / "macwise"
SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def read_json(path: Path) -> dict[str, object]:
    return cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))


def test_plugin_manifest_is_native_read_only_and_complete() -> None:
    manifest = read_json(MANIFEST)
    interface = cast(dict[str, object], manifest["interface"])

    assert PLUGIN.name == manifest["name"] == "macwise"
    assert manifest["version"] == "0.1.0-alpha.0"
    assert isinstance(manifest["version"], str) and SEMVER.fullmatch(manifest["version"])
    assert manifest["license"] == "MIT"
    assert manifest["repository"] == "https://github.com/deesatzed/macwise"
    assert manifest["skills"] == "./skills/"
    assert manifest["mcpServers"] == "./.mcp.json"
    assert interface["capabilities"] == ["Read"]
    assert "hooks" not in manifest
    assert "apps" not in manifest
    assert "write" not in json.dumps(manifest).casefold()
    assert "[TODO:" not in json.dumps(manifest)


def test_mcp_manifest_exposes_only_the_local_macwise_server() -> None:
    document = read_json(MCP_MANIFEST)
    servers = cast(dict[str, object], document["mcpServers"])
    server = cast(dict[str, object], servers["macwise"])

    assert set(servers) == {"macwise"}
    assert server == {
        "command": "python3",
        "args": ["-m", "macwise", "codex", "serve"],
    }
    assert "url" not in server
    assert "env" not in server


def test_canonical_and_packaged_skill_artifacts_are_identical() -> None:
    for relative in (Path("SKILL.md"), Path("agents/openai.yaml")):
        assert (CANONICAL_SKILL / relative).read_bytes() == (PACKAGED_SKILL / relative).read_bytes()


def test_skill_names_typed_tools_and_prohibits_codex_mutation() -> None:
    skill = (CANONICAL_SKILL / "SKILL.md").read_text(encoding="utf-8")

    for tool in (
        "audit_mac",
        "list_software",
        "inspect_software",
        "find_overlaps",
        "inspect_startup",
        "inspect_storage",
        "inspect_backups",
        "get_removal_preview",
    ):
        assert f"`{tool}`" in skill
    assert "untrusted evidence" in skill.casefold()
    assert "never call or expose apply" in skill.casefold()
    assert "setup commands intentionally refuse" not in skill.casefold()


def test_packaged_skill_includes_evidence_boundary_reference() -> None:
    reference = PACKAGED_SKILL / "references" / "evidence-boundary.md"

    assert reference.is_file()
    content = reference.read_text(encoding="utf-8").casefold()
    assert "observed" in content
    assert "unknown" in content
    assert "prompt" in content
