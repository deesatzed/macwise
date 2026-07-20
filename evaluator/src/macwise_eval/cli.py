"""Standalone command surface for the independent evaluator."""

import typer

from macwise_eval import __version__

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


def main() -> None:
    """Run the standalone evaluator command."""
    app()
