"""Normalized Phase 2 findings, startup items, and related path evidence."""

from enum import StrEnum
from hashlib import sha256

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from macwise.models.evidence import Evidence, Reliability
from macwise.models.storage import StorageLocation


class ClaimBasis(StrEnum):
    """Whether a conclusion is observed, inferred, confirmed, or unknown."""

    VERIFIED = "verified"
    INFERRED = "inferred"
    USER_CONFIRMED = "user_confirmed"
    UNKNOWN = "unknown"


class UsageLabel(StrEnum):
    """User-facing usage labels permitted by the product contract."""

    ACTIVELY_USED = "actively_used"
    RECENTLY_USED = "recently_used"
    PROBABLY_USED = "probably_used"
    INDIRECTLY_REQUIRED = "indirectly_required"
    CONFIGURED_BUT_IDLE = "configured_but_idle"
    POSSIBLY_UNUSED = "possibly_unused"
    NO_RELIABLE_EVIDENCE = "no_reliable_evidence"
    USER_CONFIRMED_UNUSED = "user_confirmed_unused"


class FindingTopic(StrEnum):
    """Analysis topics rendered separately from raw inventory facts."""

    USAGE = "usage"
    STARTUP = "startup"
    RELATED_DATA = "related_data"
    BACKUP = "backup"


class StartupKind(StrEnum):
    """Kinds of automatic or background startup components."""

    LOGIN_ITEM = "login_item"
    BACKGROUND_ITEM = "background_item"
    LAUNCH_AGENT = "launch_agent"
    LAUNCH_DAEMON = "launch_daemon"
    HOMEBREW_SERVICE = "homebrew_service"
    PRIVILEGED_HELPER = "privileged_helper"
    SYSTEM_EXTENSION = "system_extension"
    FINDER_EXTENSION = "finder_extension"
    QUICK_LOOK_EXTENSION = "quick_look_extension"


class Finding(BaseModel):
    """One evidence-linked conclusion whose basis is explicit."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    subject_id: str = Field(min_length=1)
    topic: FindingTopic
    statement: str = Field(min_length=1)
    basis: ClaimBasis
    confidence: Reliability
    usage_label: UsageLabel | None = None
    evidence_kinds: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    @model_validator(mode="after")
    def require_usage_label_for_usage_topic(self) -> "Finding":
        """Keep usage conclusions typed instead of hiding labels in prose."""
        if self.topic is FindingTopic.USAGE and self.usage_label is None:
            raise ValueError("usage_label is required for a usage finding")
        if self.topic is not FindingTopic.USAGE and self.usage_label is not None:
            raise ValueError("usage_label is only valid for a usage finding")
        return self


class StartupRecord(BaseModel):
    """One startup/background component and any conservatively matched owner."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    kind: StartupKind
    source_path: str | None = None
    program: str | None = None
    bundle_identifier: str | None = None
    owner_software_ids: tuple[str, ...] = ()
    enabled: bool | None = None
    running: bool | None = None
    evidence: tuple[Evidence, ...] = ()


class PathEvidence(BaseModel):
    """A bounded related-data path measurement tied to one software record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    path: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    size_bytes: int | None = Field(default=None, ge=0)
    storage_location: StorageLocation = StorageLocation.UNKNOWN
    last_modified_at: AwareDatetime | None = None
    backup_excluded: bool | None = None
    evidence: tuple[Evidence, ...] = ()


def _stable_scoped_id(scope: str, *values: str) -> str:
    normalized = "\0".join(value.strip().casefold() for value in values)
    digest = sha256(f"{scope}\0{normalized}".encode()).hexdigest()[:20]
    return f"{scope}:{digest}"


def stable_startup_id(kind: StartupKind, canonical_key: str) -> str:
    """Return a deterministic startup ID without embedding the raw label."""
    return _stable_scoped_id("startup", kind.value, canonical_key)


def stable_path_evidence_id(subject_id: str, path: str) -> str:
    """Return a deterministic path-evidence ID without embedding the path."""
    return _stable_scoped_id("path", subject_id, path)
