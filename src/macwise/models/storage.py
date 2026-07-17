"""Normalized storage volume records."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from macwise.models.evidence import Evidence


class StorageLocation(StrEnum):
    """Whether a volume is internal, external, or not reliably classified."""

    INTERNAL = "internal"
    EXTERNAL = "external"
    UNKNOWN = "unknown"


class VolumeRecord(BaseModel):
    """A mounted or discovered storage volume."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    mount_point: str | None = None
    location: StorageLocation = StorageLocation.UNKNOWN
    filesystem: str | None = None
    capacity_bytes: int | None = Field(default=None, ge=0)
    free_bytes: int | None = Field(default=None, ge=0)
    read_only: bool | None = None
    encrypted: bool | None = None
    evidence: tuple[Evidence, ...] = ()
