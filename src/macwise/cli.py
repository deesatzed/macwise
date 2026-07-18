"""The public MacWise command-line interface."""

import hashlib
import os
import platform
import re
import shutil
import stat
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from enum import StrEnum
from importlib.resources import files
from itertools import combinations
from pathlib import Path
from typing import Annotated, Never, Protocol
from uuid import uuid4

import typer

from macwise import __version__
from macwise.execution import (
    FilesystemActionError,
    MutationCommandAdapter,
    TrashFilesystemAdapter,
    application_identity_digest,
)
from macwise.help_text import HELP
from macwise.integration.server import run_stdio
from macwise.integration.setup import (
    CodexSetupService,
    SetupResult,
    SetupStatus,
    SubprocessCodexRunner,
)
from macwise.models import (
    ActionObservation,
    ActionState,
    AuditDocument,
    ClaimBasis,
    EntityType,
    ExecutionAction,
    ExecutionRun,
    ExecutionState,
    Finding,
    FindingTopic,
    OverlapCategory,
    OverlapRelation,
    PlanActionKind,
    PlanDocument,
    PlanEligibility,
    PlannedAction,
    PreflightOutcome,
    SoftwareRecord,
    UsageLabel,
)
from macwise.persistence import (
    ExecutionStore,
    ExecutionStoreError,
    PlanStore,
    PlanStoreError,
    execution_digest,
)
from macwise.reporting import render_json, render_markdown
from macwise.services import (
    ApprovalError,
    AuditService,
    ExecutionService,
    ExecutionServiceError,
    PreparedExecution,
    RevalidationError,
    add_candidate,
    apply_approval_phrase,
    prepare_execution,
    require_approval,
    undo_approval_phrase,
)
from macwise.system.commands import CommandState, ReadCommand, resolve_executable, run_read_command
from macwise.text import safe_display_text

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
9. Review undo recovery
10. Help
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
codex_app = typer.Typer(invoke_without_command=False, no_args_is_help=True)
app.add_typer(review_app, name="review")
app.add_typer(plan_app, name="plan")
app.add_typer(setup_app, name="setup")
app.add_typer(codex_app, name="codex", hidden=True)

_service_factory: Callable[[], AuditService] = AuditService
_plan_store_factory: Callable[[], PlanStore] = PlanStore


class CLICodexSetupService(Protocol):
    def install(self) -> SetupResult: ...


def _default_codex_setup_factory() -> CLICodexSetupService:
    executable = shutil.which("codex")
    if executable is None:
        return _UnavailableCodexSetupService(
            "Codex is not installed or is not available to MacWise.",
            "Install or update Codex, then run macwise setup codex again.",
        )
    try:
        runner = SubprocessCodexRunner(
            executable=Path(executable),
            home=Path.home(),
        )
    except ValueError:
        return _UnavailableCodexSetupService(
            "MacWise could not verify the Codex executable.",
            "Install or update Codex, then run macwise setup codex again.",
        )
    payload = Path(str(files("macwise").joinpath("codex_payload", "macwise")))
    return CodexSetupService(
        home=Path.home(),
        payload=payload,
        python_executable=Path(sys.executable),
        runner=runner,
    )


class _UnavailableCodexSetupService:
    def __init__(self, message: str, recovery: str) -> None:
        self.message = message
        self.recovery = recovery

    def install(self) -> SetupResult:
        return SetupResult(
            status=SetupStatus.REFUSED,
            message=self.message,
            recovery=self.recovery,
        )


_codex_setup_factory: Callable[[], CLICodexSetupService] = _default_codex_setup_factory
_codex_stdio_runner: Callable[[], None] = run_stdio


class CLIExecutionService(Protocol):
    def apply(self, prepared: PreparedExecution, *, approval: str) -> ExecutionRun: ...

    def active(self) -> ExecutionRun | None: ...

    def undoable(self) -> ExecutionRun | None: ...

    def undo(self, *, approval: str) -> ExecutionRun: ...


def _planning_clock() -> datetime:
    return datetime.now(UTC)


def _plan_id_factory() -> str:
    return f"plan:{uuid4().hex}"


def _trash_root_factory() -> Path:
    return Path.home() / ".Trash"


def filesystem_observation(path: Path) -> ActionObservation:
    try:
        item = path.lstat()
    except FileNotFoundError:
        return ActionObservation(exists=False)
    except OSError:
        return ActionObservation(exists=None)
    identity = None
    if stat.S_ISDIR(item.st_mode):
        try:
            identity = application_identity_digest(path)
        except FilesystemActionError:
            return ActionObservation(exists=None)
    return ActionObservation(
        exists=True,
        device=item.st_dev,
        inode=item.st_ino,
        identity_digest=identity,
    )


def prepare_execution_for_cli(
    plan: PlanDocument,
    audit: AuditDocument,
) -> PreparedExecution:
    prepared = prepare_execution(
        plan,
        audit,
        trash_root=_trash_root_factory(),
        filesystem_probe=filesystem_observation,
    )
    allowed_roots = set(_application_roots())
    if any(
        action.kind is PlanActionKind.MOVE_APPLICATION_TO_TRASH
        and (
            action.inverse.destination_path is None
            or Path(action.inverse.destination_path).parent not in allowed_roots
        )
        for action in prepared.actions
    ):
        raise RevalidationError(
            "A manual application source is outside the live execution allowlist."
        )
    return prepared


_execution_preparer: Callable[[PlanDocument, AuditDocument], PreparedExecution] = (
    prepare_execution_for_cli
)


