"""Deterministic scorecard models kept separate from audit interchange data."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

OPPORTUNITY_COMPONENTS = {
    "startup_attention": 20,
    "tool_overlap": 20,
    "storage_review": 20,
    "possible_non_use": 15,
    "knowledge_gaps": 15,
    "backup_attention": 10,
}

USEFULNESS_COMPONENTS = {
    "evidence_coverage": 25,
    "decision_yield": 25,
    "explanation_quality": 20,
    "safety_integrity": 20,
    "review_efficiency": 10,
}


class ScoreComponent(BaseModel):
    """One inspectable score contribution and the evidence behind it."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    score: int = Field(ge=0)
    maximum: int = Field(gt=0)
    observed_count: int = Field(ge=0)
    reason: str = Field(min_length=1)
    limitations: tuple[str, ...] = ()

    @model_validator(mode="after")
    def keep_score_within_maximum(self) -> "ScoreComponent":
        if self.score > self.maximum:
            raise ValueError("score cannot exceed maximum")
        return self


class MacWiseScorecard(BaseModel):
    """Two independent scores describing audit opportunities and result quality."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    opportunity_score: int = Field(ge=0, le=100)
    opportunity_components: tuple[ScoreComponent, ...]
    usefulness_score: int = Field(ge=0, le=100)
    usefulness_components: tuple[ScoreComponent, ...]
    limitations: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_component_contract(self) -> "MacWiseScorecard":
        self._validate_group(
            "opportunity",
            self.opportunity_components,
            OPPORTUNITY_COMPONENTS,
            self.opportunity_score,
        )
        self._validate_group(
            "usefulness",
            self.usefulness_components,
            USEFULNESS_COMPONENTS,
            self.usefulness_score,
        )
        return self

    @staticmethod
    def _validate_group(
        name: str,
        components: tuple[ScoreComponent, ...],
        expected: dict[str, int],
        total: int,
    ) -> None:
        keys = tuple(component.key for component in components)
        if keys != tuple(expected):
            raise ValueError(f"{name} component keys must be {tuple(expected)}")
        maxima = {component.key: component.maximum for component in components}
        if maxima != expected:
            raise ValueError(f"{name} component maxima must be {expected}")
        if sum(component.score for component in components) != total:
            raise ValueError(f"{name}_score must equal its component scores")
