from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from macwise.models import Evidence, Reliability


def test_evidence_requires_timezone_aware_collection_time() -> None:
    with pytest.raises(ValidationError):
        Evidence(
            kind="bundle_metadata",
            value={"bundle_id": "org.example.SafeApp"},
            source="Info.plist",
            collected_at=datetime(2026, 7, 17, 12, 0),
            reliability=Reliability.HIGH,
        )


def test_missing_source_is_unknown_with_a_plain_language_limitation() -> None:
    evidence = Evidence(
        kind="spotlight_last_used",
        value=None,
        source="mdls",
        collected_at=datetime(2026, 7, 17, 12, 0, tzinfo=UTC),
        reliability=Reliability.UNKNOWN,
        limitations=("No reliable last-use metadata was available.",),
    )

    serialized = evidence.model_dump_json()

    assert evidence.reliability is Reliability.UNKNOWN
    assert evidence.value is None
    assert "No reliable last-use metadata was available." in serialized
    assert "never used" not in serialized.lower()


def test_evidence_is_immutable_and_rejects_unknown_fields() -> None:
    evidence = Evidence(
        kind="bundle_version",
        value="1.2.3",
        source="Info.plist",
        collected_at=datetime(2026, 7, 17, 12, 0, tzinfo=UTC),
        reliability=Reliability.HIGH,
    )

    with pytest.raises(ValidationError):
        evidence.value = "changed"  # type: ignore[misc]

    with pytest.raises(ValidationError):
        Evidence.model_validate({**evidence.model_dump(), "unexpected": True})
