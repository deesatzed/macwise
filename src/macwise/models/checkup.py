"""Immutable novice checkup summaries derived from one read-only audit."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

SUPPORTED_FOCUS_COMMANDS = {
    "macwise backups",
    "macwise overlap",
    "macwise review largest",
    "macwise review unknown",
    "macwise review unused",
    "macwise startup",
    "macwise storage",
}


class CheckupPriority(BaseModel):
    """One bounded review domain with its evidence and safest next action."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str = Field(min_length=1)
    title: str = Field(min_length=1)
    observed_count: int = Field(ge=0)
    reason: str = Field(min_length=1)
    evidence: str = Field(min_length=1)
    benefit: str = Field(min_length=1)
    limitation: str = Field(min_length=1)
    next_command: str = Field(min_length=1)

    @model_validator(mode="after")
    def require_supported_focus_command(self) -> "CheckupPriority":
        if self.next_command not in SUPPORTED_FOCUS_COMMANDS:
            raise ValueError("next_command must be a supported focused command")
        return self


class CheckupSummary(BaseModel):
    """A short first-run interpretation that never mutates the host."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    collected_at: datetime
    priorities: tuple[CheckupPriority, ...] = Field(max_length=5)
    report_confidence: int = Field(ge=0, le=100)
    largest_missing_evidence: str = Field(min_length=1)
    confidence_limitation: str = (
        "This measures report coverage and structure, not a health grade or personalized truth."
    )
    changed_mac: bool = False

    @model_validator(mode="after")
    def remain_read_only(self) -> "CheckupSummary":
        if self.changed_mac:
            raise ValueError("a checkup cannot report that it changed the Mac")
        return self
