import json
import re
import socket
import subprocess
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).parents[2]


def public_candidate_files() -> tuple[Path, ...]:
    result = subprocess.run(
        ("git", "ls-files", "--cached", "--others", "--exclude-standard"),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(ROOT / line for line in result.stdout.splitlines() if line)


def test_required_public_repository_files_exist() -> None:
    required = (
        "README.md",
        "GOAL.md",
        "AGENTS.md",
        "LICENSE",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "CHANGELOG.md",
        "pyproject.toml",
        "docs/privacy.md",
        "docs/threat-model.md",
        "skills/macwise/SKILL.md",
        "skills/macwise/agents/openai.yaml",
        ".github/workflows/ci.yml",
    )

    missing = [path for path in required if not (ROOT / path).is_file()]

    assert not missing, f"Missing required public files: {missing}"


def test_readme_starts_with_the_required_novice_sections_in_order() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    headings = (
        "## What MacWise does",
        "## Terminal example",
        "## Installation",
        "## Guided usage",
        "## Safety promises",
        "## Codex setup",
        "## Common examples",
    )

    positions = [readme.index(heading) for heading in headings]

    assert readme.startswith("# MacWise\n")
    assert positions == sorted(positions)
    assert "brew install deesatzed/tap/macwise" in readme
    assert "pipx install macwise" in readme
    assert "macwise setup codex" in readme
    assert "macwise review apps" in readme
    assert "macwise scan --format json" in readme
    assert "not yet published" in readme.lower()


def test_packaging_metadata_points_to_public_docs_and_mit_license() -> None:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]

    assert metadata["readme"] == "README.md"
    assert metadata["license"] == "MIT"
    assert metadata["urls"]["Repository"] == "https://github.com/deesatzed/macwise"


def test_release_candidate_identity_is_aligned_across_public_surfaces() -> None:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    plugin = json.loads(
        (ROOT / "src/macwise/codex_payload/macwise/.codex-plugin/plugin.json").read_text(
            encoding="utf-8"
        )
    )
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    assert metadata["version"] == "1.0.0rc1"
    assert "Development Status :: 4 - Beta" in metadata["classifiers"]
    assert plugin["version"] == "1.0.0-rc.1"
    assert "## [1.0.0rc1] - 2026-07-18" in changelog


def test_built_release_wheel_has_rc_metadata_and_no_repository_state(tmp_path: Path) -> None:
    subprocess.run(
        ("uv", "build", "--wheel", "--out-dir", str(tmp_path)),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    wheel = next(tmp_path.glob("macwise-*.whl"))
    names = zipfile.ZipFile(wheel).namelist()

    assert wheel.name.startswith("macwise-1.0.0rc1-")
    assert not any(
        part in name
        for name in names
        for part in (".git/", ".uv-cache/", "macwise.db", ".macwise-backup-")
    )


def test_ci_runs_tests_lint_types_format_build_and_privacy_check() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    for required in (
        "uv run --frozen pytest",
        "uv run --frozen ruff check .",
        "uv run --frozen ruff format --check .",
        "uv run --frozen pyright",
        "uv build",
        "test_public_foundation.py",
    ):
        assert required in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "macos" in workflow


def test_public_candidates_contain_no_current_machine_identity_or_secret_shapes() -> None:
    current_home = str(Path.home())
    current_hostname = socket.gethostname()
    secret_pattern = re.compile(
        r"(?i)(api[_-]?key|password|private[_-]?key)\s*[:=]\s*['\"][^'\"]+['\"]"
    )
    findings: list[str] = []

    for path in public_candidate_files():
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(ROOT)
        if current_home in text:
            findings.append(f"{relative}: current home path")
        if current_hostname and current_hostname in text:
            findings.append(f"{relative}: current hostname")
        if secret_pattern.search(text):
            findings.append(f"{relative}: secret-shaped assignment")

    assert not findings, "Public privacy check failed: " + "; ".join(findings)