class LiveActionObserver:
    """Collect fresh command-action state through existing read-only collectors."""

    @staticmethod
    def collector_complete(audit: AuditDocument, collector: str) -> bool:
        return any(
            item.collector == collector and item.state.value == "complete"
            for item in audit.collectors
        )

    @classmethod
    def homebrew_installed(
        cls,
        audit: AuditDocument,
        entity_type: EntityType,
        token: str | None,
    ) -> bool | None:
        matches = tuple(
            item
            for item in audit.software
            if item.entity_type is entity_type and item.name == token
        )
        if len(matches) == 1:
            return True
        if not matches and cls.collector_complete(audit, "homebrew"):
            return False
        return None

    @staticmethod
    def launchctl_state(
        label: str,
        *,
        default_enabled: bool | None,
    ) -> tuple[bool | None, bool | None]:
        uid = os.getuid()
        disabled = run_read_command(
            ReadCommand.LAUNCHCTL,
            ("print-disabled", f"gui/{uid}"),
        )
        enabled = default_enabled
        if disabled.state is CommandState.COMPLETE:
            match = re.search(
                rf'"{re.escape(label)}"\s*=>\s*(true|false)',
                disabled.stdout,
            )
            if match is not None:
                enabled = match.group(1) == "false"
        printed = run_read_command(
            ReadCommand.LAUNCHCTL,
            ("print", f"gui/{uid}/{label}"),
        )
        running: bool | None = True if printed.state is CommandState.COMPLETE else None
        missing_text = f"{printed.stdout}\n{printed.stderr}".casefold()
        if (
            printed.state is CommandState.FAILED
            and printed.return_code in {3, 113}
            and any(
                marker in missing_text
                for marker in (
                    "could not find service",
                    "could not find specified service",
                    "service not found",
                )
            )
        ):
            running = False
        return enabled, running

    def observe(self, action: ExecutionAction) -> ActionObservation:
        audit = _audit()
        if action.kind in {
            PlanActionKind.HOMEBREW_UNINSTALL_FORMULA,
            PlanActionKind.HOMEBREW_UNINSTALL_CASK,
        }:
            expected = (
                EntityType.HOMEBREW_FORMULA
                if action.kind is PlanActionKind.HOMEBREW_UNINSTALL_FORMULA
                else EntityType.HOMEBREW_CASK
            )
            return ActionObservation(
                installed=self.homebrew_installed(
                    audit,
                    expected,
                    action.inverse.homebrew_token,
                )
            )
        if action.kind is PlanActionKind.STOP_HOMEBREW_SERVICE:
            matches = tuple(
                item
                for item in audit.startup
                if item.id == action.inverse.startup_id
                and item.label == action.inverse.startup_label
            )
            return ActionObservation(
                running=matches[0].running if len(matches) == 1 else None,
                enabled=matches[0].enabled if len(matches) == 1 else None,
            )
        if action.kind is not PlanActionKind.DISABLE_LAUNCH_AGENT:
            return ActionObservation()
        source_value = action.inverse.startup_source_path
        label = action.inverse.startup_label
        if source_value is None or label is None:
            return ActionObservation()
        source = Path(source_value)
        try:
            content_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        except OSError:
            return ActionObservation(exists=False)
        startup = tuple(
            item
            for item in audit.startup
            if item.id == action.inverse.startup_id
            and item.label == label
            and item.source_path == source_value
        )
        default_enabled = startup[0].enabled if len(startup) == 1 else None
        enabled, running = self.launchctl_state(
            label,
            default_enabled=default_enabled,
        )
        return ActionObservation(
            exists=True,
            enabled=enabled,
            running=running,
            plist_sha256=content_hash,
        )


def _execution_service_factory(plan_store: PlanStore) -> CLIExecutionService:
    lock_path = plan_store.lock_path
    return ExecutionService(
        plan_store=plan_store,
        execution_store=ExecutionStore(lock_path=lock_path),
        state_lock_path=lock_path,
        trash_adapter=TrashFilesystemAdapter(
            source_roots=_application_roots(),
            trash_root=_trash_root_factory(),
        ),
        command_adapter=MutationCommandAdapter(
            launch_agents_root=Path.home() / "Library" / "LaunchAgents",
            uid=os.getuid(),
        ),
        action_observer=LiveActionObserver(),
        filesystem_probe=filesystem_observation,
        revalidator=lambda current_plan: prepare_execution_for_cli(
            current_plan,
            _audit(),
        ),
        clock=lambda: datetime.now(UTC),
        run_id_factory=lambda: f"run:{uuid4().hex}",
    )


def _is_interactive() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _deduplicated_roots(roots: Sequence[Path]) -> tuple[Path, ...]:
    unique: dict[str, Path] = {}
    for root in roots:
        absolute = Path(root).expanduser().absolute()
        unique.setdefault(str(absolute), absolute)
    return tuple(unique.values())


def _application_roots(additional: Sequence[Path] = ()) -> tuple[Path, ...]:
    return _deduplicated_roots((Path("/Applications"), Path.home() / "Applications", *additional))


def _audit(
    application_roots: Sequence[Path] | None = None,
    *,
    project_roots: Sequence[Path] = (),
) -> AuditDocument:
    roots = tuple(application_roots) if application_roots is not None else _application_roots()
    service = _service_factory()
    if project_roots:
        return service.run(roots, project_roots=tuple(project_roots))
    return service.run(roots)


def _render(audit: AuditDocument, output_format: OutputFormat) -> str:
    return render_json(audit) if output_format is OutputFormat.JSON else render_markdown(audit)


def _write_or_print(content: str, output: Path | None, force: bool) -> None:
    if output is None:
        typer.echo(content, nl=False)
        return
    if output.exists() and not force:
        typer.echo(
            f"MacWise did not replace {safe_display_text(output)} because it already exists."
        )
        typer.echo("Run again with --force only after reviewing that file.")
        raise typer.Exit(2)
    try:
        output.write_text(content, encoding="utf-8")
    except OSError as error:
        typer.echo(
            f"MacWise could not save {safe_display_text(output)}: "
            f"{safe_display_text(error.strerror or error)}."
        )
        typer.echo("Run with a writable --output path.")
        raise typer.Exit(2) from error
    typer.echo(f"Saved the read-only audit to {safe_display_text(output)}.")


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


def _resolve_record(audit: AuditDocument, query: str) -> SoftwareRecord:
    matches = _matching_records(audit, query)
    if not matches:
        typer.echo(f'MacWise did not find an installed item matching "{safe_display_text(query)}".')
        typer.echo("Run macwise review apps or macwise review brew, then use the displayed name.")
        raise typer.Exit(2)
    if len(matches) > 1:
        typer.echo("MacWise found more than one possible match:\n")
        for index, record in enumerate(matches, start=1):
            typer.echo(f"{index}. {_record_label(record)}")
        typer.echo("\nRun a qualified name such as app:NAME, cask:NAME, or formula:NAME.")
        raise typer.Exit(2)
    return next(iter(matches))


def _record_label(record: SoftwareRecord) -> str:
    kind = {
        EntityType.APPLICATION: "application",
        EntityType.HOMEBREW_CASK: "Homebrew cask",
        EntityType.HOMEBREW_FORMULA: "Homebrew formula",
    }[record.entity_type]
    return f"{safe_display_text(record.display_name)} ({kind})"


