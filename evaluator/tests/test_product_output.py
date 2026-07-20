"""Independent parsing of serialized product output never imports product models."""

import json
from pathlib import Path

from macwise_eval.claims import ExtractedClaimKind
from macwise_eval.product_output import ProductOutputKind, parse_product_output

FIXTURES = Path(__file__).parents[1] / "fixtures" / "product_outputs"


def test_audit_schema_four_extracts_facts_inferences_and_uncertainty_pointers() -> None:
    result = parse_product_output((FIXTURES / "audit-v4.json").read_text(encoding="utf-8"))

    assert result.kind is ProductOutputKind.AUDIT
    assert result.schema_version == 4
    assert any(
        claim.kind is ExtractedClaimKind.FACT
        and claim.subject == "volume:root"
        and claim.value == 168577466368
        and claim.pointer == "/volumes/0/free_bytes"
        for claim in result.claims
    )
    assert any(
        claim.kind is ExtractedClaimKind.INFERENCE and claim.pointer == "/findings/0"
        for claim in result.claims
    )
    assert any(
        claim.kind is ExtractedClaimKind.UNCERTAINTY
        and claim.pointer == "/findings/0/limitations/0"
        for claim in result.claims
    )


def test_checkup_plan_and_execution_outputs_keep_typed_claims_and_pointers() -> None:
    checkup = parse_product_output((FIXTURES / "checkup.json").read_text(encoding="utf-8"))
    plan = parse_product_output((FIXTURES / "plan-v2.json").read_text(encoding="utf-8"))
    execution = parse_product_output((FIXTURES / "execution-v1.json").read_text(encoding="utf-8"))

    assert checkup.kind is ProductOutputKind.CHECKUP
    assert checkup.claims[0].kind is ExtractedClaimKind.PRIORITY
    assert checkup.claims[0].pointer == "/priorities/0"
    assert plan.kind is ProductOutputKind.PLAN
    assert any(claim.kind is ExtractedClaimKind.ACTION for claim in plan.claims)
    assert execution.kind is ProductOutputKind.EXECUTION
    assert any(claim.kind is ExtractedClaimKind.UNDO for claim in execution.claims)


def test_malformed_or_future_document_is_inconclusive_not_a_product_failure() -> None:
    malformed = parse_product_output("[]")
    future = parse_product_output(json.dumps({"schema_version": 99, "audit_id": "future"}))

    assert malformed.kind is ProductOutputKind.INCONCLUSIVE
    assert future.kind is ProductOutputKind.INCONCLUSIVE
    assert malformed.claims == ()
    assert "object" in malformed.limitations[0]
    assert "unsupported" in future.limitations[0]
