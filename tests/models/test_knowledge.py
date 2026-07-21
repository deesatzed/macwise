"""Strict contracts for privacy-bounded public app identification."""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from pydantic import ValidationError

from macwise.models.knowledge import (
    ClaimConfidence,
    LookupIdentity,
    LookupStatus,
    MatchMethod,
    PublicLookupResult,
    PublicPurposeClaim,
    PublicSourceType,
)

NOW = datetime.now(UTC)


def identity() -> LookupIdentity:
    return LookupIdentity(
        bundle_id="com.example.focus",
        name="Focus",
        publisher="Example, Inc.",
        version="2.4.1",
    )


def claim(**overrides: object) -> PublicPurposeClaim:
    values: dict[str, Any] = {
        "identity": identity(),
        "purpose": "A focused writing application.",
        "source_url": "https://example.com/focus",
        "source_type": PublicSourceType.PUBLISHER,
        "retrieved_at": NOW - timedelta(minutes=1),
        "expires_at": NOW + timedelta(days=30),
        "confidence": ClaimConfidence.HIGH,
        "match_method": MatchMethod.BUNDLE_ID_EXACT,
        "limitation": "Public information does not prove local use or safety.",
    }
    values.update(overrides)
    return PublicPurposeClaim(**values)


def test_lookup_identity_accepts_only_allowed_app_identifiers() -> None:
    item = identity()

    assert item.bundle_id == "com.example.focus"
    assert item.name == "Focus"
    assert item.publisher == "Example, Inc."
    assert item.version == "2.4.1"
    with pytest.raises(ValidationError):
        LookupIdentity(name="Focus", path="/Applications/Focus.app")  # type: ignore[reportCallIssue]


@pytest.mark.parametrize("field", ["bundle_id", "name", "publisher", "version"])
def test_lookup_identity_rejects_control_text(field: str) -> None:
    values = identity().model_dump()
    values[field] = "Focus\nInjected"

    with pytest.raises(ValidationError):
        LookupIdentity(**values)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("bundle_id", "com.example/focus"),
        ("bundle_id", "https://example.com/focus"),
        ("bundle_id", "focus@host.example"),
        ("bundle_id", "not a bundle id"),
        ("name", "/Applications/Focus.app"),
        ("name", "https://example.com/focus"),
        ("name", "owner@example.com"),
        ("publisher", "../private/publisher"),
        ("publisher", "https://example.com"),
        ("publisher", "owner@example.com"),
        ("version", "../../private/version"),
        ("version", "https://example.com/version"),
        ("version", "owner@example.com"),
    ],
)
def test_lookup_identity_rejects_path_url_and_account_like_values(field: str, value: str) -> None:
    values = identity().model_dump()
    values[field] = value

    with pytest.raises(ValidationError):
        LookupIdentity(**values)


