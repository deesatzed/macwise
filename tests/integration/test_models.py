from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from macwise.integration.models import (
    AuditMacRequest,
    Fact,
    FindOverlapsRequest,
    InspectBackupsRequest,
    InspectSoftwareRequest,
    ListSoftwareRequest,
    Operation,
    SoftwareSummary,
    ToolError,
    ToolResult,
    ToolStatus,
    Unknown,
)
from macwise.models import EntityType


def test_requests_are_versioned_strict_and_bounded() -> None:
    request = InspectSoftwareRequest(identity="cask:visual-studio-code")

    assert request.schema_version == 1
    with pytest.raises(ValidationError):
        InspectSoftwareRequest.model_validate({"identity": "x", "command": "rm"})
    with pytest.raises(ValidationError):
        InspectSoftwareRequest(identity="")
    with pytest.raises(ValidationError):
        InspectSoftwareRequest(identity="x" * 257)
    with pytest.raises(ValidationError):
        InspectSoftwareRequest(identity="\x1b\u202e")


def test_collection_requests_reject_unbounded_or_control_shaped_values() -> None:
    request = ListSoftwareRequest(entity_type=EntityType.APPLICATION, page_size=25, cursor=0)

    assert request.page_size == 25
    with pytest.raises(ValidationError):
        ListSoftwareRequest(page_size=101)
    with pytest.raises(ValidationError):
        ListSoftwareRequest(cursor=-1)
    with pytest.raises(ValidationError):
        FindOverlapsRequest(identities=tuple(f"app:item-{index}" for index in range(21)))
    with pytest.raises(ValidationError):
        InspectBackupsRequest(identity="../private")


def test_audit_refresh_is_explicit_and_false_by_default() -> None:
    assert AuditMacRequest().refresh is False
    assert AuditMacRequest(refresh=True).refresh is True


def test_tool_result_keeps_evidence_unknowns_and_limitations_separate() -> None:
    collected_at = datetime(2026, 7, 18, tzinfo=UTC)
    result = ToolResult(
        operation=Operation.INSPECT_SOFTWARE,
        status=ToolStatus.PARTIAL,
        audit_id="audit:test",
        collected_at=collected_at,
        facts=(Fact(topic="identity", value="Example"),),
        software=(
            SoftwareSummary(
                id="app:com.example.App",
                entity_type=EntityType.APPLICATION,
                display_name="Example",
            ),
        ),
        unknowns=(Unknown(topic="usage", reason="No reliable use evidence was found."),),
        limitations=("The usage collector was unavailable.",),
    )

    assert result.schema_version == 1
    assert result.facts[0].value == "Example"
    assert result.unknowns[0].topic == "usage"
    assert result.limitations == ("The usage collector was unavailable.",)
    assert result.errors == ()


def test_tool_errors_are_bounded_and_extra_fields_are_rejected() -> None:
    error = ToolError(
        code="ambiguous_identity",
        message="More than one exact software record matched.",
        recovery=("Use a qualified identity.",),
    )

    assert error.code == "ambiguous_identity"
    with pytest.raises(ValidationError):
        ToolError.model_validate({"code": "x", "message": "m", "shell": "rm"})
    with pytest.raises(ValidationError):
        Fact(topic="x", value="y" * 4097)


def test_all_eight_operations_are_closed_enum_values() -> None:
    assert {operation.value for operation in Operation} == {
        "audit_mac",
        "list_software",
        "inspect_software",
        "find_overlaps",
        "inspect_startup",
        "inspect_storage",
        "inspect_backups",
        "get_removal_preview",
    }


def test_tool_result_rejects_an_oversized_serialized_payload() -> None:
    facts = tuple(Fact(topic=f"topic-{index}", value="x" * 4096) for index in range(200))

    with pytest.raises(ValidationError):
        ToolResult(
            operation=Operation.AUDIT_MAC,
            status=ToolStatus.OK,
            facts=facts,
        )
