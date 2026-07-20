"""Standalone command surface for the independent evaluator."""

from pathlib import Path
from typing import Annotated

import typer

from macwise_eval import __version__
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


def _parse_policy_outcomes(values: tuple[str, ...]) -> dict[str, str]:
    outcomes: dict[str, str] = {}
    for value in values:
        identifier, separator, outcome = value.partition("=")
        if not separator or not identifier or outcome not in {"pass", "fail", "inconclusive"}:
            raise ValueError("policy outcomes must use POLICY_ID=pass|fail|inconclusive")
        if identifier in outcomes:
            raise ValueError(f"policy outcome is repeated: {identifier}")
        outcomes[identifier] = outcome
    return outcomes


def _empty_output_directory(path: Path) -> None:
    if path.is_symlink():
        raise ValueError("output directory must not be a symlink")
    if path.exists():
        if not path.is_dir() or any(path.iterdir()):
            raise ValueError("output directory must be empty")
    else:
        path.mkdir(parents=True)


@app.command()
def evaluate(
    capsule: Annotated[Path, typer.Argument(exists=True, file_okay=False, dir_okay=True)],
    product_output: Annotated[Path, typer.Option("--product-output", exists=True, dir_okay=False)],
    output_dir: Annotated[Path, typer.Option("--output-dir")],
    policy_outcomes: Annotated[list[str] | None, typer.Option("--policy-outcome")] = None,
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
        outcomes = _parse_policy_outcomes(tuple(policy_outcomes or ()))
        policy_path = Path(__file__).parents[2] / "policies" / "v1" / "safety.toml"
        report = evaluate_capsule(
            manifest,
            oracle,
            parse_product_output(product_output.read_text(encoding="utf-8")),
            contract_digest=contract_digest((policy_path, oracle_path)),
            observed_policy_outcomes=outcomes,
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
