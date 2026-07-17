"""Versioned MacWise audit documents and collector health."""

from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from macwise.models.software import SoftwareRecord
from macwise.models.storage import VolumeRecord


class CollectorState(StrEnum):
    """Whether a collector returned all, some, or none of its intended data."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


class CollectorStatus(BaseModel):
    """Collection outcome kept alongside the records it qualifies."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    collector: str = Field(min_length=1)
    state: CollectorState
    collected_at: AwareDatetime
    records_count: int = Field(ge=0)
    limitations: tuple[str, ...] = ()


class AuditDocument(BaseModel):
    """The stable, local interchange format for a MacWise read-only audit."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[2] = 2
    audit_id: str = Field(min_length=1)
    collected_at: AwareDatetime
    software: tuple[SoftwareRecord, ...] = ()
    volumes: tuple[VolumeRecord, ...] = ()
    collectors: tuple[CollectorStatus, ...] = ()
