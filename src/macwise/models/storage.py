"""Normalized storage volume records."""

from enum import StrEnum
from hashlib import sha256

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
    device_identifier: str = Field(min_length=1)
    mount_point: str | None = None
    location: StorageLocation = StorageLocation.UNKNOWN
    filesystem: str | None = None
    capacity_bytes: int | None = Field(default=None, ge=0)
    free_bytes: int | None = Field(default=None, ge=0)
    read_only: bool | None = None
    encrypted: bool | None = None
    removable: bool | None = None
    protocol: str | None = None
    smart_status: str | None = None
    evidence: tuple[Evidence, ...] = ()


def stable_volume_id(device_identifier: str) -> str:
    """Return a deterministic volume ID without embedding a device name."""
    digest = sha256(device_identifier.strip().casefold().encode()).hexdigest()[:20]
    return f"volume:{digest}"
