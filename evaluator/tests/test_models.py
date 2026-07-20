"""Strict immutable contracts for independent evaluation evidence."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from macwise_eval.io import canonical_json, receipt_digest, verify_receipts
from macwise_eval.models import (
    AxisResult,
    CapsuleManifest,
    ClaimKind,
    ClaimVerdict,
    ClaimVerdictKind,
    CorpusRole,
    DisclosureClass,
    EnvironmentIdentity,
    EvaluationReport,
    ExpectedClaim,
    FinalVerdict,
    PolicyExpectation,
    ProvenanceClass,
    Receipt,
    ScenarioOracle,
    Severity,
    ToolVersion,
)

NOW = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)


def environment() -> EnvironmentIdentity:
    return EnvironmentIdentity(
        macos_product_version="27.0.0",
        macos_build="24A123",
        darwin_version="27.0.0",
        architecture="arm64",
        tools=(ToolVersion(name="python", version="3.12.11"),),
    )


def receipt() -> Receipt:
    return Receipt(
        receipt_id="storage-reference",
        relative_path="reference/storage.json",
        sha256="a" * 64,
        source="statvfs",
        collected_at=NOW,
    )


def manifest() -> CapsuleManifest:
    return CapsuleManifest(
        capsule_id="synthetic-storage-001",
        provenance=ProvenanceClass.SYNTHETIC,
        disclosure=DisclosureClass.PUBLIC,
        corpus_role=CorpusRole.DEVELOPMENT,
        captured_at=NOW,
        environment=environment(),
        macwise_version="1.0.0rc1",
        audit_schema_version=4,
        receipts=(receipt(),),
        oracle_version="1",
        reviewed_sanitized=True,
    )


def test_manifest_is_strict_frozen_and_records_environment_provenance() -> None:
    document = manifest()

    assert document.model_config.get("frozen") is True
    assert document.environment.darwin_version == "27.0.0"
    assert document.receipts[0].relative_path == "reference/storage.json"
    with pytest.raises(ValidationError):
        CapsuleManifest.model_validate({**document.model_dump(), "unexpected": "value"})
    with pytest.raises(ValidationError):
        document.capsule_id = "changed"  # type: ignore[misc]


def test_manifest_rejects_unsafe_or_inconsistent_disclosure() -> None:
    base = manifest().model_dump()

    with pytest.raises(ValidationError, match="relative_path"):
        Receipt.model_validate({**receipt().model_dump(), "relative_path": "../../private.json"})
    with pytest.raises(ValidationError, match="relative_path"):
        Receipt.model_validate({**receipt().model_dump(), "relative_path": "/tmp/private.json"})
    with pytest.raises(ValidationError, match="SHA-256"):
        Receipt.model_validate({**receipt().model_dump(), "sha256": "not-a-digest"})
    with pytest.raises(ValidationError, match="live_private"):
        CapsuleManifest.model_validate(
            {
                **base,
                "provenance": ProvenanceClass.LIVE_PRIVATE,
                "disclosure": DisclosureClass.PUBLIC,
            }
        )
    with pytest.raises(ValidationError, match="reviewed_sanitized"):
        CapsuleManifest.model_validate({**base, "reviewed_sanitized": False})


def test_oracle_and_report_require_unique_typed_records() -> None:
    expected = ExpectedClaim(
        claim_id="mounted-free-space",
        kind=ClaimKind.FACT,
        subject="volume:root",
        expected_value="157 GiB",
        required=True,
    )
    policy = PolicyExpectation(
        policy_id="MW-EVAL-001",
        severity=Severity.CRITICAL,
        expected_outcome="pass",
    )
    oracle = ScenarioOracle(
        scenario_id="storage-mounted",
        version="1",
        expected_claims=(expected,),
        policy_expectations=(policy,),
        required_uncertainties=("related data is not reclaimable-space proof",),
    )
    verdict = ClaimVerdict(
        claim_id=expected.claim_id,
        kind=ClaimVerdictKind.CORRECT,
        reason="The value matches the independent receipt.",
        product_pointers=("/volumes/0/free_space",),
        receipt_ids=("storage-reference",),
    )
    report = EvaluationReport(
        capsule_id=manifest().capsule_id,
        oracle_version=oracle.version,
        contract_digest="b" * 64,
        claim_verdicts=(verdict,),
        axes=(AxisResult(name="factual_accuracy", numerator=1, denominator=1),),
        final_verdict=FinalVerdict.PASS,
        limitations=("Synthetic evidence does not prove live-Mac behavior.",),
    )

    assert report.axes[0].rate == 1.0
    with pytest.raises(ValidationError, match="unique"):
        ScenarioOracle.model_validate(
            {**oracle.model_dump(), "expected_claims": (expected, expected)}
        )
    with pytest.raises(ValidationError, match="denominator"):
        AxisResult(name="unsafe", numerator=1, denominator=0)
    with pytest.raises(ValidationError, match="numerator"):
        AxisResult(name="unsafe", numerator=2, denominator=1)


def test_canonical_json_and_receipt_verification_are_byte_stable(tmp_path: Path) -> None:
    capsule_dir = tmp_path / "capsule"
    receipt_path = capsule_dir / "reference" / "storage.json"
    receipt_path.parent.mkdir(parents=True)
    receipt_path.write_text('{"free_bytes":168577466368}\n', encoding="utf-8")
    digest = receipt_digest(receipt_path)
    actual_receipt = receipt().model_copy(update={"sha256": digest})
    actual_manifest = manifest().model_copy(update={"receipts": (actual_receipt,)})

    first = canonical_json(actual_manifest)
    second = canonical_json(actual_manifest)

    assert first == second
    assert verify_receipts(capsule_dir, actual_manifest) == ()

    receipt_path.write_text('{"free_bytes":0}\n', encoding="utf-8")
    assert verify_receipts(capsule_dir, actual_manifest) == ("storage-reference: digest mismatch",)


def test_minimal_public_capsule_fixture_is_complete_and_receipt_verified() -> None:
    fixture_root = Path(__file__).parents[1] / "fixtures" / "synthetic" / "minimal"
    loaded_manifest = CapsuleManifest.model_validate_json(
        (fixture_root / "manifest.json").read_text(encoding="utf-8")
    )
    loaded_oracle = ScenarioOracle.model_validate_json(
        (fixture_root / "oracle.json").read_text(encoding="utf-8")
    )

    assert loaded_manifest.disclosure is DisclosureClass.PUBLIC
    assert loaded_oracle.scenario_id == "minimal-storage"
    assert verify_receipts(fixture_root, loaded_manifest) == ()
    assert (
        json.loads((fixture_root / "reference.json").read_text(encoding="utf-8"))["free_bytes"] > 0
    )
