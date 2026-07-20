"""The product-side fixture driver crosses the boundary only through serialized JSON."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
SCRIPT = ROOT / "scripts" / "generate_eval_product_outputs.py"


def test_driver_generates_sanitized_serialized_outputs_in_an_empty_directory(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "outputs"

    result = subprocess.run(
        (sys.executable, str(SCRIPT), "--output-dir", str(output_dir)),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    audit = json.loads((output_dir / "audit-v4.json").read_text(encoding="utf-8"))
    checkup = json.loads((output_dir / "checkup.json").read_text(encoding="utf-8"))
    assert audit["schema_version"] == 4
    assert audit["audit_id"] == "audit:evaluation-fixture"
    assert checkup["changed_mac"] is False


def test_driver_refuses_to_overwrite_an_existing_directory(tmp_path: Path) -> None:
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    (output_dir / "existing.json").write_text("{}\n", encoding="utf-8")

    result = subprocess.run(
        (sys.executable, str(SCRIPT), "--output-dir", str(output_dir)),
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "empty" in result.stderr
