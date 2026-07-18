from dataclasses import dataclass

from macwise.integration.models import (
    AuditMacRequest,
    InspectSoftwareRequest,
    ListSoftwareRequest,
    Operation,
    ToolStatus,
)
from macwise.integration.service import CodexReadService
from macwise.models import (
    AuditDocument,
    CollectorState,
    EntityType,
    SoftwareRecord,
    stable_software_id,
)


@dataclass
class CountingAuditProvider:
    audit: AuditDocument
    calls: int = 0

    def __call__(self) -> AuditDocument:
        self.calls += 1
        return self.audit.model_copy(update={"audit_id": f"audit:call-{self.calls}"})


def test_audit_snapshot_is_cached_until_explicit_refresh(sample_audit: AuditDocument) -> None:
    provider = CountingAuditProvider(sample_audit)
    service = CodexReadService(audit_provider=provider)

    first = service.audit_mac(AuditMacRequest())
    listed = service.list_software(ListSoftwareRequest())
    refreshed = service.audit_mac(AuditMacRequest(refresh=True))

    assert provider.calls == 2
    assert first.audit_id == "audit:call-1"
    assert listed.audit_id == "audit:call-1"
    assert refreshed.audit_id == "audit:call-2"


def test_audit_summary_reports_collector_limits_without_negative_claims(
    sample_audit: AuditDocument,
) -> None:
    usage_limited = sample_audit.collectors[0].model_copy(
        update={
            "collector": "usage",
            "state": CollectorState.UNAVAILABLE,
            "records_count": 0,
            "limitations": ("Spotlight metadata was unavailable.",),
        }
    )
    audit = sample_audit.model_copy(update={"collectors": (*sample_audit.collectors, usage_limited)})

    result = CodexReadService(audit_provider=lambda: audit).audit_mac(AuditMacRequest())

    assert result.operation is Operation.AUDIT_MAC
    assert result.status is ToolStatus.PARTIAL
    assert "Spotlight metadata was unavailable." in result.limitations
    assert any(unknown.topic == "usage" for unknown in result.unknowns)
    assert "never used" not in result.model_dump_json().casefold()


def test_list_software_is_stable_filterable_and_paginated(sample_audit: AuditDocument) -> None:
    service = CodexReadService(audit_provider=lambda: sample_audit)

    first = service.list_software(ListSoftwareRequest(page_size=1))
    second = service.list_software(ListSoftwareRequest(page_size=1, cursor=first.next_cursor or 0))
    applications = service.list_software(
        ListSoftwareRequest(entity_type=EntityType.APPLICATION, query="example")
    )

    assert len(first.software) == 1
    assert first.next_cursor == 1
    assert first.truncated is True
    assert len(second.software) == 1
    assert second.next_cursor is None
    assert [item.display_name for item in applications.software] == ["Example App"]


def test_inspect_software_returns_identity_facts_and_usage_unknown(
    sample_audit: AuditDocument,
) -> None:
    application = next(
        record for record in sample_audit.software if record.entity_type is EntityType.APPLICATION
    )

    result = CodexReadService(audit_provider=lambda: sample_audit).inspect_software(
        InspectSoftwareRequest(identity=application.id)
    )

    assert result.status is ToolStatus.PARTIAL
    assert result.software[0].id == application.id
    assert any(fact.topic == "version" and fact.value == "2.4.1" for fact in result.facts)
    assert any(unknown.topic == "usage" for unknown in result.unknowns)


def test_inspect_supports_qualified_exact_names(sample_audit: AuditDocument) -> None:
    result = CodexReadService(audit_provider=lambda: sample_audit).inspect_software(
        InspectSoftwareRequest(identity="formula:openssl@3")
    )

    assert result.status is ToolStatus.PARTIAL
    assert result.software[0].entity_type is EntityType.HOMEBREW_FORMULA


def test_inspect_refuses_ambiguous_unqualified_identity(sample_audit: AuditDocument) -> None:
    duplicate = SoftwareRecord(
        id=stable_software_id(EntityType.HOMEBREW_CASK, "example"),
        entity_type=EntityType.HOMEBREW_CASK,
        name="example",
        display_name="Example App",
    )
    audit = sample_audit.model_copy(update={"software": (*sample_audit.software, duplicate)})

    result = CodexReadService(audit_provider=lambda: audit).inspect_software(
        InspectSoftwareRequest(identity="Example App")
    )

    assert result.status is ToolStatus.REFUSED
    assert result.errors[0].code == "ambiguous_identity"
    assert "qualified" in result.errors[0].recovery[0].casefold()


def test_inspect_refuses_unknown_identity(sample_audit: AuditDocument) -> None:
    result = CodexReadService(audit_provider=lambda: sample_audit).inspect_software(
        InspectSoftwareRequest(identity="Missing App")
    )

    assert result.status is ToolStatus.REFUSED
    assert result.errors[0].code == "unknown_identity"
