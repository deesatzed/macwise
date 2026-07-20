"""Typed claims extracted from serialized product output only."""

from dataclasses import dataclass
from enum import StrEnum


class ExtractedClaimKind(StrEnum):
    """Claim categories independently recognized by the evaluator."""

    FACT = "fact"
    INFERENCE = "inference"
    UNCERTAINTY = "uncertainty"
    PRIORITY = "priority"
    GUIDANCE = "guidance"
    ACTION = "action"
    UNDO = "undo"


@dataclass(frozen=True)
class ExtractedClaim:
    """One inert claim with a JSON pointer back to the product artifact."""

    claim_id: str
    kind: ExtractedClaimKind
    subject: str
    value: str | int | bool | None
    pointer: str
