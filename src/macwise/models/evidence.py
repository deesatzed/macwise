"""Evidence provenance shared by every MacWise finding."""

from enum import StrEnum

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, JsonValue


class Reliability(StrEnum):
    """How strongly a source supports the value it accompanies."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class Evidence(BaseModel):
    """One observed value and enough provenance to interpret its limits."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: str = Field(min_length=1)
    value: JsonValue
    source: str = Field(min_length=1)
    collected_at: AwareDatetime
    reliability: Reliability
    limitations: tuple[str, ...] = ()
