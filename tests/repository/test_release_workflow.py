import re
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[2]
WORKFLOW = ROOT / ".github/workflows/release.yml"
CI_WORKFLOW = ROOT / ".github/workflows/ci.yml"
PUBLIC_SMOKE_WORKFLOW = ROOT / ".github/workflows/public-install-smoke.yml"


def test_release_workflow_is_exact_tag_gated_and_version_checked() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)

    assert workflow[True]["push"]["tags"] == ["v1.0.0rc*"]
    assert 'test "$GITHUB_REF_NAME" = "v$VERSION"' in text
    assert "^1\\.0\\.0rc[0-9]+$" in text
    assert "workflow_dispatch" not in text


def test_release_workflow_uses_least_privilege_trusted_publishing_and_pins_actions() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)

    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["jobs"]["publish-pypi"]["permissions"] == {"id-token": "write"}
    assert workflow["jobs"]["release"]["permissions"] == {"contents": "write"}
    for forbidden in ("pass" + "word:", "api" + "-token"):
        assert forbidden not in text.casefold()
    action_refs = re.findall(r"uses:\s*[^@\s]+@([^\s#]+)", text)
    assert action_refs
    assert all(re.fullmatch(r"[0-9a-f]{40}", reference) for reference in action_refs)


def test_release_workflow_builds_once_checks_artifacts_and_releases_after_pypi() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)

    assert text.count("uv build") == 1
    assert "twine check dist/*" in text
    assert "sha256sum dist/*" in text
    assert workflow["jobs"]["release"]["needs"] == ["build", "publish-pypi"]
    assert "prerelease: true" in text


def test_ci_has_ephemeral_macos_homebrew_candidate_install_proof() -> None:
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)
    job = workflow["jobs"]["homebrew-candidate"]

    assert job["runs-on"] == "macos-15"
    assert "brew audit --strict" in text
    assert "brew install --build-from-source" in text
    assert "brew test" in text
    assert "uv build --sdist" in text
    assert "file://" in text
    assert "brew uninstall" in text


def test_public_install_smoke_requires_manual_version_and_tests_both_channels() -> None:
    text = PUBLIC_SMOKE_WORKFLOW.read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)

    assert "workflow_dispatch" in text
    assert workflow["permissions"] == {"contents": "read"}
    assert "pipx install" in text
    assert "brew install deesatzed/tap/macwise" in text
    assert "macwise setup codex --help" in text
    assert "macwise --version" in text
    assert 'python3 scripts/verify_public_release.py "$VERSION"' in text
    assert workflow["jobs"]["cross-channel-identity"]["needs"] == ["pipx", "homebrew"]


def test_every_release_related_action_is_commit_pinned() -> None:
    for path in (CI_WORKFLOW, WORKFLOW, PUBLIC_SMOKE_WORKFLOW):
        references = re.findall(r"uses:\s*[^@\s]+@([^\s#]+)", path.read_text(encoding="utf-8"))
        assert references
        assert all(re.fullmatch(r"[0-9a-f]{40}", reference) for reference in references)
