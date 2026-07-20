"""Private capture is explicit, local, and never prints collected inventory."""

from pathlib import Path

from pytest import MonkeyPatch
from typer.testing import CliRunner

from macwise_eval.capture import CaptureResult
from macwise_eval.cli import app

RUNNER = CliRunner()


def test_capture_requires_an_explicit_private_output_and_reports_only_aggregate(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    output_dir = tmp_path / "private-capsule"

    def fake_capture(path: Path, **_: object) -> CaptureResult:
        path.mkdir()
        return CaptureResult(capsule_id="live-private-001", observation_count=5)

    monkeypatch.setattr("macwise_eval.cli.capture_private_capsule", fake_capture)

    result = RUNNER.invoke(app, ["capture", "--private-output", str(output_dir)])

    assert result.exit_code == 0
    assert "5 observation categories" in result.stdout
    assert "live-private-001" not in result.stdout


def test_capture_refuses_a_nonempty_private_output(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    output_dir = tmp_path / "private-capsule"
    output_dir.mkdir()
    (output_dir / "existing.txt").write_text("keep", encoding="utf-8")

    result = RUNNER.invoke(app, ["capture", "--private-output", str(output_dir)])

    assert result.exit_code == 2
    assert "empty" in result.stdout
