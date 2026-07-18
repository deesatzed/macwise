"""Read-only application facade for the optional Codex integration."""

from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from threading import RLock

from macwise.integration.models import (
    AuditMacRequest,
    Fact,
    FindOverlapsRequest,
    InspectBackupsRequest,
    InspectSoftwareRequest,
    InspectStartupRequest,
    InspectStorageRequest,
    ListSoftwareRequest,
    Operation,
    RemovalPreviewRequest,
    SoftwareSummary,
    ToolError,
    ToolResult,
    ToolStatus,
    Unknown,
)
from macwise.models import (
    AuditDocument,
    CollectorState,
    EntityType,
    FindingTopic,
    SoftwareRecord,
)
from macwise.services.planning import add_candidate
from macwise.text import safe_display_text

AuditProvider = Callable[[], AuditDocument]

_TYPE_PREFIXES = {
    "app": EntityType.APPLICATION,
    "application": EntityType.APPLICATION,
    "formula": EntityType.HOMEBREW_FORMULA,
    "homebrew_formula": EntityType.HOMEBREW_FORMULA,
    "cask": EntityType.HOMEBREW_CASK,
    "homebrew_cask": EntityType.HOMEBREW_CASK,
}


def _bounded(value: object, limit: int) -> str:
    text = safe_display_text(value)
    if len(text) <= limit:
        return text
    return f"{text[: max(0, limit - 1)]}…"


def _summary(record: SoftwareRecord) -> SoftwareSummary:
    return SoftwareSummary(
        id=_bounded(record.id, 256),
        entity_type=record.entity_type,
        display_name=_bounded(record.display_name, 512),
        version=_bounded(record.version, 256) if record.version else None,
        identifier=_bounded(record.identifier, 512) if record.identifier else None,
        install_role=record.install_role.value,
        storage_location=record.storage_location.value,
    )


def _collector_limitations(audit: AuditDocument) -> tuple[str, ...]:
    return tuple(
        _bounded(limitation, 1024)
        for collector in audit.collectors
        for limitation in collector.limitations
    )


def _result_status(*, limitations: Sequence[str], unknowns: Sequence[Unknown]) -> ToolStatus:
    return ToolStatus.PARTIAL if limitations or unknowns else ToolStatus.OK


def _matches(record: SoftwareRecord, value: str) -> bool:
    folded = value.casefold()
    candidates = (record.id, record.name, record.display_name, record.identifier)
    return any(candidate is not None and candidate.casefold() == folded for candidate in candidates)


def _resolve_identity(
    software: Sequence[SoftwareRecord], identity: str
) -> SoftwareRecord | ToolError:
    direct = [record for record in software if record.id.casefold() == identity.casefold()]
    if len(direct) == 1:
        return direct[0]

    prefix, separator, value = identity.partition(":")
    entity_type = _TYPE_PREFIXES.get(prefix.casefold()) if separator else None
    if entity_type is not None:
        matches = [
            record
            for record in software
            if record.entity_type is entity_type and _matches(record, value)
        ]
    else:
        matches = [record for record in software if _matches(record, identity)]

    if not matches:
        return ToolError(
            code="unknown_identity",
            message="No exact software record matched that identity.",
            recovery=("Run list_software and use an exact returned identity.",),
        )
    if len(matches) > 1:
        return ToolError(
            code="ambiguous_identity",
            message="More than one exact software record matched that identity.",
            recovery=("Use a qualified application:, formula:, or cask: identity.",),
        )
    return matches[0]