def _human_label(value: str) -> str:
    return safe_display_text(value.replace("_", " "))


def _tri_state(value: bool | None) -> str:
    if value is None:
        return "unknown"
    return "yes" if value else "no"


def _bytes(value: int | None) -> str:
    if value is None:
        return "unknown size"
    amount = float(value)
    units = ("bytes", "KiB", "MiB", "GiB", "TiB")
    unit = units[0]
    for candidate in units:
        unit = candidate
        if amount < 1024 or candidate == units[-1]:
            break
        amount /= 1024
    return f"{int(amount)} {unit}" if unit == "bytes" else f"{amount:.1f} {unit}"


def _finding_summary(finding: Finding) -> str:
    if finding.topic is FindingTopic.USAGE and finding.usage_label is not None:
        topic = f"Usage: {_human_label(finding.usage_label.value)}"
    else:
        topic = _human_label(finding.topic.value).capitalize()
    return (
        f"{topic} ({_human_label(finding.confidence.value)} confidence) — "
        f"{safe_display_text(finding.statement)}"
    )


def _echo_findings(findings: Sequence[Finding]) -> None:
    if not findings:
        typer.echo("- None recorded.")
        return
    for finding in findings:
        typer.echo(f"- {_finding_summary(finding)}")
        for limitation in finding.limitations:
            typer.echo(f"  Limitation: {safe_display_text(limitation)}")


def _usage_finding(audit: AuditDocument, subject_id: str) -> Finding | None:
    return next(
        (
            finding
            for finding in audit.findings
            if finding.subject_id == subject_id and finding.topic is FindingTopic.USAGE
        ),
        None,
    )


_OBSERVED_USE_RANK = {
    UsageLabel.USER_CONFIRMED_UNUSED: 0,
    UsageLabel.POSSIBLY_UNUSED: 1,
    UsageLabel.CONFIGURED_BUT_IDLE: 2,
    UsageLabel.PROBABLY_USED: 3,
    UsageLabel.RECENTLY_USED: 4,
    UsageLabel.ACTIVELY_USED: 5,
}


def _actual_use_comparison(audit: AuditDocument, records: Sequence[SoftwareRecord]) -> str:
    """Compare direct-use evidence conservatively and independently of input order."""
    ranked: list[tuple[int, SoftwareRecord]] = []
    for record in records:
        finding = _usage_finding(audit, record.id)
        if (
            finding is None
            or finding.usage_label is None
            or finding.usage_label is UsageLabel.NO_RELIABLE_EVIDENCE
        ):
            return "Actual-use comparison: unresolved because usage evidence is missing."
        if finding.usage_label is UsageLabel.INDIRECTLY_REQUIRED:
            return (
                "Actual-use comparison: unresolved because dependency evidence is not "
                "direct-use evidence."
            )
        ranked.append((_OBSERVED_USE_RANK[finding.usage_label], record))

    strongest_rank = max(rank for rank, _ in ranked)
    strongest = [record for rank, record in ranked if rank == strongest_rank]
    if len(strongest) != 1:
        return "Actual-use comparison: unresolved; the strongest observed-use evidence is tied."

    winner = strongest[0]
    others = [record for _, record in ranked if record.id != winner.id]
    winner_name = safe_display_text(winner.display_name)
    if len(others) == 1:
        other_label = safe_display_text(others[0].display_name)
        return (
            f"Actual-use comparison: {winner_name} has stronger observed use evidence "
            f"than {other_label}."
        )
    return (
        f"Actual-use comparison: {winner_name} has the strongest observed use evidence "
        "among the selected items."
    )


def _relation_for(
    audit: AuditDocument,
    left_subject_id: str,
    right_subject_id: str,
) -> OverlapRelation | None:
    sought = frozenset((left_subject_id, right_subject_id))
    return next(
        (
            relation
            for relation in audit.overlaps
            if frozenset((relation.left_subject_id, relation.right_subject_id)) == sought
        ),
        None,
    )


def _echo_plan_checks(plan: PlanDocument, outcome: PreflightOutcome, heading: str) -> None:
    typer.echo(f"\n{heading}")
    selected = tuple(item for item in plan.checks if item.outcome is outcome)
    if not selected:
        typer.echo("- None.")
        return
    names = {item.subject_id: item.display_name for item in plan.candidates}
    for item in selected:
        name = names.get(item.subject_id, item.subject_id)
        typer.echo(
            f"- {safe_display_text(name)} — {_human_label(item.kind.value)}: "
            f"{safe_display_text(item.statement)}"
        )
        for limitation in item.limitations:
            typer.echo(f"  Limitation: {safe_display_text(limitation)}")


