"""Disclosure gates keep real-Mac evaluation receipts outside public artifacts."""

import json
from pathlib import Path

import pytest

from macwise_eval.models import DisclosureClass
from macwise_eval.privacy import (
    DisclosureFindingKind,
    require_public_disclosure,
    scan_text,
)

from .test_models import manifest


def test_disclosure_scanner_finds_private_and_prompt_shaped_values() -> None:
    hostile_document = json.loads(
        (
            Path(__file__).parents[1] / "fixtures" / "privacy" / "hostile-private-values.json"
        ).read_text(encoding="utf-8")
    )
    hostile = hostile_document["contents"]

    findings = scan_text(hostile, known_usernames=("alice",), known_hostnames=("alice-mini",))
    kinds = {finding.kind for finding in findings}

    assert DisclosureFindingKind.HOME_PATH in kinds
    assert DisclosureFindingKind.VOLUME_PATH in kinds
    assert DisclosureFindingKind.HOSTNAME in kinds
    assert DisclosureFindingKind.SERIAL_SHAPED in kinds
    assert DisclosureFindingKind.SECRET_SHAPED in kinds
    assert DisclosureFindingKind.CONTROL_CHARACTER in kinds
    assert DisclosureFindingKind.PROMPT_SHAPED in kinds


def test_public_disclosure_requires_review_and_a_clean_receipt(tmp_path: Path) -> None:
    capsule_dir = tmp_path / "capsule"
    capsule_dir.mkdir()
    receipt_path = capsule_dir / "reference.json"
    receipt_path.write_text('{"path":"/Users/alice/private"}\n', encoding="utf-8")
    private_manifest = manifest().model_copy(
        update={
            "disclosure": DisclosureClass.PRIVATE,
            "reviewed_sanitized": False,
            "receipts": (),
        }
    )

    with pytest.raises(ValueError, match="public"):
        require_public_disclosure(capsule_dir, private_manifest)

    public_manifest = manifest().model_copy(update={"receipts": (), "reviewed_sanitized": True})
    with pytest.raises(ValueError, match="home_path"):
        require_public_disclosure(capsule_dir, public_manifest, known_usernames=("alice",))


def test_scanner_reports_without_rewriting_source_text() -> None:
    original = "api" + "_key='do-not-commit'\n"

    findings = scan_text(original)

    assert findings[0].kind is DisclosureFindingKind.SECRET_SHAPED
    assert original == "api" + "_key='do-not-commit'\n"
