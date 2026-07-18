import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "scripts/verify_public_release.py"
VERSION = "1.0.0rc1"
SDIST = f"macwise-{VERSION}.tar.gz"
WHEEL = f"macwise-{VERSION}-py3-none-any.whl"
SDIST_DIGEST = "a" * 64
WHEEL_DIGEST = "b" * 64


def fixture_files(tmp_path: Path, *, formula_digest: str = SDIST_DIGEST) -> list[str]:
    pypi = tmp_path / "pypi.json"
    github = tmp_path / "github.json"
    checksums = tmp_path / "SHA256SUMS"
    formula = tmp_path / "macwise.rb"
    pypi.write_text(
        json.dumps(
            {
                "info": {"version": VERSION},
                "urls": [
                    {"filename": SDIST, "digests": {"sha256": SDIST_DIGEST}},
                    {"filename": WHEEL, "digests": {"sha256": WHEEL_DIGEST}},
                ],
            }
        ),
        encoding="utf-8",
    )
    github.write_text(
        json.dumps(
            {
                "tag_name": f"v{VERSION}",
                "prerelease": True,
                "assets": [{"name": SDIST}, {"name": WHEEL}, {"name": "SHA256SUMS"}],
            }
        ),
        encoding="utf-8",
    )
    checksums.write_text(
        f"{SDIST_DIGEST}  dist/{SDIST}\n{WHEEL_DIGEST}  dist/{WHEEL}\n",
        encoding="utf-8",
    )
    formula.write_text(
        (
            "class Macwise < Formula\n"
            f'  url "https://github.com/deesatzed/macwise/releases/download/v{VERSION}/{SDIST}"\n'
            f'  version "{VERSION}"\n'
            f'  sha256 "{formula_digest}"\n'
            "end\n"
        ),
        encoding="utf-8",
    )
    return [
        "--pypi-json",
        str(pypi),
        "--github-json",
        str(github),
        "--checksums",
        str(checksums),
        "--formula",
        str(formula),
    ]


def test_public_release_verifier_accepts_one_exact_cross_channel_identity(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), VERSION, *fixture_files(tmp_path)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "artifacts": [SDIST, WHEEL],
        "status": "verified",
        "tag": f"v{VERSION}",
        "version": VERSION,
    }


def test_public_release_verifier_rejects_formula_digest_drift(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            VERSION,
            *fixture_files(tmp_path, formula_digest="c" * 64),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "formula" in result.stderr.casefold()