def _software_facts(record: SoftwareRecord) -> tuple[Fact, ...]:
    values: list[tuple[str, object, str]] = [
        ("identity", record.id, "observed"),
        ("entity_type", record.entity_type.value, "observed"),
        ("display_name", record.display_name, "observed"),
        ("install_role", record.install_role.value, "observed"),
        ("storage_location", record.storage_location.value, "observed"),
    ]
    optional: tuple[tuple[str, object | None, str], ...] = (
        ("version", record.version, "observed"),
        ("identifier", record.identifier, "observed"),
        ("install_source", record.install_source, "inferred"),
        ("running", record.running, "observed"),
        ("size_bytes", record.size_bytes, "observed"),
    )
    values.extend((topic, value, basis) for topic, value, basis in optional if value is not None)
    return tuple(
        Fact(
            subject_id=_bounded(record.id, 256),
            topic=topic,
            value=_bounded(value, 4096),
            basis=basis,
        )
        for topic, value, basis in values
    )


def _usage_evidence(
    audit: AuditDocument, subject_id: str
) -> tuple[tuple[Fact, ...], tuple[Unknown, ...]]:
    findings = tuple(
        finding
        for finding in audit.findings
        if finding.subject_id == subject_id and finding.topic is FindingTopic.USAGE
    )
    if not findings:
        return (), (
            Unknown(
                subject_id=_bounded(subject_id, 256),
                topic="usage",
                reason="No reliable use evidence was found.",
            ),
        )
    return (
        tuple(
            Fact(
                subject_id=_bounded(subject_id, 256),
                topic="usage",
                value=_bounded(finding.statement, 4096),
                basis=finding.basis.value,
            )
            for finding in findings
        ),
        (),
    )


