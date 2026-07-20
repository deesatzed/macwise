"""Strict local parsers for product JSON; this module never imports product models."""

import json
from dataclasses import dataclass
from enum import StrEnum
from typing import cast

from macwise_eval.claims import ExtractedClaim, ExtractedClaimKind


class ProductOutputKind(StrEnum):
    """Recognized serialized product artifact kinds."""

    AUDIT = "audit"
    CHECKUP = "checkup"
    PLAN = "plan"
    EXECUTION = "execution"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class ParsedProductOutput:
    """Claims and limitations derived from one recognized product JSON document."""

    kind: ProductOutputKind
    schema_version: int | None
    claims: tuple[ExtractedClaim, ...]
    limitations: tuple[str, ...]


def _token(value: object) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def _claim(
    kind: ExtractedClaimKind,
    subject: object,
    value: str | int | bool | None,
    pointer: str,
) -> ExtractedClaim:
    subject_text = str(subject)
    return ExtractedClaim(
        claim_id=f"{kind.value}:{_token(subject_text)}:{_token(pointer)}",
        kind=kind,
        subject=subject_text,
        value=value,
        pointer=pointer,
    )


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _audit(document: dict[str, object], schema_version: int) -> ParsedProductOutput:
    if schema_version != 4:
        return ParsedProductOutput(
            kind=ProductOutputKind.INCONCLUSIVE,
            schema_version=schema_version,
            claims=(),
            limitations=(f"unsupported audit schema version {schema_version}",),
        )
    claims: list[ExtractedClaim] = []
    for index, raw_volume in enumerate(cast(list[object], document.get("volumes", []))):
        if not isinstance(raw_volume, dict):
            continue
        volume = cast(dict[str, object], raw_volume)
        subject = volume.get("id", f"volume-index-{index}")
        free_bytes = volume.get("free_bytes")
        if isinstance(free_bytes, int) and not isinstance(free_bytes, bool):
            claims.append(
                _claim(ExtractedClaimKind.FACT, subject, free_bytes, f"/volumes/{index}/free_bytes")
            )
        mounted = volume.get("mount_point")
        if isinstance(mounted, str):
            claims.append(
                _claim(ExtractedClaimKind.FACT, subject, mounted, f"/volumes/{index}/mount_point")
            )

    for index, raw_finding in enumerate(cast(list[object], document.get("findings", []))):
        if not isinstance(raw_finding, dict):
            continue
        finding = cast(dict[str, object], raw_finding)
        subject = finding.get("subject_id", f"finding-index-{index}")
        basis = finding.get("basis")
        claim_kind = (
            ExtractedClaimKind.FACT if basis == "verified" else ExtractedClaimKind.INFERENCE
        )
        statement = _string_or_none(finding.get("statement"))
        if statement is not None:
            claims.append(_claim(claim_kind, subject, statement, f"/findings/{index}"))
        for limitation_index, limitation in enumerate(
            cast(list[object], finding.get("limitations", []))
        ):
            if isinstance(limitation, str):
                claims.append(
                    _claim(
                        ExtractedClaimKind.UNCERTAINTY,
                        subject,
                        limitation,
                        f"/findings/{index}/limitations/{limitation_index}",
                    )
                )

    for index, raw_recommendation in enumerate(
        cast(list[object], document.get("recommendations", []))
    ):
        if not isinstance(raw_recommendation, dict):
            continue
        recommendation = cast(dict[str, object], raw_recommendation)
        subject = recommendation.get("subject_id", f"recommendation-index-{index}")
        action = _string_or_none(recommendation.get("action"))
        if action is not None:
            claims.append(
                _claim(
                    ExtractedClaimKind.GUIDANCE, subject, action, f"/recommendations/{index}/action"
                )
            )
    return ParsedProductOutput(
        kind=ProductOutputKind.AUDIT,
        schema_version=schema_version,
        claims=tuple(claims),
        limitations=(),
    )


