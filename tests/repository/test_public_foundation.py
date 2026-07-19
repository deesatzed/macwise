import json
import re
import socket
import subprocess
import tarfile
import tomllib
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).parents[2]


class LocalLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in {"a", "link"}:
            return
        attribute = "href"
        for name, value in attrs:
            if name == attribute and value:
                self.links.append(value)


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
        "docs/getting-started.md",
        "docs/demo.md",
        "docs/scorecard-evaluation.md",
        "docs/simple-ux-acceptance.md",
        "docs/index.html",
        "docs/assets/macwise.css",
        "docs/release-checklist.md",
        "skills/macwise/SKILL.md",
        "skills/macwise/agents/openai.yaml",
        ".github/workflows/ci.yml",
        ".github/workflows/release.yml",
        ".github/workflows/public-install-smoke.yml",
        "scripts/verify_public_release.py",
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
    assert readme.index("uv tool install macwise") < readme.index("pipx install macwise")
    assert "brew install deesatzed/tap/macwise" not in readme
    assert "macwise setup codex" in readme
    assert "macwise review apps" in readme
    assert "macwise scan --format json" in readme
    assert "not yet published" in readme.lower()
    assert "homebrew distribution is deferred" in readme.lower()
    assert "setup codex` still refuses" not in readme
    assert "not enabled in the current" not in readme
    assert "1.0.0rc1" in readme
    assert "hosted ci passes" in readme.lower()
    assert "not yet published to pypi" in readme.lower()
    assert "docs/index.html" in readme
    assert "how macwise knows" in readme.lower()
    assert "opportunity profile" in readme.lower()
    assert "macwise usefulness score" in readme.lower()
    assert "does not grade this mac" in readme.lower()
    assert "does not prove personalized correctness" in readme.lower()
    assert "1. Check up this Mac (Recommended)" in readme
    assert "macwise checkup" in readme
    assert "`uv` is a tool that installs" in readme.lower()
    assert "fresh evidence" in readme.lower()


def test_landing_page_has_launch_content_without_remote_assets_or_scripts() -> None:
    page = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")

    for required in (
        "Understand what is installed on your Mac",
        "uv tool install macwise",
        "Read-only by default",
        "How MacWise knows",
        "1.0.0rc1",
        "Hosted CI passes",
        "Review opportunities found",
        "Confidence in this report",
        "does not grade this Mac",
        "does not prove personalized correctness",
    ):
        assert required in page
    assert "Check up this Mac (Recommended)" in page
    assert "macwise checkup" in page
    assert '<meta name="viewport"' in page
    assert "<main" in page
    assert "<script" not in page.lower()
    assert "http://" not in page
    parser = LocalLinkParser()
    parser.feed(page)
    assert not any(urlparse(link).scheme in {"http", "https"} for link in parser.links)


def test_public_entry_points_have_no_broken_local_links() -> None:
    markdown_files = (ROOT / "README.md", ROOT / "docs" / "getting-started.md")
    html_file = ROOT / "docs" / "index.html"
    links: list[tuple[Path, str]] = []

    markdown_link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for source in markdown_files:
        for target in markdown_link_pattern.findall(source.read_text(encoding="utf-8")):
            links.append((source, target))

    parser = LocalLinkParser()
    parser.feed(html_file.read_text(encoding="utf-8"))
    links.extend((html_file, target) for target in parser.links)

    missing: list[str] = []
    for source, target in links:
        parsed = urlparse(target)
        if parsed.scheme or parsed.netloc or target.startswith(("#", "mailto:")):
            continue
        path = unquote(parsed.path)
        resolved = (source.parent / path).resolve()
        if not resolved.exists():
            missing.append(f"{source.relative_to(ROOT)} -> {target}")

    assert not missing, f"Broken local public links: {missing}"


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


def test_release_sdist_excludes_development_and_local_control_surfaces(tmp_path: Path) -> None:
    subprocess.run(
        ("uv", "build", "--sdist", "--out-dir", str(tmp_path)),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    sdist = next(tmp_path.glob("macwise-1.0.0rc1.tar.gz"))
    with tarfile.open(sdist) as archive:
        names = archive.getnames()

    assert any(name.endswith("/src/macwise/cli.py") for name in names)
    assert not any(
        part in name
        for name in names
        for part in ("/tests/", "/docs/plans/", "/packaging/", "/PROGRESS.md", "/GOAL.md")
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