def _echo_plan(plan: PlanDocument) -> None:
    """Render one saved snapshot without collecting or interpreting current host state."""
    typer.echo("Cleanup plan preview\n")
    typer.echo(f"Plan: {safe_display_text(plan.plan_id)} — revision {plan.revision}")
    typer.echo(f"Snapshot: {plan.source_audit_collected_at.isoformat()}")
    typer.echo(f"Eligibility: {_human_label(plan.eligibility.value)}")
    typer.echo("This eligibility is not approval or action authority.\n")

    actions: dict[str, list[PlannedAction]] = {}
    for item in plan.actions:
        actions.setdefault(item.subject_id, []).append(item)
    for candidate in plan.candidates:
        candidate_kind = {
            EntityType.APPLICATION: "application",
            EntityType.HOMEBREW_CASK: "Homebrew cask",
            EntityType.HOMEBREW_FORMULA: "Homebrew formula",
        }[candidate.entity_type]
        typer.echo(f"- {safe_display_text(candidate.display_name)} ({candidate_kind})")
        typer.echo(
            f"  Candidate snapshot: {candidate.source_audit_collected_at.isoformat()} "
            f"from {safe_display_text(candidate.source_audit_id)}"
        )
        candidate_actions = actions.get(candidate.subject_id, [])
        if not candidate_actions:
            typer.echo("  Preview: no exact supported action can be planned.")
        for action in candidate_actions:
            if action.sequence is not None:
                typer.echo(f"  Action order: {action.sequence}")
            prefix = "  Preview:"
            if action.kind is PlanActionKind.MOVE_APPLICATION_TO_TRASH:
                typer.echo(
                    f"{prefix} move application bundle from "
                    f"{safe_display_text(action.source_path or 'unknown')} to "
                    f"{safe_display_text(action.destination_path or 'unknown')}"
                )
            elif action.kind in {
                PlanActionKind.HOMEBREW_UNINSTALL_FORMULA,
                PlanActionKind.HOMEBREW_UNINSTALL_CASK,
            }:
                package_kind = (
                    "formula"
                    if action.kind is PlanActionKind.HOMEBREW_UNINSTALL_FORMULA
                    else "cask"
                )
                typer.echo(
                    f"{prefix} brew uninstall --{package_kind} "
                    f"{safe_display_text(action.homebrew_token or 'unknown')}"
                )
            elif action.kind is PlanActionKind.DISABLE_LAUNCH_AGENT:
                typer.echo(
                    f"{prefix} disable user LaunchAgent "
                    f"{safe_display_text(action.startup_label or 'unknown')} from "
                    f"{safe_display_text(action.startup_source_path or 'unknown')}"
                )
            else:
                typer.echo(
                    f"{prefix} stop Homebrew service "
                    f"{safe_display_text(action.homebrew_token or 'unknown')}"
                )
        typer.echo(f"  Related data records preserved: {len(candidate.related_path_ids)}")
        planned_startup = sum(action.startup_id is not None for action in candidate_actions)
        if planned_startup:
            typer.echo(f"  Startup changes previewed: {planned_startup}")
        typer.echo(
            "  Startup records left unchanged: "
            f"{max(0, len(candidate.startup_ids) - planned_startup)}"
        )

    _echo_plan_checks(plan, PreflightOutcome.BLOCK, "Blockers")
    _echo_plan_checks(plan, PreflightOutcome.WARNING, "Warnings")
    _echo_plan_checks(plan, PreflightOutcome.PASS, "Observed passes")

    typer.echo("\nRollback blueprints")
    if not plan.rollback:
        typer.echo("- None available.")
    for item in plan.rollback:
        typer.echo(
            f"- Rollback: {_human_label(item.feasibility.value)} — "
            f"{safe_display_text(item.strategy)}"
        )
        for limitation in item.limitations:
            typer.echo(f"  Limitation: {safe_display_text(limitation)}")

    typer.echo("\nPlan limitations")
    for limitation in plan.limitations:
        typer.echo(f"- {safe_display_text(limitation)}")
    typer.echo("\nNo changes were made to installed software, startup state, or user data.")
    if plan.eligibility is PlanEligibility.BLOCKED:
        typer.echo("Next: resolve every blocker, then create a fresh preview.")
    else:
        typer.echo("Next: review this preview, then run macwise apply for fresh revalidation.")


def _plan_store_failure(*, writing: bool) -> Never:
    operation = "save" if writing else "read"
    typer.echo(f"MacWise could not {operation} local planning state safely.")
    typer.echo("Move or back up the planning database, then run macwise plan show again.")
    typer.echo("No changes were made to installed software, startup state, or user data.")
    raise typer.Exit(2)


def _active_plan() -> PlanDocument | None:
    try:
        return _plan_store_factory().active()
    except PlanStoreError:
        _plan_store_failure(writing=False)


def _show_active_plan() -> None:
    plan = _active_plan()
    if plan is None:
        typer.echo("No active cleanup plan exists.")
        typer.echo("No changes were made.")
        typer.echo("\nNext:")
        typer.echo("  macwise explain NAME")
        typer.echo("  macwise plan add NAME")
        return
    _echo_plan(plan)


def _list_records(records: Sequence[SoftwareRecord]) -> None:
    if not records:
        typer.echo(
            "No matching records were collected. Check collection limitations with macwise scan."
        )
        return
    for record in records:
        version = f" — version {safe_display_text(record.version)}" if record.version else ""
        typer.echo(f"- {_record_label(record)}{version}")
        if record.install_path:
            typer.echo(f"  Location: {safe_display_text(record.install_path)}")
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
    project_root: Annotated[
        list[Path] | None,
        typer.Option(
            "--project-root",
            help="Scan this explicitly approved project folder for package references (repeatable).",
        ),
    ] = None,
) -> None:
    """Create and render one read-only audit."""
    audit = _audit(
        _application_roots(app_root or ()),
        project_roots=_deduplicated_roots(project_root or ()),
    )
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
    audit = _audit()
    records = {record.id: record for record in audit.software}
    candidates = tuple(
        relation
        for relation in audit.overlaps
        if relation.category is not OverlapCategory.NOT_ACTUALLY_RELATED
    )
    typer.echo("Overlap candidates — not all are duplicates\n")
    if not candidates:
        typer.echo("No explicit overlap candidates were found in the bundled role catalog.")
    grouped: dict[OverlapCategory, list[OverlapRelation]] = {}
    for relation in candidates:
        grouped.setdefault(relation.category, []).append(relation)
    for category in sorted(grouped, key=lambda item: item.value):
        typer.echo(f"{_human_label(category.value).capitalize()}")
        for relation in grouped[category]:
            left = records.get(relation.left_subject_id)
            right = records.get(relation.right_subject_id)
            left_name = left.display_name if left is not None else relation.left_subject_id
            right_name = right.display_name if right is not None else relation.right_subject_id
            typer.echo(
                f"- {safe_display_text(left_name)} and {safe_display_text(right_name)}: "
                f"{safe_display_text(relation.statement)}"
            )
        typer.echo("")
    typer.echo("This review is read-only and does not authorize removal or other changes.")


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
            f"- {safe_display_text(record.display_name)}: {record.size_bytes} bytes "
            f"({record.storage_location.value})"
        )
    if not measured:
        typer.echo("No application bundle sizes were collected.")
    typer.echo("\nRelated data is not included, so this is not a reclaimable-space estimate.")


@review_app.command("unused", help=HELP["review_unused"])
def review_unused() -> None:
    audit = _audit()
    records = {record.id: record for record in audit.software}
    supported_labels = {
        UsageLabel.POSSIBLY_UNUSED,
        UsageLabel.USER_CONFIRMED_UNUSED,
    }
    candidates = sorted(
        (
            (records[finding.subject_id], finding)
            for finding in audit.findings
            if finding.topic is FindingTopic.USAGE
            and finding.usage_label in supported_labels
            and finding.subject_id in records
        ),
        key=lambda item: (item[0].display_name.casefold(), item[0].id),
    )
    typer.echo("Items with cautious non-use evidence\n")
    if not candidates:
        typer.echo("No items met the supported possibly-unused or user-confirmed-unused labels.")
    for record, finding in candidates:
        assert finding.usage_label is not None
        typer.echo(
            f"- {_record_label(record)}: {_human_label(finding.usage_label.value)} "
            f"({_human_label(finding.basis.value)}, {finding.confidence.value} confidence)"
        )
        typer.echo(f"  Reason: {safe_display_text(finding.statement)}")
        for limitation in finding.limitations:
            typer.echo(f"  Limitation: {safe_display_text(limitation)}")
    typer.echo("\nMissing evidence alone never qualifies an item for this list.")
    typer.echo("This review is read-only. MacWise did not change this Mac.")


