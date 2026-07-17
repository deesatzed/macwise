"""The public MacWise command-line interface."""

import typer

ROOT_HELP = """Understand the software installed on this Mac and decide what deserves attention.

MacWise gathers local evidence and explains it in plain language. The guided experience is
useful when you do not know which command to choose.

This command does not remove or change anything.

Examples:
  macwise
  macwise scan

Next:
  Run macwise scan to create a read-only software inventory.
"""

GUIDED_MENU = """MacWise

What would you like to do?

1. Scan this Mac
2. Review installed apps
3. Review Homebrew software
4. See what starts automatically
5. Find overlapping apps
6. See what uses the most space
7. Ask what an app does
8. Create a safe cleanup plan
9. Help

Run macwise --help to see direct commands.
"""

app = typer.Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    help=ROOT_HELP,
    invoke_without_command=True,
    no_args_is_help=False,
    rich_markup_mode=None,
)


@app.callback()
def guided(ctx: typer.Context) -> None:
    """Show the guided experience when no direct command was selected."""
    if ctx.invoked_subcommand is None:
        typer.echo(GUIDED_MENU)


def main() -> None:
    """Run the MacWise CLI."""
    app()
