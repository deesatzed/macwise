"""Normalized installed-software records."""

from enum import StrEnum
from hashlib import sha256

from pydantic import BaseModel, ConfigDict, Field

from macwise.models.evidence import Evidence
from macwise.models.storage import StorageLocation


class EntityType(StrEnum):
    """Kinds of software collected during the public read-only phase."""

    APPLICATION = "application"
    HOMEBREW_FORMULA = "homebrew_formula"
    HOMEBREW_CASK = "homebrew_cask"


def stable_software_id(entity_type: EntityType, canonical_key: str) -> str:
    """Return a deterministic, type-scoped ID without embedding private values."""
    normalized_key = canonical_key.strip().casefold()
    digest = sha256(f"{entity_type.value}\0{normalized_key}".encode()).hexdigest()[:20]
    return f"{entity_type.value}:{digest}"


class SoftwareRecord(BaseModel):
    """A normalized application or package discovered on the host."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    entity_type: EntityType
    name: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    identifier: str | None = None
    version: str | None = None
    install_path: str | None = None
    install_source: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)
    storage_location: StorageLocation = StorageLocation.UNKNOWN
    protected: bool = False
    evidence: tuple[Evidence, ...] = ()
