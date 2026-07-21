"""Privacy-bounded contracts for public-purpose lookup providers."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import HttpUrl, ValidationError

from macwise.knowledge.providers import RecordingPublicPurposeProvider
from macwise.models.knowledge import (
    ClaimConfidence,
    LookupIdentity,
    LookupStatus,
    MatchMethod,
    PublicLookupResult,
    PublicPurposeClaim,
    PublicSourceType,
)


def identity() -> LookupIdentity:
    return LookupIdentity(
        bundle_id="com.example.focus",
        name="Focus",
        publisher="Example, Inc.",
        version="2.4.1",
    )


def resolved_result(
    *, match_method: MatchMethod = MatchMethod.BUNDLE_ID_EXACT
) -> PublicLookupResult:
    item = identity()
    now = datetime.now(UTC)
    return PublicLookupResult(
        identity=item,
        status=LookupStatus.RESOLVED,
        claim=PublicPurposeClaim(
            identity=item,
            purpose="A focused writing application.",
            source_url=HttpUrl("https://example.com/focus"),
            source_type=PublicSourceType.PUBLISHER,
            retrieved_at=now - timedelta(minutes=1),
            expires_at=now + timedelta(days=30),
            confidence=ClaimConfidence.HIGH,
            match_method=match_method,
            limitation="Public information does not prove local use or safety.",
        ),
        reason="Matched a cited public source.",
    )


def outcome(status: LookupStatus, reason: str) -> PublicLookupResult:
    return PublicLookupResult(identity=identity(), status=status, reason=reason)


def test_recording_provider_receives_exactly_one_lookup_identity_per_call() -> None:
    item = identity()
    expected = resolved_result()
    provider = RecordingPublicPurposeProvider([expected])

    actual = provider.lookup(item)

    assert actual == expected
    assert provider.calls == [item]


@pytest.mark.parametrize(
    "forbidden_field",
    ["checkup", "audit", "path", "usage", "startup", "dependency", "backup", "plan"],
)
def test_lookup_identity_structurally_rejects_private_audit_fields(forbidden_field: str) -> None:
    with pytest.raises(ValidationError):
        LookupIdentity(name="Focus", **{forbidden_field: "private local evidence"})


@pytest.mark.parametrize(
    "private_payload",
    [
        {"audit": "entire machine inventory"},
        {"path": "/Applications/Focus.app"},
        {"usage": "recently used"},
        {"startup": "enabled"},
        {"dependency": "depends-on-other-app"},
        {"backup": "time-machine-status"},
        {"plan": "remove this app"},
    ],
)
def test_recording_provider_rejects_non_identity_payloads(
    private_payload: dict[str, str],
) -> None:
    provider = RecordingPublicPurposeProvider([])

    with pytest.raises(TypeError, match="LookupIdentity"):
        provider.lookup(private_payload)  # type: ignore[arg-type]

    assert provider.calls == []


def test_recording_provider_does_not_record_a_validation_bypassing_identity() -> None:
    unsafe_identity = LookupIdentity.model_construct(
        bundle_id="https://private.example/inventory",
        name="Focus",
        publisher="Example, Inc.",
        version="2.4.1",
    )
    provider = RecordingPublicPurposeProvider([])

    with pytest.raises(ValidationError):
        provider.lookup(unsafe_identity)

    assert provider.calls == []


@pytest.mark.parametrize(
    ("status", "reason"),
    [
        (LookupStatus.UNAVAILABLE, "Public source timed out."),
        (LookupStatus.UNRESOLVED, "Public source response was malformed."),
        (LookupStatus.CONFLICT, "Public sources matched different products."),
        (LookupStatus.UNAVAILABLE, "Public provider failed without a result."),
    ],
)
def test_provider_returns_typed_nonfatal_outcomes_for_source_problems(
    status: LookupStatus, reason: str
) -> None:
    item = identity()
    expected = outcome(status, reason)
    provider = RecordingPublicPurposeProvider([expected])

    actual = provider.lookup(item)

    assert isinstance(actual, PublicLookupResult)
    assert actual.status is status
    assert actual.claim is None
    assert actual.reason == reason
    assert "<html" not in actual.reason.casefold()


def test_provider_does_not_promote_tentative_name_match_to_exact() -> None:
    item = identity()
    expected = resolved_result(match_method=MatchMethod.NAME_TENTATIVE)
    provider = RecordingPublicPurposeProvider([expected])

    actual = provider.lookup(item)

    assert actual.claim is not None
    assert actual.claim.match_method is MatchMethod.NAME_TENTATIVE
