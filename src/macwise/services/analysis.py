"""Deterministic, evidence-linked Phase 2 analysis."""

from collections.abc import Sequence
from datetime import datetime, timedelta

from macwise.models import (
    ClaimBasis,
    Finding,
    FindingTopic,
    InstallRole,
    PathEvidence,
    Reliability,
    SoftwareRecord,
    StartupRecord,
    UsageLabel,
)

RECENT_WINDOW = timedelta(days=30)
STALE_WINDOW = timedelta(days=180)


def _spotlight_last_used(record: SoftwareRecord) -> datetime | None:
    for evidence in record.evidence:
        if evidence.kind != "spotlight_last_used" or not isinstance(evidence.value, str):
            continue
        try:
            parsed = datetime.fromisoformat(evidence.value.replace("Z", "+00:00"))
        except ValueError:
            continue
        if parsed.tzinfo is not None:
            return parsed
    return None


def _finding(
    record: SoftwareRecord,
    *,
    label: UsageLabel,
    statement: str,
    basis: ClaimBasis,
    confidence: Reliability,
    evidence_kinds: Sequence[str] = (),
    limitations: Sequence[str] = (),
) -> Finding:
    return Finding(
        subject_id=record.id,
        topic=FindingTopic.USAGE,
        statement=statement,
        basis=basis,
        confidence=confidence,
        usage_label=label,
        evidence_kinds=tuple(dict.fromkeys(evidence_kinds)),
        limitations=tuple(limitations),
    )


def analyze_usage(
    software: Sequence[SoftwareRecord],
    *,
    startup: Sequence[StartupRecord],
    path_evidence: Sequence[PathEvidence],
    collected_at: datetime,
    user_confirmed_unused: Sequence[str] = (),
) -> tuple[Finding, ...]:
    """Assign one cautious usage label per record from ordered evidence signals."""
    confirmed = set(user_confirmed_unused)
    startup_by_owner: dict[str, list[StartupRecord]] = {}
    for item in startup:
        for owner_id in item.owner_software_ids:
            startup_by_owner.setdefault(owner_id, []).append(item)
    paths_by_subject: dict[str, list[PathEvidence]] = {}
    for item in path_evidence:
        paths_by_subject.setdefault(item.subject_id, []).append(item)

    findings: list[Finding] = []
    for record in software:
        owned_startup = startup_by_owner.get(record.id, [])
        related_paths = paths_by_subject.get(record.id, [])
        last_used_at = _spotlight_last_used(record)

        if record.id in confirmed:
            findings.append(
                _finding(
                    record,
                    label=UsageLabel.USER_CONFIRMED_UNUSED,
                    statement="The user confirmed this item is unused.",
                    basis=ClaimBasis.USER_CONFIRMED,
                    confidence=Reliability.HIGH,
                    evidence_kinds=("user_confirmation",),
                    limitations=("User confirmation does not authorize removal.",),
                )
            )
            continue

        active_startup = [item for item in owned_startup if item.running is True]
        if record.running is True or active_startup:
            evidence_kinds = ["application_process_state"] if record.running is True else []
            evidence_kinds.extend(
                evidence.kind for item in active_startup for evidence in item.evidence
            )
            if active_startup and not evidence_kinds:
                evidence_kinds.append("startup_record")
            findings.append(
                _finding(
                    record,
                    label=UsageLabel.ACTIVELY_USED,
                    statement="Currently running or has an active owned background component.",
                    basis=ClaimBasis.VERIFIED,
                    confidence=Reliability.HIGH,
                    evidence_kinds=evidence_kinds,
                    limitations=("This is a point-in-time activity signal.",),
                )
            )
            continue

        if last_used_at is not None and collected_at - last_used_at <= RECENT_WINDOW:
            findings.append(
                _finding(
                    record,
                    label=UsageLabel.RECENTLY_USED,
                    statement="Spotlight recorded use within the last 30 days.",
                    basis=ClaimBasis.VERIFIED,
                    confidence=Reliability.MEDIUM,
                    evidence_kinds=("spotlight_last_used",),
                    limitations=("Spotlight metadata can be absent, stale, or reset.",),
                )
            )
            continue

        if (
            record.install_role is InstallRole.DEPENDENCY
            or record.reverse_dependencies
            or record.project_references
        ):
            findings.append(
                _finding(
                    record,
                    label=UsageLabel.INDIRECTLY_REQUIRED,
                    statement="Dependency or approved project evidence indicates indirect use.",
                    basis=ClaimBasis.INFERRED,
                    confidence=(
                        Reliability.HIGH
                        if record.reverse_dependencies
                        or record.install_role is InstallRole.DEPENDENCY
                        else Reliability.MEDIUM
                    ),
                    evidence_kinds=("homebrew_formula_metadata",),
                    limitations=("Indirect use does not prove direct user interaction.",),
                )
            )
            continue

        recent_paths = [
            item
            for item in related_paths
            if item.last_modified_at is not None
            and collected_at - item.last_modified_at <= RECENT_WINDOW
        ]
        if recent_paths:
            findings.append(
                _finding(
                    record,
                    label=UsageLabel.PROBABLY_USED,
                    statement="A known related-data path changed within the last 30 days.",
                    basis=ClaimBasis.INFERRED,
                    confidence=Reliability.MEDIUM,
                    evidence_kinds=("related_data_path",),
                    limitations=(
                        "File activity can be caused by background updates or maintenance.",
                    ),
                )
            )
            continue

        if owned_startup:
            findings.append(
                _finding(
                    record,
                    label=UsageLabel.CONFIGURED_BUT_IDLE,
                    statement="An owned startup component is configured but was not observed running.",
                    basis=ClaimBasis.INFERRED,
                    confidence=Reliability.MEDIUM,
                    evidence_kinds=("startup_record",),
                    limitations=("Current enablement can be overridden outside the plist.",),
                )
            )
            continue

        if last_used_at is not None and collected_at - last_used_at > STALE_WINDOW:
            findings.append(
                _finding(
                    record,
                    label=UsageLabel.POSSIBLY_UNUSED,
                    statement=(
                        "The available last-use timestamp is older than 180 days and no "
                        "stronger usage signal was found."
                    ),
                    basis=ClaimBasis.INFERRED,
                    confidence=Reliability.LOW,
                    evidence_kinds=("spotlight_last_used",),
                    limitations=("Old metadata is not proof that the item is unused.",),
                )
            )
            continue

        findings.append(
            _finding(
                record,
                label=UsageLabel.NO_RELIABLE_EVIDENCE,
                statement="No reliable usage evidence was found.",
                basis=ClaimBasis.UNKNOWN,
                confidence=Reliability.UNKNOWN,
                limitations=("Missing evidence is not proof of non-use.",),
            )
        )

    return tuple(findings)
