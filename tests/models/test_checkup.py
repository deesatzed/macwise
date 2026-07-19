from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from macwise.models import CheckupPriority, CheckupSummary


def test_checkup_summary_is_immutable_and_read_only() -> None:
    priority = CheckupPriority(
        key="knowledge_gaps",
        title="Unknown software deserves identification",
        observed_count=3,
        reason="MacWise found 3 installed items whose purpose is unknown.",
        evidence="Verified local inventory plus the bundled catalog.",
        benefit="Identifying them makes later keep-or-remove decisions better informed.",
        limitation="Unknown does not mean unused or unsafe.",
        next_command="macwise review unknown",
    )
    summary = CheckupSummary(
        collected_at=datetime(2026, 7, 19, tzinfo=UTC),
        priorities=(priority,),
        report_confidence=72,
        largest_missing_evidence="Application purpose coverage is incomplete.",
    )

    assert summary.changed_mac is False
    with pytest.raises(ValidationError):
        summary.changed_mac = True


def test_checkup_priority_rejects_unsupported_next_command() -> None:
    with pytest.raises(ValidationError, match="supported focused command"):
        CheckupPriority(
            key="unsafe",
            title="Unsafe",
            observed_count=1,
            reason="Unsafe",
            evidence="Unsafe",
            benefit="Unsafe",
            limitation="Unsafe",
            next_command="rm -rf /",
        )
