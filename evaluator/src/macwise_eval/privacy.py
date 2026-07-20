"""Conservative, non-mutating disclosure checks for evaluator artifacts."""

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from macwise_eval.models import CapsuleManifest, DisclosureClass

MAX_SCAN_BYTES = 2 * 1024 * 1024


class DisclosureFindingKind(StrEnum):
    """A category of material that requires private handling or human review."""

    HOME_PATH = "home_path"
    VOLUME_PATH = "volume_path"
    HOSTNAME = "hostname"
    SERIAL_SHAPED = "serial_shaped"
    SECRET_SHAPED = "secret_shaped"
    CONTROL_CHARACTER = "control_character"
    PROMPT_SHAPED = "prompt_shaped"
    INVENTORY_SHAPED = "inventory_shaped"


@dataclass(frozen=True)
class DisclosureFinding:
    """A safe finding that names the category and location but never repeats sensitive text."""

    kind: DisclosureFindingKind
    line: int
    column: int


_HOME_PATH = re.compile(r"/(?:Users|home)/[^/\s\"']+", re.IGNORECASE)
_VOLUME_PATH = re.compile(r"/Volumes/[^/\s\"']+", re.IGNORECASE)
_SERIAL_SHAPED = re.compile(r"\b[A-Z0-9]{11,14}\b")
_SECRET_SHAPED = re.compile(
    r"(?i)\"?(?:api[_-]?key|password|private[_-]?key|token)\"?\s*[:=]\s*['\"][^'\"]+['\"]"
)
_CONTROL_CHARACTER = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F\u202A-\u202E\u2066-\u2069]")
_PROMPT_SHAPED = re.compile(
    r"(?i)(?:ignore\s+(?:all\s+)?previous\s+instructions|system\s+message|assistant\s*:|developer\s*:)",
)
_INVENTORY_SHAPED = re.compile(r'(?i)"(?:bundle_identifier|install_path|software_inventory)"\s*:')


def _line_and_column(text: str, offset: int) -> tuple[int, int]:
    """Map a string offset to a one-based line and column without retaining its value."""
    line = text.count("\n", 0, offset) + 1
    previous_newline = text.rfind("\n", 0, offset)
    return line, offset - previous_newline


def _find(
    pattern: re.Pattern[str], kind: DisclosureFindingKind, text: str
) -> list[DisclosureFinding]:
    return [
        DisclosureFinding(
            kind=kind,
            line=_line_and_column(text, match.start())[0],
            column=_line_and_column(text, match.start())[1],
        )
        for match in pattern.finditer(text)
    ]


def _known_value_findings(
    text: str,
    values: tuple[str, ...],
    kind: DisclosureFindingKind,
) -> list[DisclosureFinding]:
    findings: list[DisclosureFinding] = []
    for value in values:
        if not value:
            continue
        for match in re.finditer(re.escape(value), text):
            line, column = _line_and_column(text, match.start())
            findings.append(DisclosureFinding(kind=kind, line=line, column=column))
    return findings


def scan_text(
    text: str,
    *,
    known_usernames: tuple[str, ...] = (),
    known_hostnames: tuple[str, ...] = (),
) -> tuple[DisclosureFinding, ...]:
    """Return disclosure categories found in text without modifying or echoing its contents."""
    findings = [
        *_find(_HOME_PATH, DisclosureFindingKind.HOME_PATH, text),
        *_find(_VOLUME_PATH, DisclosureFindingKind.VOLUME_PATH, text),
        *_find(_SERIAL_SHAPED, DisclosureFindingKind.SERIAL_SHAPED, text),
        *_find(_SECRET_SHAPED, DisclosureFindingKind.SECRET_SHAPED, text),
        *_find(_CONTROL_CHARACTER, DisclosureFindingKind.CONTROL_CHARACTER, text),
        *_find(_PROMPT_SHAPED, DisclosureFindingKind.PROMPT_SHAPED, text),
        *_find(_INVENTORY_SHAPED, DisclosureFindingKind.INVENTORY_SHAPED, text),
        *_known_value_findings(text, known_usernames, DisclosureFindingKind.HOSTNAME),
        *_known_value_findings(text, known_hostnames, DisclosureFindingKind.HOSTNAME),
    ]
    return tuple(
        sorted(set(findings), key=lambda finding: (finding.line, finding.column, finding.kind))
    )


def _scan_directory(
    capsule_dir: Path,
    *,
    known_usernames: tuple[str, ...],
    known_hostnames: tuple[str, ...],
) -> tuple[DisclosureFinding, ...]:
    findings: list[DisclosureFinding] = []
    for path in sorted(capsule_dir.rglob("*")):
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_SCAN_BYTES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        findings.extend(
            scan_text(text, known_usernames=known_usernames, known_hostnames=known_hostnames)
        )
    return tuple(
        sorted(set(findings), key=lambda finding: (finding.line, finding.column, finding.kind))
    )


def require_public_disclosure(
    capsule_dir: Path,
    manifest: CapsuleManifest,
    *,
    known_usernames: tuple[str, ...] = (),
    known_hostnames: tuple[str, ...] = (),
) -> None:
    """Refuse public disclosure unless metadata and all readable artifacts pass review."""
    if manifest.disclosure is not DisclosureClass.PUBLIC:
        raise ValueError("public disclosure requires a public capsule")
    if not manifest.reviewed_sanitized:
        raise ValueError("public disclosure requires reviewed_sanitized")
    findings = _scan_directory(
        capsule_dir,
        known_usernames=known_usernames,
        known_hostnames=known_hostnames,
    )
    if findings:
        kinds = ", ".join(sorted({finding.kind.value for finding in findings}))
        raise ValueError(f"public disclosure blocked: {kinds}")
