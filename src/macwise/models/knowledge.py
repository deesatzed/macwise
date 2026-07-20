"""Strict, non-authoritative public application-identification contracts."""

import re
from datetime import UTC, datetime
from enum import StrEnum
from ipaddress import ip_address

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


class ClaimConfidence(StrEnum):
    """Confidence supported by a cited public source."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MatchMethod(StrEnum):
    """How a public source matched an application identity."""

    BUNDLE_ID_EXACT = "bundle_id_exact"
    PUBLISHER_PRODUCT_EXACT = "publisher_product_exact"
    NAME_TENTATIVE = "name_tentative"


class PublicSourceType(StrEnum):
    """Allowlisted kinds of cited public sources."""

    APP_STORE = "app_store"
    PUBLISHER = "publisher"


class LookupStatus(StrEnum):
    """A public-lookup outcome, including nonfatal failure states."""

    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    UNAVAILABLE = "unavailable"
    CONFLICT = "conflict"


def _reject_control_text(value: str | None) -> str | None:
    if value is not None and any(
        ord(character) < 32 or ord(character) == 127 for character in value
    ):
        raise ValueError("must not contain control text")
    return value


_PERCENT_ENCODED_CONTROL = re.compile(r"%(?:0[0-9a-f]|1[0-9a-f]|7f)", re.IGNORECASE)


class LookupIdentity(BaseModel):
    """The only application fields that a public provider may receive."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    bundle_id: str | None = Field(default=None, min_length=1, max_length=255)
    name: str = Field(min_length=1, max_length=160)
    publisher: str | None = Field(default=None, min_length=1, max_length=160)
    version: str | None = Field(default=None, min_length=1, max_length=64)

    @field_validator("bundle_id", "name", "publisher", "version")
    @classmethod
    def reject_control_text(cls, value: str | None) -> str | None:
        return _reject_control_text(value)


class PublicPurposeClaim(BaseModel):
    """A cited public description that cannot carry local decision evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    identity: LookupIdentity
    purpose: str = Field(min_length=1, max_length=500)
    source_url: HttpUrl
    source_type: PublicSourceType
    retrieved_at: AwareDatetime
    expires_at: AwareDatetime
    confidence: ClaimConfidence
    match_method: MatchMethod
    limitation: str = Field(min_length=1, max_length=500)

    @field_validator("purpose", "limitation")
    @classmethod
    def reject_control_text(cls, value: str) -> str:
        return _reject_control_text(value) or ""

    @field_validator("source_url", mode="before")
    @classmethod
    def reject_encoded_control_text(cls, value: object) -> object:
        if _PERCENT_ENCODED_CONTROL.search(str(value)):
            raise ValueError("source_url must not contain percent-encoded control text")
        return value

    @field_validator("source_url")
    @classmethod
    def require_https(cls, value: HttpUrl) -> HttpUrl:
        if value.scheme != "https":
            raise ValueError("source_url must use HTTPS")
        if value.username is not None or value.password is not None:
            raise ValueError("source_url must not contain userinfo")
        host = value.host
        if host is None:
            raise ValueError("source_url must contain a host")
        try:
            target = ip_address(host.strip("[]"))
        except ValueError:
            normalized_host = host.casefold().rstrip(".")
            if (
                normalized_host == "localhost"
                or normalized_host.endswith(".local")
                or normalized_host.endswith(".internal")
                or "." not in normalized_host
            ):
                raise ValueError("source_url must use a public hostname") from None
            # Publisher-domain authenticity needs provider identity proof, not URL shape alone.
            # DNS resolution and rebinding defenses belong to the Task 5 provider/network layer.
            return value
        if not target.is_global:
            raise ValueError("source_url literal IP target must be globally routable")
        return value

    @model_validator(mode="after")
    def require_valid_lifetime(self) -> "PublicPurposeClaim":
        if self.expires_at <= self.retrieved_at:
            raise ValueError("expires_at must be after retrieved_at")
        current_time = datetime.now(UTC)
        if self.retrieved_at > current_time:
            raise ValueError("retrieved_at cannot be in the future")
        if self.source_type is PublicSourceType.APP_STORE:
            app_store_host = (self.source_url.host or "").casefold().rstrip(".")
            if app_store_host not in {"apps.apple.com", "itunes.apple.com"}:
                raise ValueError("app_store claims must use a known Apple App Store host")
        return self

    def is_fresh(self, now: datetime) -> bool:
        """Whether this historical claim can be used at the supplied instant."""

        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now must be timezone-aware")
        return self.expires_at > now


class PublicLookupResult(BaseModel):
    """A typed public lookup result; failures are never silently omitted."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    identity: LookupIdentity
    status: LookupStatus
    claim: PublicPurposeClaim | None = None
    reason: str = Field(min_length=1, max_length=500)

    @field_validator("reason")
    @classmethod
    def reject_control_text(cls, value: str) -> str:
        return _reject_control_text(value) or ""

    @model_validator(mode="after")
    def keep_claim_consistent_with_status(self) -> "PublicLookupResult":
        if self.status is LookupStatus.RESOLVED and self.claim is None:
            raise ValueError("resolved results require a claim")
        if self.status is not LookupStatus.RESOLVED and self.claim is not None:
            raise ValueError("only resolved results can carry a claim")
        if self.claim is not None and self.claim.identity != self.identity:
            raise ValueError("claim identity must match lookup identity")
        if (
            self.status is LookupStatus.RESOLVED
            and self.claim is not None
            and not self.claim.is_fresh(datetime.now(UTC))
        ):
            raise ValueError("resolved results cannot carry expired claims")
        return self
