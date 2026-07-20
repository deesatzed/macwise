"""Read-only independent observations used as reference receipts."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from macwise_eval.system import CommandResult


class CommandRunner(Protocol):
    """Minimal command boundary needed by reference collectors."""

    def run(self, executable: str, *arguments: str) -> CommandResult: ...


@dataclass(frozen=True)
class ReferenceObservation:
    """One independently captured fact bundle and its correlation limitation."""

    source: str
    source_correlated: bool
    document: Mapping[str, object]
    limitations: tuple[str, ...] = ()


def _command_document(result: CommandResult) -> dict[str, object]:
    return {
        "returncode": result.returncode,
        "stderr": result.stderr,
        "stdout": result.stdout,
        "truncated": result.truncated,
        "error": result.error,
    }


def _applications(app_roots: tuple[Path, ...]) -> ReferenceObservation:
    bundles: list[str] = []
    for root in app_roots:
        if root.is_symlink() or not root.is_dir():
            continue
        bundles.extend(
            sorted(path.name for path in root.iterdir() if path.is_dir() and path.suffix == ".app")
        )
    return ReferenceObservation(
        source="approved-root traversal",
        source_correlated=False,
        document={"bundle_count": len(bundles), "bundle_names": tuple(bundles)},
    )


def collect_reference_observations(
    runner: CommandRunner,
    *,
    app_roots: tuple[Path, ...],
    user_id: str | None = None,
) -> dict[str, ReferenceObservation]:
    """Collect fixed read-only reference observations without product imports or execution."""
    effective_user_id = user_id or str(os.getuid())
    brew = runner.run("/opt/homebrew/bin/brew", "list", "--formula")
    if brew.returncode is None:
        brew = runner.run("/usr/local/bin/brew", "list", "--formula")
    results = {
        "applications": _applications(app_roots),
        "backups": ReferenceObservation(
            source="tmutil latestbackup",
            source_correlated=True,
            document=_command_document(runner.run("/usr/bin/tmutil", "latestbackup")),
            limitations=("A latest backup path does not prove application-level recoverability.",),
        ),
        "homebrew": ReferenceObservation(
            source="brew list --formula",
            source_correlated=True,
            document=_command_document(brew),
            limitations=("Installed formula names do not establish dependency safety alone.",),
        ),
        "startup": ReferenceObservation(
            source="launchctl print-disabled",
            source_correlated=True,
            document=_command_document(
                runner.run("/bin/launchctl", "print-disabled", f"user/{effective_user_id}")
            ),
        ),
        "storage": ReferenceObservation(
            source="df -kP",
            source_correlated=True,
            document=_command_document(runner.run("/bin/df", "-kP")),
            limitations=("Mounted filesystem capacity does not measure unmounted volumes.",),
        ),
    }
    return dict(sorted(results.items()))
