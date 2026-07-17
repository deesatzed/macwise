"""The public MacWise command-line interface."""

import platform
import sys
from collections.abc import Callable, Sequence
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from macwise import __version__
from macwise.help_text import HELP
from macwise.models import AuditDocument, EntityType, SoftwareRecord
from macwise.reporting import render_json, render_markdown
from macwise.services import AuditService
from macwise.system.commands import ReadCommand, resolve_executable

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
"""


class OutputFormat(StrEnum):
    TERMINAL = "terminal"
    JSON = "json"
    MARKDOWN = "markdown"


app = typer.Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    help=HELP["root"],
    invoke_without_command=True,
    no_args_is_help=False,
    rich_markup_mode=None,
)
review_app = typer.Typer(
    help=HELP["review"],
    invoke_without_command=True,
    no_args_is_help=False,
    rich_markup_mode=None,
)
plan_app = typer.Typer(
    help=HELP["plan"],
    invoke_without_command=True,
    no_args_is_help=False,
    rich_markup_mode=None,
)
setup_app = typer.Typer(
    help=HELP["setup"],
    invoke_without_command=True,
    no_args_is_help=False,
    rich_markup_mode=None,
)
app.add_typer(review_app, name="review")
app.add_typer(plan_app, name="plan")
app.add_typer(setup_app, name="setup")

_service_factory: Callable[[], AuditService] = AuditService


def _is_interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _application_roots(additional: Sequence[Path] = ()) -> tuple[Path, ...]:
    roots = (Path("/Applications"), Path.home() / "Applications", *additional)
    unique: dict[str, Path] = {}
    for root in roots:
        absolute = Path(root).expanduser().absolute()
        unique.setdefault(str(absolute), absolute)
    return tuple(unique.values())


def _audit(application_roots: Sequence[Path] | None = None) -> AuditDocument:
    roots = tuple(application_roots) if application_roots is not None else _application_roots()
    return _service_factory().run(roots)


def _render(audit: AuditDocument, output_format: OutputFormat) -> str:
    return render_json(audit) if output_format is OutputFormat.JSON else render_markdown(audit)


def _write_or_print(content: str, output: Path | None, force: bool) -> None:
    if output is None:
        typer.echo(content, nl=False)
        return
    if output.exists() and not force:
        typer.echo(f"MacWise did not replace {output} because it already exists.")
        typer.echo("Run again with --force only after reviewing that file.")
        raise typer.Exit(2)
    try:
        output.write_text(content, encoding="utf-8")
    except OSError as error:
        typer.echo(f"MacWise could not save {output}: {error.strerror or error}.")
        typer.echo("Run with a writable --output path.")
        raise typer.Exit(2) from error
    typer.echo(f"Saved the read-only audit to {output}.")


def _phase_message(message: str, *next_steps: str, failure: bool = False) -> None:
    typer.echo(message)
    typer.echo("No changes were made.")
    typer.echo("\nNext:")
    for step in next_steps:
        typer.echo(f"  {step}")
    if failure:
        raise typer.Exit(2)


def _matching_records(audit: AuditDocument, query: str) -> tuple[SoftwareRecord, ...]:
    qualifier, separator, raw_name = query.partition(":")
    sought = raw_name if separator and qualifier in {"app", "cask", "formula"} else query
    normalized = sought.strip().casefold()
    allowed_types = {
        "app": {EntityType.APPLICATION},
        "cask": {EntityType.HOMEBREW_CASK},
        "formula": {EntityType.HOMEBREW_FORMULA},
    }.get(qualifier if separator else "", set(EntityType))
    exact = tuple(
        record
        for record in audit.software
        if record.entity_type in allowed_types
        and normalized
        in {
            record.name.casefold(),
            record.display_name.casefold(),
            (record.identifier or "").casefold(),
        }
    )
    if exact:
        return exact
    return tuple(
        record
        for record in audit.software
        if record.entity_type in allowed_types
        and normalized
        in f"{record.name} {record.display_name} {record.identifier or ''}".casefold()
    )


def _record_label(record: SoftwareRecord) -> str:
    kind = {
        EntityType.APPLICATION: "application",
        EntityType.HOMEBREW_CASK: "Homebrew cask",
        EntityType.HOMEBREW_FORMULA: "Homebrew formula",
    }[record.entity_type]
    return f"{record.display_name} ({kind})"


def _list_records(records: Sequence[SoftwareRecord]) -> None:
    if not records:
        typer.echo(
            "No matching records were collected. Check collection limitations with macwise scan."
        )
        return
    for record in records:
        version = f" — version {record.version}" if record.version else ""
        typer.echo(f"- {_record_label(record)}{version}")
        if record.install_path:
            typer.echo(f"  Location: {record.install_path}")
        if record.entity_type is EntityType.HOMEBREW_FORMULA:
            typer.echo(f"  Installation role: {record.install_role.value}")


@app.command(help=HELP["scan"])
def scan(
    output_format: Annotated[
        OutputFormat,
        typer.Option("--format", "-f", help="Choose terminal, JSON, or Markdown output."),
    ] = OutputFormat.TERMINAL,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Explicitly save the audit to this file."),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", help="Replace an existing --output file after review."),
    ] = False,
    app_root: Annotated[
        list[Path] | None,
        typer.Option(
            "--app-root",
            help="Also scan this explicitly approved application folder (repeatable).",
        ),
    ] = None,
) -> None:
    """Create and render one read-only audit."""
    audit = _audit(_application_roots(app_root or ()))
    _write_or_print(_render(audit, output_format), output, force)


@review_app.callback()
def review_root(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@review_app.command("apps", help=HELP["review_apps"])
def review_apps() -> None:
    records = tuple(
        item for item in _audit().software if item.entity_type is EntityType.APPLICATION
    )
    typer.echo("Applications\n")
    _list_records(records)
    typer.echo("\nThis review is read-only. Related user data and usage evidence remain unknown.")


@review_app.command("brew", help=HELP["review_brew"])
def review_brew() -> None:
    records = tuple(
        item
        for item in _audit().software
        if item.entity_type in {EntityType.HOMEBREW_FORMULA, EntityType.HOMEBREW_CASK}
    )
    typer.echo("Homebrew software\n")
    _list_records(records)
    typer.echo("\nDependencies are not presented as independently selected applications.")


@review_app.command("startup", help=HELP["review_startup"])
def review_startup() -> None:
    startup()


@review_app.command("duplicates", help=HELP["review_duplicates"])
def review_duplicates() -> None:
    _phase_message(
        "Role-aware overlap analysis is not available until Phase 3; MacWise will not guess from names.",
        "macwise compare NAME NAME",
        "macwise scan",
    )


@review_app.command("largest", help=HELP["review_largest"])
def review_largest() -> None:
    measured = sorted(
        (item for item in _audit().software if item.size_bytes is not None),
        key=lambda item: item.size_bytes or 0,
        reverse=True,
    )
    typer.echo("Largest measured application bundles\n")
    for record in measured:
        typer.echo(
            f"- {record.display_name}: {record.size_bytes} bytes ({record.storage_location.value})"
        )
    if not measured:
        typer.echo("No application bundle sizes were collected.")
    typer.echo("\nRelated data is not included, so this is not a reclaimable-space estimate.")


@review_app.command("unused", help=HELP["review_unused"])
def review_unused() -> None:
    _phase_message(
        "Reliable usage evidence is not collected until Phase 2. Missing metadata is not proof of non-use.",
        "macwise review unknown",
        "macwise explain NAME",
    )


@review_app.command("unknown", help=HELP["review_unknown"])
def review_unknown() -> None:
    unknown = tuple(item for item in _audit().software if not item.description)
    typer.echo("Items with an unknown purpose\n")
    _list_records(unknown)


@app.command(help=HELP["explain"])
def explain(
    name: Annotated[str, typer.Argument(help="Installed app, cask, or formula name.")],
) -> None:
    matches = _matching_records(_audit(), name)
    if not matches:
        typer.echo(f'MacWise did not find an installed item matching "{name}".')
        typer.echo("Run macwise review apps or macwise review brew, then use the displayed name.")
        raise typer.Exit(2)
    if len(matches) > 1:
        typer.echo("MacWise found more than one possible match:\n")
        for index, record in enumerate(matches, start=1):
            typer.echo(f"{index}. {_record_label(record)}")
        typer.echo("\nRun a qualified name such as app:NAME, cask:NAME, or formula:NAME.")
        raise typer.Exit(2)
    record = next(iter(matches))
    typer.echo(f"{record.display_name}\n")
    typer.echo(f"Verified type: {record.entity_type.value}")
    typer.echo(f"Version: {record.version or 'Unknown'}")
    typer.echo(f"Installed by: {record.install_source or 'Unknown'}")
    typer.echo(f"Purpose: {record.description or 'Unknown in the current local catalog'}")
    typer.echo("Usage: No reliable usage assessment has been collected yet.")
    typer.echo("Backup coverage: Not verified.")
    typer.echo(
        "Recommendation: Not available until dependency, usage, data, and backup checks complete."
    )
    typer.echo("\nThis command is read-only. MacWise did not change this Mac.")


@app.command(help=HELP["compare"])
def compare(
    names: Annotated[list[str], typer.Argument(help="One or more installed names.")],
) -> None:
    typer.echo(f"Requested comparison: {', '.join(names)}")
    _phase_message(
        "Role-aware overlap categories and actual-use comparison are not available until Phase 3.",
        "macwise review duplicates",
        "macwise explain NAME",
    )


@app.command(help=HELP["startup"])
def startup() -> None:
    services = tuple(item for item in _audit().software if item.service_status)
    typer.echo("Verified Homebrew services\n")
    for record in services:
        typer.echo(f"- {record.display_name}: {record.service_status}")
    if not services:
        typer.echo("No active Homebrew service metadata was collected.")
    typer.echo("\nLogin items, LaunchAgents, and system extensions are unknown until Phase 2.")
    typer.echo("This command is read-only. MacWise did not change this Mac.")


@app.command(help=HELP["storage"])
def storage() -> None:
    audit = _audit()
    typer.echo("Storage volumes\n")
    for volume in audit.volumes:
        mount = volume.mount_point or "unmounted"
        typer.echo(
            f"- {volume.name}: {volume.location.value}, {volume.free_bytes or 0} bytes free, {mount}"
        )
    if not audit.volumes:
        typer.echo("No storage metadata was collected.")
    typer.echo("\nThis command is read-only. MacWise did not change this Mac.")


@app.command(help=HELP["backups"])
def backups() -> None:
    _phase_message(
        "Backup coverage has not been verified in Phase 1. MacWise will not infer coverage from configuration alone.",
        "macwise storage",
        "macwise scan",
    )


@plan_app.callback()
def plan_root(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        _phase_message(
            "Cleanup planning is not available until dependency, backup, and rollback preflight exists.",
            "macwise explain NAME",
            "macwise scan",
            failure=True,
        )


@plan_app.command("add", help=HELP["plan_add"])
def plan_add(
    name: Annotated[str, typer.Argument(help="One reviewed, unambiguous item name.")],
) -> None:
    _phase_message(
        f'MacWise did not add "{name}" because cleanup planning is not available yet.',
        "macwise explain NAME",
        "macwise plan show",
        failure=True,
    )


@plan_app.command("show", help=HELP["plan_show"])
def plan_show() -> None:
    _phase_message(
        "No cleanup plan exists because Phase 4 planning has not been enabled.",
        "macwise explain NAME",
        "macwise scan",
    )


@app.command("apply", help=HELP["apply"])
def apply_plan() -> None:
    _phase_message(
        "MacWise cannot apply changes because reversible execution and an approved plan are unavailable.",
        "macwise plan show",
        "macwise scan",
        failure=True,
    )


@app.command(help=HELP["undo"])
def undo() -> None:
    _phase_message(
        "MacWise cannot undo changes because this build cannot create action manifests.",
        "macwise doctor",
        "macwise scan",
        failure=True,
    )


@app.command(help=HELP["doctor"])
def doctor() -> None:
    typer.echo("MacWise doctor\n")
    typer.echo(f"Operating system: {platform.system()} {platform.release()}")
    typer.echo(f"Python: {platform.python_version()}")
    brew = "available" if resolve_executable(ReadCommand.BREW) else "not found (optional)"
    typer.echo(f"Homebrew: {brew}")
    typer.echo("Collectors are read-only. Run macwise scan for a complete collection check.")


@setup_app.callback()
def setup_root(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@setup_app.command("codex", help=HELP["setup_codex"])
def setup_codex() -> None:
    _phase_message(
        "Codex setup is unavailable until the bundled skill and typed read-only integration pass Phase 6 tests.",
        "macwise scan",
        "macwise doctor",
        failure=True,
    )


@app.command("help", help=HELP["help"])
def help_command(ctx: typer.Context) -> None:
    typer.echo(ctx.parent.get_help() if ctx.parent else ctx.get_help())


def _guided_action(choice: int, ctx: typer.Context) -> None:
    if choice == 1:
        scan()
    elif choice == 2:
        review_apps()
    elif choice == 3:
        review_brew()
    elif choice == 4:
        startup()
    elif choice == 5:
        review_duplicates()
    elif choice == 6:
        review_largest()
    elif choice == 7:
        explain(typer.prompt("App or tool name"))
    elif choice == 8:
        plan_root(ctx)
    else:
        typer.echo(ctx.get_help())


@app.callback()
def guided(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option("--version", help="Show the installed MacWise version and exit."),
    ] = False,
) -> None:
    """Show the guided experience when no direct command was selected."""
    if version:
        typer.echo(f"MacWise {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is not None:
        return
    typer.echo(GUIDED_MENU)
    if not _is_interactive():
        typer.echo("Run macwise --help to see direct commands.")
        return
    choice = typer.prompt("Choose 1-9", type=int)
    if choice not in range(1, 10):
        typer.echo("Choose a number from 1 through 9.")
        raise typer.Exit(2)
    _guided_action(choice, ctx)


def main() -> None:
    """Run the MacWise CLI."""
    app()