class CodexReadService:
    """Serve a consistent in-memory audit without exposing mutation services."""

    def __init__(self, *, audit_provider: AuditProvider) -> None:
        self._audit_provider = audit_provider
        self._lock = RLock()
        self._audit: AuditDocument | None = None

    def _snapshot(self, *, refresh: bool = False) -> AuditDocument:
        with self._lock:
            if self._audit is None or refresh:
                self._audit = self._audit_provider()
            return self._audit

    def audit_mac(self, request: AuditMacRequest) -> ToolResult:
        """Return bounded health/count facts for one in-memory audit snapshot."""
        audit = self._snapshot(refresh=request.refresh)
        limitations = _collector_limitations(audit)
        unavailable = tuple(
            Unknown(
                topic=_bounded(collector.collector, 128),
                reason=f"The {safe_display_text(collector.collector)} collector is {collector.state.value}.",
            )
            for collector in audit.collectors
            if collector.state is not CollectorState.COMPLETE
        )
        facts = (
            Fact(topic="software_count", value=str(len(audit.software))),
            Fact(topic="volume_count", value=str(len(audit.volumes))),
            Fact(topic="startup_count", value=str(len(audit.startup))),
            *(
                Fact(
                    topic=f"collector_{_bounded(collector.collector, 96)}",
                    value=collector.state.value,
                )
                for collector in audit.collectors
            ),
        )
        return ToolResult(
            operation=Operation.AUDIT_MAC,
            status=_result_status(limitations=limitations, unknowns=unavailable),
            audit_id=_bounded(audit.audit_id, 256),
            collected_at=audit.collected_at,
            facts=facts,
            unknowns=unavailable,
            limitations=limitations,
        )

    def list_software(self, request: ListSoftwareRequest) -> ToolResult:
        """Return one stable bounded page of normalized software."""
        audit = self._snapshot()
        records: Iterable[SoftwareRecord] = audit.software
        if request.entity_type is not None:
            records = (record for record in records if record.entity_type is request.entity_type)
        if request.query is not None:
            query = request.query.casefold()
            records = (
                record
                for record in records
                if query in record.name.casefold() or query in record.display_name.casefold()
            )
        ordered = tuple(
            sorted(records, key=lambda record: (record.display_name.casefold(), record.id))
        )
        page = ordered[request.cursor : request.cursor + request.page_size]
        next_cursor = request.cursor + len(page)
        truncated = next_cursor < len(ordered)
        limitations = _collector_limitations(audit)
        return ToolResult(
            operation=Operation.LIST_SOFTWARE,
            status=_result_status(limitations=limitations, unknowns=()),
            audit_id=_bounded(audit.audit_id, 256),
            collected_at=audit.collected_at,
            facts=(Fact(topic="matching_count", value=str(len(ordered))),),
            software=tuple(_summary(record) for record in page),
            limitations=limitations,
            next_cursor=next_cursor if truncated else None,
            truncated=truncated,
        )

    def inspect_software(self, request: InspectSoftwareRequest) -> ToolResult:
        """Return evidence for one exact identity or a bounded refusal."""
        audit = self._snapshot()
        resolved = _resolve_identity(audit.software, request.identity)
        if isinstance(resolved, ToolError):
            return ToolResult(
                operation=Operation.INSPECT_SOFTWARE,
                status=ToolStatus.REFUSED,
                audit_id=_bounded(audit.audit_id, 256),
                collected_at=audit.collected_at,
                errors=(resolved,),
            )
        usage_facts, unknowns = _usage_evidence(audit, resolved.id)
        limitations = _collector_limitations(audit)
        return ToolResult(
            operation=Operation.INSPECT_SOFTWARE,
            status=_result_status(limitations=limitations, unknowns=unknowns),
            audit_id=_bounded(audit.audit_id, 256),
            collected_at=audit.collected_at,
            facts=(*_software_facts(resolved), *usage_facts),
            software=(_summary(resolved),),
            unknowns=unknowns,
            limitations=limitations,
        )

    def find_overlaps(self, request: FindOverlapsRequest) -> ToolResult:
        """Return only catalog-backed relations among exact requested identities."""
        audit = self._snapshot()
        selected_ids: set[str] = set()
        selected_records: list[SoftwareRecord] = []
        for identity in request.identities:
            resolved = _resolve_identity(audit.software, identity)
            if isinstance(resolved, ToolError):
                return ToolResult(
                    operation=Operation.FIND_OVERLAPS,
                    status=ToolStatus.REFUSED,
                    audit_id=_bounded(audit.audit_id, 256),
                    collected_at=audit.collected_at,
                    errors=(resolved,),
                )
            selected_ids.add(resolved.id)
            selected_records.append(resolved)
        relations = tuple(
            relation
            for relation in audit.overlaps
            if not selected_ids
            or (
                relation.left_subject_id in selected_ids
                and relation.right_subject_id in selected_ids
            )
        )
        if not selected_records:
            related_ids = {
                subject_id
                for relation in relations
                for subject_id in (relation.left_subject_id, relation.right_subject_id)
            }
            selected_records = [record for record in audit.software if record.id in related_ids]
        limitations = (
            *_collector_limitations(audit),
            *(
                _bounded(limitation, 1024)
                for relation in relations
                for limitation in relation.limitations
            ),
        )
        facts = tuple(
            Fact(
                subject_id=_bounded(relation.left_subject_id, 256),
                topic=f"overlap_{relation.category.value}",
                value=_bounded(relation.statement, 4096),
                basis=relation.basis.value,
                source="bundled exact-match catalog",
            )
            for relation in relations[:100]
        )
        unknowns = (
            ()
            if relations
            else (
                Unknown(
                    topic="overlap",
                    reason="No exact catalog-backed overlap relation matched this request.",
                ),
            )
        )
        return ToolResult(
            operation=Operation.FIND_OVERLAPS,
            status=_result_status(limitations=limitations, unknowns=unknowns),
            audit_id=_bounded(audit.audit_id, 256),
            collected_at=audit.collected_at,
            facts=facts,
            software=tuple(_summary(record) for record in selected_records[:100]),
            unknowns=unknowns,
            limitations=limitations[:100],
            truncated=len(relations) > 100 or len(selected_records) > 100,
        )

    def inspect_startup(self, request: InspectStartupRequest) -> ToolResult:
        """Return startup evidence without inferring missing enabled/running state."""
        audit = self._snapshot()
        subject_id: str | None = None
        selected: SoftwareRecord | None = None
        if request.identity is not None:
            resolved = _resolve_identity(audit.software, request.identity)
            if isinstance(resolved, ToolError):
                return ToolResult(
                    operation=Operation.INSPECT_STARTUP,
                    status=ToolStatus.REFUSED,
                    audit_id=_bounded(audit.audit_id, 256),
                    collected_at=audit.collected_at,
                    errors=(resolved,),
                )
            subject_id = resolved.id
            selected = resolved
        startup = tuple(
            item
            for item in audit.startup
            if subject_id is None or subject_id in item.owner_software_ids
        )
        facts: list[Fact] = []
        unknowns: list[Unknown] = []
        for item in startup[:100]:
            facts.extend(
                (
                    Fact(
                        subject_id=_bounded(item.id, 256),
                        topic="startup_kind",
                        value=item.kind.value,
                    ),
                    Fact(
                        subject_id=_bounded(item.id, 256),
                        topic="startup_label",
                        value=_bounded(item.label, 4096),
                    ),
                )
            )
            for topic, value in (
                ("startup_enabled", item.enabled),
                ("startup_running", item.running),
            ):
                if value is None:
                    unknowns.append(
                        Unknown(
                            subject_id=_bounded(item.id, 256),
                            topic=topic,
                            reason=f"No authoritative {topic.removeprefix('startup_')} state was collected.",
                        )
                    )
                else:
                    facts.append(
                        Fact(
                            subject_id=_bounded(item.id, 256),
                            topic=topic,
                            value=str(value).lower(),
                        )
                    )
        limitations = _collector_limitations(audit)
        return ToolResult(
            operation=Operation.INSPECT_STARTUP,
            status=_result_status(limitations=limitations, unknowns=unknowns),
            audit_id=_bounded(audit.audit_id, 256),
            collected_at=audit.collected_at,
            facts=tuple(facts),
            software=(_summary(selected),) if selected is not None else (),
            unknowns=tuple(unknowns),
            limitations=limitations,
            truncated=len(startup) > 100,
        )

    def inspect_storage(self, request: InspectStorageRequest) -> ToolResult:
        """Return normalized volume or software-location facts without scanning content."""
        audit = self._snapshot()
        selected: SoftwareRecord | None = None
        facts: list[Fact] = []
        if request.identity is not None:
            resolved = _resolve_identity(audit.software, request.identity)
            if isinstance(resolved, ToolError):
                return ToolResult(
                    operation=Operation.INSPECT_STORAGE,
                    status=ToolStatus.REFUSED,
                    audit_id=_bounded(audit.audit_id, 256),
                    collected_at=audit.collected_at,
                    errors=(resolved,),
                )
            selected = resolved
            facts.extend(
                (
                    Fact(
                        subject_id=_bounded(resolved.id, 256),
                        topic="software_storage_location",
                        value=resolved.storage_location.value,
                    ),
                    Fact(
                        subject_id=_bounded(resolved.id, 256),
                        topic="software_size_bytes",
                        value=str(resolved.size_bytes),
                    )
                    if resolved.size_bytes is not None
                    else Fact(
                        subject_id=_bounded(resolved.id, 256),
                        topic="software_size_bytes",
                        value="unknown",
                        basis="unknown",
                    ),
                )
            )
        else:
            for volume in audit.volumes[:100]:
                facts.extend(
                    (
                        Fact(
                            subject_id=_bounded(volume.id, 256),
                            topic="volume_name",
                            value=_bounded(volume.name, 4096),
                        ),
                        Fact(
                            subject_id=_bounded(volume.id, 256),
                            topic="volume_location",
                            value=volume.location.value,
                        ),
                    )
                )
        limitations = _collector_limitations(audit)
        return ToolResult(
            operation=Operation.INSPECT_STORAGE,
            status=_result_status(limitations=limitations, unknowns=()),
            audit_id=_bounded(audit.audit_id, 256),
            collected_at=audit.collected_at,
            facts=tuple(facts),
            software=(_summary(selected),) if selected is not None else (),
            limitations=limitations,
            truncated=request.identity is None and len(audit.volumes) > 100,
        )

    def inspect_backups(self, request: InspectBackupsRequest) -> ToolResult:
        """Return configuration facts while keeping path coverage explicitly unknown."""
        audit = self._snapshot()
        selected: SoftwareRecord | None = None
        if request.identity is not None:
            resolved = _resolve_identity(audit.software, request.identity)
            if isinstance(resolved, ToolError):
                return ToolResult(
                    operation=Operation.INSPECT_BACKUPS,
                    status=ToolStatus.REFUSED,
                    audit_id=_bounded(audit.audit_id, 256),
                    collected_at=audit.collected_at,
                    errors=(resolved,),
                )
            selected = resolved
        facts: list[Fact] = []
        limitations = list(_collector_limitations(audit))
        if audit.backup is not None:
            if audit.backup.configured is not None:
                facts.append(
                    Fact(
                        topic="backup_configured",
                        value=str(audit.backup.configured).lower(),
                    )
                )
            if audit.backup.last_backup_at is not None:
                facts.append(
                    Fact(topic="last_backup_at", value=audit.backup.last_backup_at.isoformat())
                )
            limitations.extend(_bounded(item, 1024) for item in audit.backup.limitations)
        unknowns = (
            Unknown(
                subject_id=_bounded(selected.id, 256) if selected is not None else None,
                topic="backup_coverage",
                reason="Backup configuration and timestamps do not prove path-specific recoverability.",
            ),
        )
        return ToolResult(
            operation=Operation.INSPECT_BACKUPS,
            status=ToolStatus.PARTIAL,
            audit_id=_bounded(audit.audit_id, 256),
            collected_at=audit.collected_at,
            facts=tuple(facts),
            software=(_summary(selected),) if selected is not None else (),
            unknowns=unknowns,
            limitations=tuple(limitations[:100]),
        )

    def get_removal_preview(self, request: RemovalPreviewRequest) -> ToolResult:
        """Build one pure, nonpersistent preview without approval or execution state."""
        audit = self._snapshot()
        resolved = _resolve_identity(audit.software, request.identity)
        if isinstance(resolved, ToolError):
            return ToolResult(
                operation=Operation.GET_REMOVAL_PREVIEW,
                status=ToolStatus.REFUSED,
                audit_id=_bounded(audit.audit_id, 256),
                collected_at=audit.collected_at,
                errors=(resolved,),
            )
        preview = add_candidate(
            None,
            audit,
            resolved.id,
            clock=lambda: audit.collected_at,
            plan_id_factory=lambda: "plan:codex-read-only-preview",
            trash_root=Path.home() / ".Trash",
            include_startup=request.include_supported_startup,
        ).plan
        facts: list[Fact] = [
            Fact(
                subject_id=_bounded(resolved.id, 256),
                topic="eligibility",
                value=preview.eligibility.value,
            )
        ]
        facts.extend(
            Fact(
                subject_id=_bounded(check.subject_id, 256),
                topic=f"preflight_{check.kind.value}",
                value=_bounded(check.statement, 4096),
                basis=check.outcome.value,
            )
            for check in preview.checks
        )
        facts.extend(
            Fact(
                subject_id=_bounded(action.subject_id, 256),
                topic="preview_action_kind",
                value=action.kind.value,
                basis="preview_only",
            )
            for action in preview.actions
        )
        limitations = (
            *(_bounded(item, 1024) for item in preview.limitations),
            "Use the standalone MacWise terminal workflow for any plan or state change.",
        )
        return ToolResult(
            operation=Operation.GET_REMOVAL_PREVIEW,
            status=ToolStatus.PARTIAL,
            audit_id=_bounded(audit.audit_id, 256),
            collected_at=audit.collected_at,
            facts=tuple(facts[:500]),
            software=(_summary(resolved),),
            limitations=limitations[:100],
            truncated=len(facts) > 500 or len(limitations) > 100,
        )
