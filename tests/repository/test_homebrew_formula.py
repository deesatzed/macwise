import hashlib
import re
import subprocess
import tomllib
from pathlib import Path

from packaging.markers import Marker

ROOT = Path(__file__).parents[2]
FORMULA = ROOT / "packaging/homebrew/Formula/macwise.rb"


def production_resources() -> dict[str, tuple[str, str]]:
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    packages = {package["name"]: package for package in lock["package"]}
    environment = {
        "python_full_version": "3.13.0",
        "python_version": "3.13",
        "sys_platform": "darwin",
        "platform_system": "Darwin",
        "implementation_name": "cpython",
        "platform_python_implementation": "CPython",
        "os_name": "posix",
        "platform_machine": "arm64",
    }
    requested_names = {"macwise"}
    seen_states: set[tuple[str, frozenset[str]]] = set()
    pending = [("macwise", frozenset[str]())]
    while pending:
        name, extras = pending.pop()
        state = (name, extras)
        if state in seen_states:
            continue
        seen_states.add(state)
        package = packages[name]
        dependencies = list(package.get("dependencies", []))
        for extra in extras:
            dependencies.extend(package.get("optional-dependencies", {}).get(extra, []))
        for dependency in dependencies:
            marker = dependency.get("marker")
            if marker and not Marker(marker).evaluate(environment):
                continue
            dependency_name = dependency["name"]
            dependency_extras = frozenset(dependency.get("extra", []))
            requested_names.add(dependency_name)
            pending.append((dependency_name, dependency_extras))
    return {
        name: (
            packages[name]["sdist"]["url"],
            packages[name]["sdist"]["hash"].removeprefix("sha256:"),
        )
        for name in requested_names - {"macwise"}
    }


def formula_resources(text: str) -> dict[str, tuple[str, str]]:
    return {
        name: (url, digest)
        for name, url, digest in re.findall(
            r'resource "([^"]+)" do\s+url "([^"]+)"\s+sha256 "([0-9a-f]{64})"\s+end',
            text,
        )
    }


def test_formula_is_exact_rc_with_no_placeholder_or_install_time_resolution() -> None:
    text = FORMULA.read_text(encoding="utf-8")

    assert "macwise-1.0.0rc1.tar.gz" in text
    assert not re.search(r'^  version "', text, re.MULTILINE)
    assert re.search(r'^  sha256 "[0-9a-f]{64}"$', text, re.MULTILINE)
    assert "PLACEHOLDER" not in text
    assert "pip install" not in text
    assert "virtualenv_install_with_resources" in text
    assert 'depends_on "python@3.13"' in text


def test_formula_resources_exactly_match_locked_macos_runtime_closure() -> None:
    assert formula_resources(FORMULA.read_text(encoding="utf-8")) == production_resources()


def test_formula_smoke_checks_the_installed_rc() -> None:
    text = FORMULA.read_text(encoding="utf-8")

    assert 'system bin/"macwise", "--version"' in text
    assert 'assert_match "MacWise 1.0.0rc1"' in text


def test_formula_main_hash_matches_reproducible_release_sdist(tmp_path: Path) -> None:
    subprocess.run(
        ("uv", "build", "--sdist", "--out-dir", str(tmp_path)),
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    artifact = next(tmp_path.glob("macwise-1.0.0rc1.tar.gz"))
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    text = FORMULA.read_text(encoding="utf-8")
    main_digest = re.search(r'^  sha256 "([0-9a-f]{64})"$', text, re.MULTILINE)

    assert main_digest is not None
    assert main_digest.group(1) == digest
