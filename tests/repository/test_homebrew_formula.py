import re
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
    seen = {"macwise"}
    pending = ["macwise"]
    while pending:
        for dependency in packages[pending.pop()].get("dependencies", []):
            marker = dependency.get("marker")
            if marker and not Marker(marker).evaluate(environment):
                continue
            name = dependency["name"]
            if name not in seen:
                seen.add(name)
                pending.append(name)
    return {
        name: (
            packages[name]["sdist"]["url"],
            packages[name]["sdist"]["hash"].removeprefix("sha256:"),
        )
        for name in seen - {"macwise"}
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

    assert 'version "1.0.0rc1"' in text
    assert "macwise-1.0.0rc1.tar.gz" in text
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
