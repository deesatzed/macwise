"""Judge a product-side temporary action lab from its serialized receipt only."""

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class ActionLabResult:
    """Non-averageable safety conclusion for one isolated temporary action run."""

    passed: bool
    failures: tuple[str, ...]


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _bool(section: Mapping[str, object], key: str) -> bool:
    return section.get(key) is True


def evaluate_action_lab(receipt: Mapping[str, object]) -> ActionLabResult:
    """Require evidence for apply, interrupted recovery, undo, and sentinel preservation.

    The evaluator receives no filesystem paths and never invokes the product.  A missing
    field is a failed proof rather than an assumption that the operation was safe.
    """
    if receipt.get("schema_version") != 1 or receipt.get("lab_kind") != "temporary_synthetic_bundle":
        return ActionLabResult(False, ("unsupported action-lab receipt schema",))

    before = _mapping(receipt.get("source_before"))
    applied = _mapping(receipt.get("after_apply"))
    recovered = _mapping(receipt.get("interrupted_recovery"))
    undone = _mapping(receipt.get("after_undo"))
    sentinel = _mapping(receipt.get("sentinel"))
    journal = _mapping(receipt.get("journal"))
    failures: list[str] = []
    before_digest = before.get("payload_sha256")

    if not _bool(before, "exists") or not isinstance(before_digest, str) or len(before_digest) != 64:
        failures.append("synthetic source identity was not captured before apply")
    if _bool(applied, "source_exists") or not _bool(applied, "trash_exists"):
        failures.append("apply did not prove a source-to-temporary-Trash move")
    if recovered.get("state") != "interrupted" or not _bool(recovered, "source_exists"):
        failures.append("recovery did not restore the synthetic source")
    if not _bool(undone, "source_exists"):
        failures.append("undo did not restore the synthetic source")
    if _bool(undone, "trash_exists"):
        failures.append("undo did not remove the temporary Trash copy")
    if undone.get("payload_sha256") != before_digest:
        failures.append("undo changed the synthetic bundle payload")
    if not _bool(sentinel, "unchanged"):
        failures.append("an unrelated sentinel was changed")
    if journal.get("apply_state") != "succeeded" or journal.get("final_state") != "undone":
        failures.append("journal states do not prove completed apply and undo")
    return ActionLabResult(not failures, tuple(failures))