@review_app.command("unknown", help=HELP["review_unknown"])
def review_unknown() -> None:
    unknown = tuple(item for item in _audit().software if not item.description)
    typer.echo("Items with an unknown purpose\n")
    _list_records(unknown)


@app.command(help=HELP["explain"])
def explain(
    name: Annotated[str, typer.Argument(help="Installed app, cask, or formula name.")],
) -> None:
    audit = _audit()
    record = _resolve_record(audit, name)
    typer.echo(f"{safe_display_text(record.display_name)}\n")
    typer.echo("Verified facts")
    typer.echo(f"- Type: {_human_label(record.entity_type.value)}")
    typer.echo(f"- Version: {safe_display_text(record.version or 'unknown')}")
    typer.echo(f"- Installed by: {safe_display_text(record.install_source or 'unknown')}")
    typer.echo(
        f"- Purpose: {safe_display_text(record.description or 'unknown in the local catalog')}"
    )
    if record.dependencies:
        typer.echo(f"- Depends on: {', '.join(map(safe_display_text, record.dependencies))}")
    if record.reverse_dependencies:
        typer.echo(
            f"- Required by: {', '.join(map(safe_display_text, record.reverse_dependencies))}"
        )
    if record.size_bytes is not None:
        typer.echo(f"- Installed size: {_bytes(record.size_bytes)}")

    startup_items = sorted(
        (item for item in audit.startup if record.id in item.owner_software_ids),
        key=lambda item: (item.kind.value, item.label.casefold(), item.id),
    )
    for item in startup_items:
        typer.echo(
            f"- {_human_label(item.kind.value).capitalize()}: {safe_display_text(item.label)}"
        )
        typer.echo(f"  Enabled: {_tri_state(item.enabled)}; Running: {_tri_state(item.running)}")

    related_paths = sorted(
        (item for item in audit.path_evidence if item.subject_id == record.id),
        key=lambda item: (item.kind, item.path.casefold(), item.id),
    )
    for item in related_paths:
        typer.echo(
            f"- Related {_human_label(item.kind)}: {safe_display_text(item.path)} — "
            f"{_bytes(item.size_bytes)} on {item.storage_location.value} storage"
        )
        if item.backup_excluded is True:
            typer.echo("  Backup fact: excluded from Time Machine.")
        elif item.backup_excluded is False:
            typer.echo(
                "  Backup fact: not excluded from Time Machine; this does not prove coverage."
            )
        else:
            typer.echo("  Backup fact: Time Machine exclusion is unknown.")

    subject_findings = tuple(
        finding for finding in audit.findings if finding.subject_id == record.id
    )
    verified = tuple(
        finding for finding in subject_findings if finding.basis is ClaimBasis.VERIFIED
    )
    inferred = tuple(
        finding for finding in subject_findings if finding.basis is ClaimBasis.INFERRED
    )
    confirmed = tuple(
        finding for finding in subject_findings if finding.basis is ClaimBasis.USER_CONFIRMED
    )
    unknown = tuple(finding for finding in subject_findings if finding.basis is ClaimBasis.UNKNOWN)
    _echo_findings(verified)
    typer.echo("\nInferred findings")
    _echo_findings(inferred)
    assessment = next(
        (item for item in audit.catalog_assessments if item.subject_id == record.id),
        None,
    )
    if assessment is not None:
        typer.echo(f"- Catalog roles: {', '.join(map(safe_display_text, assessment.roles))}")
        if assessment.unique_capabilities:
            typer.echo(
                "- Unique capabilities: "
                f"{', '.join(map(safe_display_text, assessment.unique_capabilities))}"
            )
        typer.echo(f"- Learning value: {_human_label(assessment.learning_value.value)}")
        typer.echo(f"  {safe_display_text(assessment.learning_statement)}")
    records_by_id = {item.id: item for item in audit.software}
    for relation in audit.overlaps:
        if record.id not in {relation.left_subject_id, relation.right_subject_id}:
            continue
        other_id = (
            relation.right_subject_id
            if relation.left_subject_id == record.id
            else relation.left_subject_id
        )
        other = records_by_id.get(other_id)
        other_name = other.display_name if other is not None else other_id
        typer.echo(
            f"- Related overlap: {safe_display_text(other_name)} — "
            f"{_human_label(relation.category.value)}"
        )
    typer.echo("\nUser-confirmed findings")
    _echo_findings(confirmed)
    typer.echo("\nUnknowns and limitations")
    _echo_findings(unknown)
    if audit.backup is None:
        typer.echo("- Time Machine configuration is unknown.")
    else:
        typer.echo(f"- Time Machine configured: {_tri_state(audit.backup.configured)}")
        for limitation in audit.backup.limitations:
            typer.echo(f"- Backup limitation: {safe_display_text(limitation)}")
    typer.echo("- Backup coverage: Not verified.")
    guidance = tuple(item for item in audit.recommendations if record.id in item.subject_ids)
    if guidance:
        for item in guidance:
            typer.echo(
                f"Guarded guidance: {_human_label(item.action.value)} — "
                f"{safe_display_text(item.statement)}"
            )
            for prerequisite in item.prerequisites:
                typer.echo(f"- Prerequisite: {safe_display_text(prerequisite)}")
            for limitation in item.limitations:
                typer.echo(f"- Guidance limitation: {safe_display_text(limitation)}")
    else:
        typer.echo(
            "Recommendation: Not available until overlap, learning-value, and cleanup preflight complete."
        )
    typer.echo("\nThis command is read-only. MacWise did not change this Mac.")


