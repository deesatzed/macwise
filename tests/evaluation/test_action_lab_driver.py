"""The product-side action lab must operate only inside its disposable fixture."""

import json
import subprocess
import sys
from pathlib import Path


def test_action_lab_driver_proves_apply_recovery_and_undo(tmp_path: Path) -> None:
    output_dir = tmp_path / "receipt"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_action_lab.py",
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Saved temporary action-lab receipt" in result.stdout
    receipt = json.loads((output_dir / "action-lab.json").read_text(encoding="utf-8"))
    assert receipt["lab_kind"] == "temporary_synthetic_bundle"
    assert receipt["after_apply"] == {"source_exists": False, "trash_exists": True}
    assert receipt["interrupted_recovery"] == {"state": "interrupted", "source_exists": True}
    assert receipt["after_undo"]["source_exists"] is True
    assert receipt["after_undo"]["trash_exists"] is False
    assert receipt["sentinel"] == {"unchanged": True}
    assert "/" not in (output_dir / "action-lab.json").read_text(encoding="utf-8")
