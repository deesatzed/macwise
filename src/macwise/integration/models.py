"""Versioned, bounded contracts for MacWise read-only local tools."""

import unicodedata
from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

from macwise.models import EntityType


class StrictModel(BaseModel):
    """Immutable model that rejects unknown protocol fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class Operation(StrEnum):
    """The closed MacWise read-only tool surface."""

    AUDIT_MAC = "audit_mac"
    LIST_SOFTWARE = "list_software"
    INSPECT_SOFTWARE = "inspect_software"
    FIND_OVERLAPS = "find_overlaps"
    INSPECT_STARTUP = "inspect_startup"
    INSPECT_STORAGE = "inspect_storage"
    INSPECT_BACKUPS = "inspect_backups"
    GET_REMOVAL_PREVIEW = "get_removal_preview"


class ToolStatus(StrEnum):
    """Bounded outcome classification for a local tool call."""

    OK = "ok"
    PARTIAL = "partial"
    REFUSED = "refused"
    ERROR = "error"


def _validate_evidence_identity(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("Identity must contain visible text.")
    if stripped.startswith(("../", "..\\")):
        raise ValueError("Identity cannot be a traversal-shaped path.")
    if all(unicodedata.category(character) in {"Cc", "Cf", "Zs"} for character in stripped):
        raise ValueError("Identity must contain visible text.")
    if any(unicodedata.category(character) in {"Cc", "Cf"} for character in stripped):
        raise ValueError("Identity cannot contain control or format characters.")
    return stripped


class AuditMacRequest(StrictModel):
    """Request a bounded summary of the current or refreshed in-memory audit."""

    schema_version: Literal[1] = 1
    refresh: bool = False


class ListSoftwareRequest(StrictModel):
    """List a bounded page of normalized software records."""

    schema_version: Literal[1] = 1
    entity_type: EntityType | None = None
    query: str | None = Field(default=None, min_length=1, max_length=128)
    page_size: int = Field(default=50, ge=1, le=100)
    cursor: int = Field(default=0, ge=0)

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str | None) -> str | None:
        return None if value is None else _validate_evidence_identity(value)


class IdentityRequest(StrictModel):
    """Base request for one exact or user-visible software identity."""

    schema_version: Literal[1] = 1
    identity: str = Field(min_length=1, max_length=256)

    @field_validator("identity")
    @classmethod
    def validate_identity(cls, value: str) -> str:
        return _validate_evidence_identity(value)


class InspectSoftwareRequest(IdentityRequest):
    """Inspect one exact software identity."""


class FindOverlapsRequest(StrictModel):
    """Find catalog-backed overlap among zero or more requested identities."""

    schema_version: Literal[1] = 1
    identities: tuple[str, ...] = Field(default=(), max_length=20)

    @field_validator("identities")
    @classmethod
    def validate_identities(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_validate_evidence_identity(value) for value in values)


class InspectStartupRequest(StrictModel):
    """Inspect startup evidence, optionally narrowed to one software identity."""

    schema_version: Literal[1] = 1
    identity: str | None = Field(default=None, min_length=1, max_length=256)

    @field_validator("identity")
    @classmethod
    def validate_identity(cls, value: str | None) -> str | None:
        return None if value is None else _validate_evidence_identity(value)


class InspectStorageRequest(InspectStartupRequest):
    """Inspect storage evidence, optionally narrowed to one software identity."""


class InspectBackupsRequest(InspectStartupRequest):
    """Inspect backup evidence, optionally narrowed to one software identity."""


class RemovalPreviewRequest(IdentityRequest):
    """Build a nonpersistent removal preview for one exact identity."""

    include_supported_startup: bool = False


class Fact(StrictModel):
    """One bounded observed or derived fact."""

    subject_id: str | None = Field(default=None, min_length=1, max_length=256)
    topic: str = Field(min_length=1, max_length=128)
    value: str = Field(max_length=4096)
    basis: str = Field(default="observed", min_length=1, max_length=128)
    source: str | None = Field(default=None, min_length=1, max_length=512)


class Unknown(StrictModel):
    """One explicit evidence gap."""

    subject_id: str | None = Field(default=None, min_length=1, max_length=256)
    topic: str = Field(min_length=1, max_length=128)
    reason: str = Field(min_length=1, max_length=1024)


class ToolError(StrictModel):
    """Bounded public refusal or failure without a traceback."""

    code: str = Field(min_length=1, max_length=128, pattern=r"^[a-z][a-z0-9_]*$")
    message: str = Field(min_length=1, max_length=1024)
    recovery: tuple[str, ...] = Field(default=(), max_length=8)


class SoftwareSummary(StrictModel):
    """Bounded normalized software identity returned to Codex."""

    id: str = Field(min_length=1, max_length=256)
    entity_type: EntityType
    display_name: str = Field(min_length=1, max_length=512)
    version: str | None = Field(default=None, max_length=256)
    identifier: str | None = Field(default=None, max_length=512)
    install_role: str | None = Field(default=None, max_length=64)
    storage_location: str | None = Field(default=None, max_length=64)


class ToolResult(StrictModel):
    """Stable response envelope shared by every read-only operation."""

    schema_version: Literal[1] = 1
    operation: Operation
    status: ToolStatus
    audit_id: str | None = Field(default=None, min_length=1, max_length=256)
    collected_at: AwareDatetime | None = None
    facts: tuple[Fact, ...] = Field(default=(), max_length=500)
    software: tuple[SoftwareSummary, ...] = Field(default=(), max_length=100)
    unknowns: tuple[Unknown, ...] = Field(default=(), max_length=100)
    limitations: tuple[str, ...] = Field(default=(), max_length=100)
    errors: tuple[ToolError, ...] = Field(default=(), max_length=16)
    next_cursor: int | None = Field(default=None, ge=0)
    truncated: bool = False