@app.command(help=HELP["compare"])
def compare(
    names: Annotated[list[str], typer.Argument(help="One or more installed names.")],
) -> None:
    if len(names) < 2:
        typer.echo("MacWise compare requires at least two installed names.")
        raise typer.Exit(2)
    audit = _audit()
    selected = tuple(_resolve_record(audit, name) for name in names)
    if len({record.id for record in selected}) != len(selected):
        typer.echo("Choose distinct installed items for a comparison.")
        raise typer.Exit(2)

    assessments = {item.subject_id: item for item in audit.catalog_assessments}
    records_by_id = {record.id: record for record in audit.software}
    typer.echo("Role-aware comparison\n")
    for record in selected:
        typer.echo(f"- {_record_label(record)}")
        assessment = assessments.get(record.id)
        if assessment is None:
            typer.echo("  Catalog role: unknown")
            typer.echo("  Learning value: unknown")
        else:
            typer.echo(f"  Catalog roles: {', '.join(map(safe_display_text, assessment.roles))}")
            typer.echo(f"  Learning value: {_human_label(assessment.learning_value.value)}")
        finding = _usage_finding(audit, record.id)
        if finding is None or finding.usage_label is None:
            typer.echo("  Usage: no reliable evidence (unknown, unknown confidence)")
        else:
            typer.echo(
                f"  Usage: {_human_label(finding.usage_label.value)} "
                f"({_human_label(finding.basis.value)}, {finding.confidence.value} confidence)"
            )

    typer.echo(f"\n{_actual_use_comparison(audit, selected)}")

    for left, right in combinations(selected, 2):
        typer.echo(
            f"\n{safe_display_text(left.display_name)} and {safe_display_text(right.display_name)}"
        )
        relation = _relation_for(audit, left.id, right.id)
        if relation is None:
            typer.echo("Relationship unknown.")
            typer.echo("MacWise will not infer a category from names alone.")
            continue
        typer.echo(f"Relationship: {_human_label(relation.category.value)}")
        typer.echo(f"Reason: {safe_display_text(relation.statement)}")
        if relation.shared_capabilities:
            typer.echo(
                "Shared capabilities: "
                f"{', '.join(map(safe_display_text, relation.shared_capabilities))}"
            )
        left_name = records_by_id.get(relation.left_subject_id)
        right_name = records_by_id.get(relation.right_subject_id)
        if relation.left_unique_capabilities:
            label = left_name.display_name if left_name is not None else relation.left_subject_id
            values = ", ".join(
                _human_label(value).capitalize() for value in relation.left_unique_capabilities
            )
            typer.echo(f"{safe_display_text(label)} unique: {values}")
        if relation.right_unique_capabilities:
            label = right_name.display_name if right_name is not None else relation.right_subject_id
            values = ", ".join(
                _human_label(value).capitalize() for value in relation.right_unique_capabilities
            )
            typer.echo(f"{safe_display_text(label)} unique: {values}")

    selected_ids = {record.id for record in selected}
    guidance = tuple(
        item for item in audit.recommendations if set(item.subject_ids) <= selected_ids
    )
    typer.echo("\nGuarded guidance")
    if not guidance:
        typer.echo("- No recommendation is available for the selected items.")
    for item in guidance:
        typer.echo(
            f"- {_human_label(item.action.value).capitalize()}: {safe_display_text(item.statement)}"
        )
        for prerequisite in item.prerequisites:
            typer.echo(f"  Prerequisite: {safe_display_text(prerequisite)}")
        for limitation in item.limitations:
            typer.echo(f"  Limitation: {safe_display_text(limitation)}")
    typer.echo("\nThis comparison is read-only and does not authorize removal or other changes.")


@app.command(help=HELP["startup"])
def startup() -> None:
    audit = _audit()
    records = {record.id: record for record in audit.software}
    typer.echo("Startup and background items\n")
    startup_items = sorted(
        audit.startup,
        key=lambda item: (item.kind.value, item.label.casefold(), item.id),
    )
    if not startup_items:
        typer.echo("No startup or background records were collected.")
    for item in startup_items:
        owners = [
            safe_display_text(records[owner_id].display_name)
            for owner_id in item.owner_software_ids
            if owner_id in records
        ]
        typer.echo(f"- {safe_display_text(item.label)} — {_human_label(item.kind.value)}")
        typer.echo(f"  Owner: {', '.join(owners) if owners else 'unknown'}")
        typer.echo(f"  Enabled: {_tri_state(item.enabled)}")
        typer.echo(f"  Running: {_tri_state(item.running)}")
        if item.source_path:
            typer.echo(f"  Source: {safe_display_text(item.source_path)}")
    typer.echo("This command is read-only. MacWise did not change this Mac.")


@app.command(help=HELP["storage"])
def storage() -> None:
    audit = _audit()
    typer.echo("Storage volumes\n")
    for volume in audit.volumes:
        mount = safe_display_text(volume.mount_point or "unmounted")
        typer.echo(
            f"- {safe_display_text(volume.name)}: {volume.location.value}, "
            f"{volume.free_bytes or 0} bytes free, {mount}"
        )
    if not audit.volumes:
        typer.echo("No storage metadata was collected.")
    typer.echo("\nThis command is read-only. MacWise did not change this Mac.")


@app.command(help=HELP["backups"])
def backups() -> None:
    audit = _audit()
    backup = audit.backup
    volumes = {volume.id: volume for volume in audit.volumes}
    typer.echo("Time Machine facts\n")
    if backup is None:
        typer.echo("Configured: unknown")
        typer.echo("Available destinations: unknown")
        typer.echo("Last verifiable backup: unknown")
    else:
        typer.echo(f"Configured: {_tri_state(backup.configured)}")
        if backup.available_destination_volume_ids:
            for volume_id in backup.available_destination_volume_ids:
                destination = volumes.get(volume_id)
                label = destination.name if destination is not None else volume_id
                typer.echo(f"Available destination: {safe_display_text(label)}")
        else:
            typer.echo("Available destination: none observed")
        latest = backup.last_backup_at.isoformat() if backup.last_backup_at else "unknown"
        typer.echo(f"Last verifiable backup: {latest}")

    typer.echo("\nRelated-path exclusion observations")
    if not audit.path_evidence:
        typer.echo("- No related paths were measured.")
    for item in sorted(audit.path_evidence, key=lambda value: (value.path.casefold(), value.id)):
        if item.backup_excluded is True:
            state = "excluded from Time Machine"
        elif item.backup_excluded is False:
            state = "not excluded from Time Machine"
        else:
            state = "Time Machine exclusion unknown"
        typer.echo(f"- {safe_display_text(item.path)}: {state}; this does not prove coverage.")
    if backup is not None:
        for limitation in backup.limitations:
            typer.echo(f"Limitation: {safe_display_text(limitation)}")
    typer.echo("\nBackup coverage: Not verified.")
    typer.echo("This command is read-only. MacWise did not change this Mac.")


