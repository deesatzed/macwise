"""Standalone command surface for the independent evaluator."""

from pathlib import Path
from typing import Annotated

import typer

from macwise_eval import __version__
from macwise_eval.capture import capture_private_capsule
from macwise_eval.evaluate import evaluate as evaluate_capsule
from macwise_eval.io import verify_receipts
from macwise_eval.models import CapsuleManifest, ScenarioOracle
from macwise_eval.oracle import contract_digest
from macwise_eval.product_output import parse_product_output
from macwise_eval.reporting import render_json, render_markdown

app = typer.Typer(
    name="macwise-eval",
    help="Independently assess serialized MacWise evidence and safety claims.",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    """Print the evaluator version when explicitly requested."""
    if value:
        typer.echo(f"MacWise Evaluator {__version__}")
        raise typer.Exit()


@app.callback()
def root(
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show the evaluator version and exit.",
    ),
) -> None:
    """Assess evidence without importing or executing the product under test."""
    del version


def _empty_output_directory(path: Path) -> None:
    if path.is_symlink():
        raise ValueError("output directory must not be a symlink")
    if path.exists():
        if not path.is_dir() or any(path.iterdir()):
            raise ValueError("output directory must be empty")
    else:
        path.mkdir(parents=True)


@app.command()
def capture(
    private_output: Annotated[Path, typer.Option("--private-output")],
) -> None:
    """Capture read-only reference evidence locally; it is never uploaded or made public."""
    try:
        result = capture_private_capsule(private_output)
    except (OSError, ValueError) as error:
        typer.echo(f"Reference capture could not run: {error}")
        raise typer.Exit(code=2) from None
    typer.echo(
        f"Saved {result.observation_count} observation categories to the private output directory."
    )


@app.command()
def evaluate(
    capsule: Annotated[Path, typer.Argument(exists=True, file_okay=False, dir_okay=True)],
    product_output: Annotated[Path, typer.Option("--product-output", exists=True, dir_okay=False)],
    output_dir: Annotated[Path, typer.Option("--output-dir")],
) -> None:
    """Evaluate one serialized product output against an evidence capsule without running it."""
    try:
        if capsule.is_symlink() or product_output.is_symlink():
            raise ValueError("capsule and product output must not be symlinks")
        manifest = CapsuleManifest.model_validate_json(
            (capsule / "manifest.json").read_text(encoding="utf-8")
        )
        oracle_path = capsule / "oracle.json"
        oracle = ScenarioOracle.model_validate_json(oracle_path.read_text(encoding="utf-8"))
        receipt_failures = verify_receipts(capsule, manifest)
        if receipt_failures:
            raise ValueError("; ".join(receipt_failures))
        policy_path = Path(__file__).parents[2] / "policies" / "v1" / "safety.toml"
        report = evaluate_capsule(
            manifest,
            oracle,
            parse_product_output(product_output.read_text(encoding="utf-8")),
            contract_digest=contract_digest((policy_path, oracle_path)),
        )
        _empty_output_directory(output_dir)
        (output_dir / "evaluation.json").write_text(render_json(report), encoding="utf-8")
        (output_dir / "evaluation.md").write_text(render_markdown(report), encoding="utf-8")
    except (OSError, ValueError) as error:
        typer.echo(f"Evaluation could not run: {error}")
        raise typer.Exit(code=2) from None
    typer.echo(f"Evaluation verdict: {report.final_verdict.value.upper()}")


def main() -> None:
    """Run the standalone evaluator command."""
    app()
