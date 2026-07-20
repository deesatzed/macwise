"""Deterministic local I/O for evaluator capsules and receipts."""

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from macwise_eval.models import CapsuleManifest


def canonical_json(value: BaseModel | dict[str, Any]) -> str:
    """Serialize a model or JSON-compatible mapping deterministically with a final newline."""
    document: Any
    if isinstance(value, BaseModel):
        document = value.model_dump(mode="json", exclude_none=True)
    else:
        document = value
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def receipt_digest(path: Path) -> str:
    """Return the SHA-256 digest of one regular receipt file."""
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"receipt is not a regular file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_receipts(capsule_dir: Path, manifest: CapsuleManifest) -> tuple[str, ...]:
    """Return deterministic receipt-integrity failures without reading outside the capsule."""
    root = capsule_dir.resolve()
    failures: list[str] = []
    for receipt in manifest.receipts:
        path = (root / receipt.relative_path).resolve()
        if not path.is_relative_to(root):
            failures.append(f"{receipt.receipt_id}: path escapes capsule")
        elif not path.exists():
            failures.append(f"{receipt.receipt_id}: missing receipt")
        elif receipt_digest(path) != receipt.sha256:
            failures.append(f"{receipt.receipt_id}: digest mismatch")
    return tuple(failures)