def _checkup(document: dict[str, object]) -> ParsedProductOutput:
    claims: list[ExtractedClaim] = []
    for index, raw_priority in enumerate(cast(list[object], document.get("priorities", []))):
        if not isinstance(raw_priority, dict):
            continue
        priority = cast(dict[str, object], raw_priority)
        subject = priority.get("key", f"priority-index-{index}")
        reason = _string_or_none(priority.get("reason"))
        if reason is not None:
            claims.append(
                _claim(ExtractedClaimKind.PRIORITY, subject, reason, f"/priorities/{index}")
            )
        limitation = _string_or_none(priority.get("limitation"))
        if limitation is not None:
            claims.append(
                _claim(
                    ExtractedClaimKind.UNCERTAINTY,
                    subject,
                    limitation,
                    f"/priorities/{index}/limitation",
                )
            )
    return ParsedProductOutput(
        kind=ProductOutputKind.CHECKUP,
        schema_version=None,
        claims=tuple(claims),
        limitations=(),
    )


def _plan(document: dict[str, object], schema_version: int) -> ParsedProductOutput:
    if schema_version != 2:
        return ParsedProductOutput(
            kind=ProductOutputKind.INCONCLUSIVE,
            schema_version=schema_version,
            claims=(),
            limitations=(f"unsupported plan schema version {schema_version}",),
        )
    claims: list[ExtractedClaim] = []
    for index, raw_action in enumerate(cast(list[object], document.get("actions", []))):
        if not isinstance(raw_action, dict):
            continue
        action = cast(dict[str, object], raw_action)
        subject = action.get("subject_id", f"action-index-{index}")
        kind = _string_or_none(action.get("kind"))
        if kind is not None:
            claims.append(
                _claim(ExtractedClaimKind.ACTION, subject, kind, f"/actions/{index}/kind")
            )
    for index, raw_check in enumerate(cast(list[object], document.get("checks", []))):
        if not isinstance(raw_check, dict):
            continue
        check = cast(dict[str, object], raw_check)
        subject = check.get("subject_id", f"check-index-{index}")
        outcome = _string_or_none(check.get("outcome"))
        if outcome is not None:
            claims.append(
                _claim(ExtractedClaimKind.GUIDANCE, subject, outcome, f"/checks/{index}/outcome")
            )
    return ParsedProductOutput(
        kind=ProductOutputKind.PLAN,
        schema_version=schema_version,
        claims=tuple(claims),
        limitations=(),
    )


def _execution(document: dict[str, object], schema_version: int) -> ParsedProductOutput:
    if schema_version != 1:
        return ParsedProductOutput(
            kind=ProductOutputKind.INCONCLUSIVE,
            schema_version=schema_version,
            claims=(),
            limitations=(f"unsupported execution schema version {schema_version}",),
        )
    claims: list[ExtractedClaim] = []
    for index, raw_action in enumerate(cast(list[object], document.get("actions", []))):
        if not isinstance(raw_action, dict):
            continue
        action = cast(dict[str, object], raw_action)
        state = _string_or_none(action.get("state"))
        subject = action.get("subject_id", f"execution-index-{index}")
        if state in {"undone", "undo_failed", "undo_in_progress"}:
            claims.append(
                _claim(ExtractedClaimKind.UNDO, subject, state, f"/actions/{index}/state")
            )
    return ParsedProductOutput(
        kind=ProductOutputKind.EXECUTION,
        schema_version=schema_version,
        claims=tuple(claims),
        limitations=(),
    )


def parse_product_output(text: str) -> ParsedProductOutput:
    """Parse supported serialized output without executing or importing the product."""
    try:
        value: object = json.loads(text)
    except json.JSONDecodeError:
        return ParsedProductOutput(
            kind=ProductOutputKind.INCONCLUSIVE,
            schema_version=None,
            claims=(),
            limitations=("product output is not valid JSON",),
        )
    if not isinstance(value, dict):
        return ParsedProductOutput(
            kind=ProductOutputKind.INCONCLUSIVE,
            schema_version=None,
            claims=(),
            limitations=("product output must contain an object",),
        )
    document = cast(dict[str, object], value)
    schema_version = document.get("schema_version")
    if "audit_id" in document and isinstance(schema_version, int):
        return _audit(document, schema_version)
    if "plan_id" in document and isinstance(schema_version, int):
        return _plan(document, schema_version)
    if "run_id" in document and isinstance(schema_version, int):
        return _execution(document, schema_version)
    if "priorities" in document and "changed_mac" in document:
        return _checkup(document)
    return ParsedProductOutput(
        kind=ProductOutputKind.INCONCLUSIVE,
        schema_version=schema_version if isinstance(schema_version, int) else None,
        claims=(),
        limitations=("unsupported product output shape",),
    )