def test_public_purpose_claim_is_immutable_and_bounded() -> None:
    item = claim()

    assert item.purpose == "A focused writing application."
    with pytest.raises(ValidationError):
        item.purpose = "Changed"
    with pytest.raises(ValidationError):
        claim(purpose="x" * 501)
    with pytest.raises(ValidationError):
        claim(purpose="Unsafe\ttext")


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_url", "http://example.com/focus"),
        ("source_url", "not-a-url"),
        ("source_type", "search-result"),
        ("retrieved_at", datetime.now(UTC) + timedelta(minutes=1)),
        ("expires_at", NOW - timedelta(minutes=2)),
        ("limitation", "x" * 501),
    ],
)
def test_public_purpose_claim_rejects_unsafe_or_invalid_metadata(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        claim(**{field: value})


def test_public_purpose_claim_rejects_expiry_at_creation() -> None:
    with pytest.raises(ValidationError):
        claim(expires_at=NOW - timedelta(minutes=1))


@pytest.mark.parametrize(
    "source_url",
    [
        "https://user:password@example.com/focus",
        "https://example.com/%0Ainjected",
        "https://example.com/%00injected",
        "https://127.0.0.1/focus",
        "https://10.0.0.1/focus",
        "https://169.254.169.254/focus",
        "https://192.0.2.1/focus",
        "https://[::1]/focus",
        "https://[fc00::1]/focus",
        "https://[fe80::1]/focus",
    ],
)
def test_public_purpose_claim_rejects_unsafe_https_targets(source_url: str) -> None:
    with pytest.raises(ValidationError):
        claim(source_url=source_url)


def test_public_purpose_claim_allows_a_public_https_source() -> None:
    assert str(claim(source_url="https://93.184.216.34/focus").source_url) == (
        "https://93.184.216.34/focus"
    )


@pytest.mark.parametrize(
    "source_url",
    [
        "https://localhost/focus",
        "https://service.local/focus",
        "https://service.internal/focus",
        "https://intranet/focus",
    ],
)
def test_public_purpose_claim_rejects_obvious_unsafe_hostname_urls(source_url: str) -> None:
    with pytest.raises(ValidationError):
        claim(source_url=source_url)


def test_expired_claim_can_be_deserialized_but_is_not_fresh() -> None:
    expired = claim(
        retrieved_at=NOW - timedelta(days=60),
        expires_at=NOW - timedelta(days=1),
    )

    assert not expired.is_fresh(NOW)
    assert expired.is_fresh(NOW - timedelta(days=2))


def test_resolved_lookup_result_rejects_an_expired_claim() -> None:
    expired = claim(
        retrieved_at=NOW - timedelta(days=60),
        expires_at=NOW - timedelta(days=1),
    )

    with pytest.raises(ValidationError):
        PublicLookupResult(
            identity=identity(),
            status=LookupStatus.RESOLVED,
            claim=expired,
            reason="matched",
        )


@pytest.mark.parametrize("source_url", ["https://example.com/focus", "https://apps.apple.com.evil/focus"])
def test_app_store_claim_requires_an_apple_app_store_host(source_url: str) -> None:
    with pytest.raises(ValidationError):
        claim(source_type=PublicSourceType.APP_STORE, source_url=source_url)


@pytest.mark.parametrize("source_url", ["https://apps.apple.com/us/app/focus/id123", "https://itunes.apple.com/focus"])
def test_app_store_claim_accepts_known_apple_app_store_hosts(source_url: str) -> None:
    assert claim(source_type=PublicSourceType.APP_STORE, source_url=source_url).source_type is (
        PublicSourceType.APP_STORE
    )


@pytest.mark.parametrize("forbidden_field", ["path", "usage", "startup", "plan", "inventory"])
def test_public_purpose_claim_cannot_carry_local_or_cleanup_data(forbidden_field: str) -> None:
    values = claim().model_dump()
    values[forbidden_field] = "local-only"

    with pytest.raises(ValidationError):
        PublicPurposeClaim(**values)


def test_public_lookup_result_makes_each_failure_state_explicit() -> None:
    resolved = PublicLookupResult(
        identity=identity(), status=LookupStatus.RESOLVED, claim=claim(), reason="matched"
    )
    assert resolved.claim == claim()

    for status in (LookupStatus.UNRESOLVED, LookupStatus.UNAVAILABLE, LookupStatus.CONFLICT):
        result = PublicLookupResult(identity=identity(), status=status, reason="not available")
        assert result.claim is None

    with pytest.raises(ValidationError):
        PublicLookupResult(identity=identity(), status=LookupStatus.RESOLVED, reason="missing")
    with pytest.raises(ValidationError):
        PublicLookupResult(
            identity=identity(), status=LookupStatus.UNAVAILABLE, claim=claim(), reason="wrong"
        )


@pytest.mark.parametrize(
    "reason",
    [
        "<html><body>source error</body></html>",
        '{"error":"source failure"}',
        "[\"raw\", \"source\", \"response\"]",
    ],
)
def test_public_lookup_result_rejects_raw_source_payloads_in_reason(reason: str) -> None:
    with pytest.raises(ValidationError):
        PublicLookupResult(
            identity=identity(),
            status=LookupStatus.UNAVAILABLE,
            reason=reason,
        )