@plan_app.callback()
def plan_root(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        _show_active_plan()


@plan_app.command("add", help=HELP["plan_add"])
def plan_add(
    name: Annotated[str, typer.Argument(help="One reviewed, unambiguous item name.")],
    include_startup: Annotated[
        bool,
        typer.Option(
            "--include-startup",
            help="Also preview supported owned startup changes before removal.",
        ),
    ] = False,
) -> None:
    store = _plan_store_factory()
    try:
        current = store.active()
    except PlanStoreError:
        _plan_store_failure(writing=False)
    audit = _audit()
    record = _resolve_record(audit, name)
    result = add_candidate(
        current,
        audit,
        record.id,
        clock=_planning_clock,
        plan_id_factory=_plan_id_factory,
        trash_root=_trash_root_factory(),
        include_startup=include_startup,
    )
    if result.changed:
        try:
            store.append(result.plan)
        except PlanStoreError:
            _plan_store_failure(writing=True)
        typer.echo(
            f"Added {safe_display_text(record.display_name)} to cleanup plan "
            f"revision {result.plan.revision}.\n"
        )
    else:
        typer.echo(
            f"{safe_display_text(record.display_name)} already appears in cleanup plan "
            f"revision {result.plan.revision}.\n"
        )
    _echo_plan(result.plan)


@plan_app.command("show", help=HELP["plan_show"])
def plan_show() -> None:
    _show_active_plan()


@app.command("apply", help=HELP["apply"])
def apply_plan(
    approve: Annotated[
        str | None,
        typer.Option(
            "--approve",
            help="Exact APPLY fingerprint phrase shown after fresh revalidation.",
        ),
    ] = None,
) -> None:
    """Revalidate and apply one reviewed schema-2 plan after exact approval."""
    plan = _active_plan()
    if plan is None:
        typer.echo("No active cleanup plan exists to apply.")
        typer.echo("No changes were made.\n\nNext:\n  macwise plan add NAME")
        raise typer.Exit(2)
    if plan.schema_version != 2:
        typer.echo("This cleanup plan uses an older preview schema and cannot be applied.")
        typer.echo("No changes were made.\n\nNext:\n  create a fresh plan revision")
        raise typer.Exit(2)
    if plan.eligibility is not PlanEligibility.PREVIEW_READY:
        typer.echo("This cleanup plan is blocked and cannot be applied.")
        typer.echo("No changes were made.\n\nNext:\n  macwise plan show")
        raise typer.Exit(2)

    try:
        fresh_audit = _audit()
        prepared = _execution_preparer(plan, fresh_audit)
    except RevalidationError:
        typer.echo("Fresh host evidence no longer matches this cleanup plan safely.")
        typer.echo("No changes were made.\n\nNext:\n  create and review a fresh plan revision")
        raise typer.Exit(2) from None

    _echo_plan(plan)
    typer.echo("\nAction-time verification")
    typer.echo(f"- {len(prepared.actions)} ordered action(s) were freshly reconstructed.")
    typer.echo("- MacWise will stop on the first action or verification failure.")
    typer.echo("- Related user data remains preserved.")
    phrase = apply_approval_phrase(prepared.plan_digest)
    typer.echo(f"\nApproval required: {phrase}")
    supplied = approve
    if supplied is None and _is_interactive():
        supplied = typer.prompt("Type the exact approval phrase")
    if supplied is None:
        typer.echo(f"Run again with --approve '{phrase}' after reviewing this output.")
        typer.echo("No changes were made.")
        raise typer.Exit(2)
    try:
        require_approval(prepared.plan_digest, supplied, verb="APPLY")
    except ApprovalError:
        typer.echo("The approval phrase does not exactly match the reviewed plan fingerprint.")
        typer.echo("No changes were made.")
        raise typer.Exit(2) from None

    service = _execution_service_factory(_plan_store_factory())
    try:
        result = service.apply(
            prepared,
            approval=supplied,
        )
    except (ExecutionServiceError, ExecutionStoreError):
        try:
            recovery = service.active()
        except ExecutionStoreError:
            recovery = None
        if recovery is not None:
            typer.echo(
                f"Execution stopped with durable state: {_human_label(recovery.state.value)}."
            )
        else:
            typer.echo("Execution did not complete safely; recovery state is unavailable.")
        typer.echo("Next: run macwise doctor before retrying or creating a new plan.")
        raise typer.Exit(2) from None
    if result.state is not ExecutionState.SUCCEEDED:
        typer.echo(f"Execution stopped with state: {_human_label(result.state.value)}.")
        typer.echo("Next: run macwise undo or macwise doctor before any new plan.")
        raise typer.Exit(2)
    typer.echo("\nExecution succeeded and every action has fresh verified after-state evidence.")
    typer.echo("Next: run macwise undo to review the separately approved reverse actions.")


@app.command(help=HELP["undo"])
def undo(
    approve: Annotated[
        str | None,
        typer.Option(
            "--approve",
            help="Exact UNDO fingerprint phrase shown for the active verified run.",
        ),
    ] = None,
) -> None:
    """Reverse the latest fully verified run after separate exact approval."""
    try:
        service = _execution_service_factory(_plan_store_factory())
        active = service.undoable()
    except (ExecutionStoreError, PlanStoreError):
        typer.echo("MacWise could not read recovery state safely.")
        typer.echo("No undo action was attempted.\n\nNext:\n  macwise doctor")
        raise typer.Exit(2) from None
    if active is None:
        typer.echo("No MacWise execution manifest is available to undo.")
        typer.echo("No changes were made.\n\nNext:\n  macwise plan show")
        raise typer.Exit(2)
    undoable_states = {
        ExecutionState.SUCCEEDED,
        ExecutionState.PARTIAL,
        ExecutionState.VERIFICATION_FAILED,
        ExecutionState.UNDO_PARTIAL,
        ExecutionState.IN_PROGRESS,
        ExecutionState.UNDO_IN_PROGRESS,
        ExecutionState.INTERRUPTED,
    }
    if active.state not in undoable_states:
        typer.echo(
            f"The active execution state is {_human_label(active.state.value)} and is not "
            "a run with safely observed reverse actions."
        )
        typer.echo("No undo action was attempted.\n\nNext:\n  macwise doctor")
        raise typer.Exit(2)

    typer.echo("Undo review\n")
    recoverable_actions = tuple(
        action
        for action in reversed(active.actions)
        if (
            action.after is not None
            and action.state
            in {
                ActionState.VERIFIED,
                ActionState.FAILED,
                ActionState.UNDO_FAILED,
            }
        )
        or action.state in {ActionState.IN_PROGRESS, ActionState.UNDO_IN_PROGRESS}
    )
    if not recoverable_actions:
        typer.echo("The active execution has no safely observed inverse action.")
        typer.echo("No undo action was attempted.\n\nNext:\n  macwise doctor")
        raise typer.Exit(2)
    if active.state in {
        ExecutionState.IN_PROGRESS,
        ExecutionState.UNDO_IN_PROGRESS,
        ExecutionState.INTERRUPTED,
    }:
        typer.echo(
            "Fresh host evidence will first classify each interrupted action; ambiguous "
            "state will remain journaled and stop recovery."
        )
    for action in recoverable_actions:
        typer.echo(f"- Reverse action {action.sequence}: {_human_label(action.inverse.kind.value)}")
    typer.echo("Homebrew reinstalls are best-effort and may not restore the captured version.")
    phrase = undo_approval_phrase(execution_digest(active))
    typer.echo(f"\nApproval required: {phrase}")
    supplied = approve
    if supplied is None and _is_interactive():
        supplied = typer.prompt("Type the exact approval phrase")
    if supplied is None:
        typer.echo(f"Run again with --approve '{phrase}' after reviewing this output.")
        typer.echo("No undo action was attempted.")
        raise typer.Exit(2)
    try:
        require_approval(execution_digest(active), supplied, verb="UNDO")
    except ApprovalError:
        typer.echo("The approval phrase does not exactly match the active run fingerprint.")
        typer.echo("No undo action was attempted.")
        raise typer.Exit(2) from None
    try:
        result = service.undo(approval=supplied)
    except (ExecutionServiceError, ExecutionStoreError):
        typer.echo("Undo did not complete safely; recovery state was preserved.")
        typer.echo("Next: run macwise doctor before retrying or creating a new plan.")
        raise typer.Exit(2) from None
    if result.state is ExecutionState.UNDO_PARTIAL:
        typer.echo("Undo restored the safely observed actions, but ambiguity remains.")
        typer.echo("Next: run macwise doctor before retrying or creating a new plan.")
        raise typer.Exit(2)
    if result.state is not ExecutionState.UNDONE:
        typer.echo(f"Undo stopped with state: {_human_label(result.state.value)}.")
        typer.echo("Next: run macwise doctor before retrying.")
        raise typer.Exit(2)
    typer.echo("\nUndo succeeded and every reverse action was verified.")
    typer.echo("Next: run macwise scan for a fresh read-only view.")


@app.command(help=HELP["doctor"])
def doctor() -> None:
    typer.echo("MacWise doctor\n")
    typer.echo(f"Operating system: {platform.system()} {platform.release()}")
    typer.echo(f"Python: {platform.python_version()}")
    brew = "available" if resolve_executable(ReadCommand.BREW) else "not found (optional)"
    typer.echo(f"Homebrew: {brew}")
    try:
        service = _execution_service_factory(_plan_store_factory())
        recovery = service.active()
        historical = service.undoable()
    except (ExecutionStoreError, PlanStoreError):
        typer.echo("Execution recovery journal: unsafe or unreadable")
    else:
        if recovery is None:
            typer.echo("Execution recovery journal: no active run")
        else:
            typer.echo(
                "Execution recovery journal: "
                f"{_human_label(recovery.state.value)} "
                f"({safe_display_text(recovery.run_id)})"
            )
            for action in recovery.actions:
                typer.echo(
                    f"  Action {action.sequence}: {_human_label(action.state.value)} — "
                    f"{_human_label(action.kind.value)}"
                )
            if recovery.state in {
                ExecutionState.SUCCEEDED,
                ExecutionState.PARTIAL,
                ExecutionState.VERIFICATION_FAILED,
                ExecutionState.UNDO_PARTIAL,
            }:
                typer.echo("  Recovery: run macwise undo to review safely observed inverses.")
            elif recovery.state in {
                ExecutionState.IN_PROGRESS,
                ExecutionState.UNDO_IN_PROGRESS,
                ExecutionState.INTERRUPTED,
            }:
                typer.echo(
                    "  Recovery: run macwise undo to review bounded fresh-state "
                    "classification; do not retry or create a new plan."
                )
            if historical is not None and (
                historical.run_id,
                historical.manifest_revision,
            ) != (recovery.run_id, recovery.manifest_revision):
                typer.echo(
                    "  Historical recovery: an older run still has safely observed "
                    "inverse actions; run macwise undo to review it."
                )
    typer.echo("Collectors are read-only. Run macwise scan for a complete collection check.")


@setup_app.callback()
def setup_root(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@setup_app.command("codex", help=HELP["setup_codex"])
def setup_codex() -> None:
    result = _codex_setup_factory().install()
    if result.status is SetupStatus.INSTALLED:
        typer.echo("The MacWise Codex experience is installed.")
    elif result.status is SetupStatus.UPDATED:
        typer.echo("The MacWise Codex experience is updated.")
    elif result.status is SetupStatus.ALREADY_CURRENT:
        typer.echo("The MacWise Codex experience is already current.")
    else:
        typer.echo(safe_display_text(result.message))
        if result.recovery:
            typer.echo(safe_display_text(result.recovery))
        raise typer.Exit(2)
    typer.echo("Start a new Codex session, then type $macwise.")


@codex_app.command("serve", hidden=True)
def codex_serve() -> None:
    """Run the internal read-only local protocol server."""
    _codex_stdio_runner()


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
    elif choice == 9:
        typer.echo("Undo recovery requires a separate approval.")
        typer.echo("Run macwise undo to review the active manifest and exact reverse actions.")
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
    choice = typer.prompt("Choose 1-10", type=int)
    if choice not in range(1, 11):
        typer.echo("Choose a number from 1 through 10.")
        raise typer.Exit(2)
    _guided_action(choice, ctx)


def main() -> None:
    """Run the MacWise CLI."""
    app()
