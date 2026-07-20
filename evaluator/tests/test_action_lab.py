"""Independent checks for the serialized, temporary action-lab receipt."""

from macwise_eval.action_lab import evaluate_action_lab
from macwise_eval.metrics import bounded_axis


def passing_receipt() -> dict[str, object]:
    return {
        "schema_version": 1,
        "lab_kind": "temporary_synthetic_bundle",
        "source_before": {"exists": True, "payload_sha256": "a" * 64},
        "after_apply": {"source_exists": False, "trash_exists": True},
        "interrupted_recovery": {"state": "interrupted", "source_exists": True},
        "after_undo": {"source_exists": True, "trash_exists": False, "payload_sha256": "a" * 64},
        "sentinel": {"unchanged": True},
        "journal": {"apply_state": "succeeded", "final_state": "undone"},
    }


def test_action_lab_accepts_a_complete_verified_temporary_round_trip() -> None:
    result = evaluate_action_lab(passing_receipt())

    assert result.passed
    assert result.failures == ()


def test_action_lab_rejects_a_receipt_when_recovery_or_undo_is_not_proven() -> None:
    receipt = passing_receipt()
    receipt["interrupted_recovery"] = {"state": "interrupted", "source_exists": False}
    receipt["after_undo"] = {
        "source_exists": True,
        "trash_exists": True,
        "payload_sha256": "b" * 64,
    }

    result = evaluate_action_lab(receipt)

    assert not result.passed
    assert "recovery did not restore the synthetic source" in result.failures
    assert "undo did not remove the temporary Trash copy" in result.failures
    assert "undo changed the synthetic bundle payload" in result.failures


def test_action_lab_rejects_unrecognized_or_malformed_receipts() -> None:
    result = evaluate_action_lab({"schema_version": 2})

    assert not result.passed
    assert "unsupported action-lab receipt schema" in result.failures


def test_action_lab_verdict_can_be_expressed_as_a_non_compensating_undo_metric() -> None:
    result = evaluate_action_lab(passing_receipt())

    metric = bounded_axis("supported_undo_restoration", numerator=int(result.passed), denominator=1)

    assert (metric.numerator, metric.denominator) == (1, 1)
