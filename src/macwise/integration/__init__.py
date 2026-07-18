"""Strict read-only integration contracts for optional Codex support."""

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
from macwise.integration.service import CodexReadService

__all__ = [
    "AuditMacRequest",
    "CodexReadService",
    "Fact",
    "FindOverlapsRequest",
    "InspectBackupsRequest",
    "InspectSoftwareRequest",
    "InspectStartupRequest",
    "InspectStorageRequest",
    "ListSoftwareRequest",
    "Operation",
    "RemovalPreviewRequest",
    "SoftwareSummary",
    "ToolError",
    "ToolResult",
    "ToolStatus",
    "Unknown",
]
