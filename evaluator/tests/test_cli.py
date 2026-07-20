"""The evaluator CLI reads files and emits reports without invoking the product."""

from pathlib import Path

from typer.testing import CliRunner

from macwise_eval.cli import app

RUNNER = CliRunner()
FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_evaluate_writes_json_and_markdown_to_an_explicit_empty_directory(tmp_path: Path) -> None:
    output_dir = tmp_path / "report"
    capsule = FIXTURES / "synthetic" / "minimal"
    product_output = FIXTURES / "product_outputs" / "audit-v4.json"

    result = RUNNER.invoke(
        app,
        [
            "evaluate",
            str(capsule),
            "--product-output",
            str(product_output),
            "--policy-outcome",
            "MW-EVAL-004=pass",
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0, result.stdout
    assert (output_dir / "evaluation.json").is_file()
    assert (output_dir / "evaluation.md").is_file()
    assert "PASS" in result.stdout


def test_evaluate_refuses_an_existing_nonempty_output_directory(tmp_path: Path) -> None:
    output_dir = tmp_path / "report"
    output_dir.mkdir()
    (output_dir / "existing.txt").write_text("keep", encoding="utf-8")
    capsule = FIXTURES / "synthetic" / "minimal"
    product_output = FIXTURES / "product_outputs" / "audit-v4.json"

    result = RUNNER.invoke(
        app,
        [
            "evaluate",
            str(capsule),
            "--product-output",
            str(product_output),
            "--policy-outcome",
            "MW-EVAL-004=pass",
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 2
    assert "empty" in result.stdout
