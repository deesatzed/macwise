from datetime import UTC, datetime

from macwise.models import AuditDocument
from macwise.services import build_checkup


def test_checkup_is_deterministic_bounded_and_never_treats_unknown_as_removable(
    sample_audit: AuditDocument,
) -> None:
    now = datetime(2026, 7, 19, tzinfo=UTC)

    first = build_checkup(sample_audit, now=now)
    second = build_checkup(sample_audit, now=now)

    assert first == second
    assert 1 <= len(first.priorities) <= 5
    unknown = next(item for item in first.priorities if item.key == "knowledge_gaps")
    assert unknown.next_command == "macwise review unknown"
    assert "does not mean unused or safe to remove" in unknown.limitation
    assert "remove" not in unknown.benefit.casefold()
    assert first.collected_at == sample_audit.collected_at
    assert first.changed_mac is False


def test_checkup_explains_the_largest_report_coverage_gap(sample_audit: AuditDocument) -> None:
    summary = build_checkup(sample_audit, now=datetime(2026, 7, 19, tzinfo=UTC))

    assert 0 <= summary.report_confidence <= 100
    assert summary.largest_missing_evidence
    assert "not a health grade" in summary.confidence_limitation
