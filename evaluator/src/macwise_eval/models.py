"""Strict, immutable interchange models owned by the independent evaluator."""

from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictFrozenModel(BaseModel):
    """Reject unrecognized data and prevent post-validation mutation."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ProvenanceClass(StrEnum):
    """How an evidence capsule originated."""

    SYNTHETIC = "synthetic"
    DERIVED_SANITIZED = "derived_sanitized"
    LIVE_PRIVATE = "live_private"
    CONTROLLED_MUTATION = "controlled_mutation"


class DisclosureClass(StrEnum):
    """Whether a capsule may leave the private local evaluation area."""

    PRIVATE = "private"
    PUBLIC = "public"


class CorpusRole(StrEnum):
    """How a capsule may be used in an evaluation corpus."""

    DEVELOPMENT = "development"
    FROZEN_ACCEPTANCE = "frozen_acceptance"
    FRESH_HOLDOUT = "fresh_holdout"


class Severity(StrEnum):
    """Policy consequence for an evaluator finding."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ClaimKind(StrEnum):
    """Product-output claim category."""

    FACT = "fact"
    INFERENCE = "inference"
    UNCERTAINTY = "uncertainty"
    PRIORITY = "priority"
    GUIDANCE = "guidance"
    ACTION = "action"
    UNDO = "undo"


class ClaimVerdictKind(StrEnum):
    """Independent judgement of one expected or observed claim."""

    CORRECT = "correct"
    INCORRECT = "incorrect"
    UNSUPPORTED = "unsupported"
    MISSING = "missing"
    UNEVALUABLE = "unevaluable"


class FinalVerdict(StrEnum):
    """Non-averageable evaluator conclusion."""

    PASS = "pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"


class ToolVersion(StrictFrozenModel):
    """One environment tool and its observed version."""

    name: str = Field(min_length=1)
    version: str = Field(min_length=1)


class EnvironmentIdentity(StrictFrozenModel):
    """Exact platform tuple needed to make a compatibility claim."""

    macos_product_version: str = Field(min_length=1)
    macos_build: str = Field(min_length=1)
    darwin_version: str = Field(min_length=1)
    architecture: str = Field(min_length=1)
    tools: tuple[ToolVersion, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def require_unique_tool_names(self) -> "EnvironmentIdentity":
        names = tuple(tool.name for tool in self.tools)
        if len(set(names)) != len(names):
            raise ValueError("tool names must be unique")
        return self


class Receipt(StrictFrozenModel):
    """A content-addressed reference observation within one capsule."""

    receipt_id: str = Field(min_length=1)
    relative_path: str = Field(min_length=1)
    sha256: str = Field(min_length=1)
    source: str = Field(min_length=1)
    collected_at: AwareDatetime
    source_correlated: bool = False

    @field_validator("relative_path")
    @classmethod
    def require_safe_relative_path(cls, value: str) -> str:
        path = Path(value)
        if path.is_absolute() or ".." in path.parts or value in {".", ""}:
            raise ValueError("relative_path must be a contained relative path")
        return value

    @field_validator("sha256")
    @classmethod
    def require_sha256(cls, value: str) -> str:
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("sha256 must be a lowercase SHA-256 digest")
        return value


class CapsuleManifest(StrictFrozenModel):
    """The immutable metadata contract for one evidence capsule."""

    schema_version: Literal[1] = 1
    capsule_id: str = Field(min_length=1)
    provenance: ProvenanceClass
    disclosure: DisclosureClass
    corpus_role: CorpusRole
    captured_at: AwareDatetime
    environment: EnvironmentIdentity
    macwise_version: str = Field(min_length=1)
    audit_schema_version: int = Field(ge=1)
    receipts: tuple[Receipt, ...] = Field(min_length=1)
    oracle_version: str = Field(min_length=1)
    limitations: tuple[str, ...] = ()
    reviewed_sanitized: bool = False

    @model_validator(mode="after")
    def enforce_disclosure_rules(self) -> "CapsuleManifest":
        receipt_ids = tuple(receipt.receipt_id for receipt in self.receipts)
        if len(set(receipt_ids)) != len(receipt_ids):
            raise ValueError("receipt identifiers must be unique")
        if (
            self.provenance is ProvenanceClass.LIVE_PRIVATE
            and self.disclosure is DisclosureClass.PUBLIC
        ):
            raise ValueError("live_private evidence may not be public")
        if self.disclosure is DisclosureClass.PUBLIC and not self.reviewed_sanitized:
            raise ValueError("public capsules require reviewed_sanitized")
        return self


class ExpectedClaim(StrictFrozenModel):
    """A claim the independent oracle expects from a scenario."""

    claim_id: str = Field(min_length=1)
    kind: ClaimKind
    subject: str = Field(min_length=1)
    expected_value: str | int | bool | None = None
    required: bool = True


class PolicyExpectation(StrictFrozenModel):
    """A predeclared safety-policy expectation for one scenario."""

    policy_id: str = Field(min_length=1)
    severity: Severity
    expected_outcome: Literal["pass", "fail", "inconclusive"]


class ScenarioOracle(StrictFrozenModel):
    """Expected facts, uncertainty, and safety outcomes written before product evaluation."""

    schema_version: Literal[1] = 1
    scenario_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    expected_claims: tuple[ExpectedClaim, ...] = ()
    policy_expectations: tuple[PolicyExpectation, ...] = ()
    required_uncertainties: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    @model_validator(mode="after")
    def require_unique_identifiers(self) -> "ScenarioOracle":
        claim_ids = tuple(claim.claim_id for claim in self.expected_claims)
        policy_ids = tuple(expectation.policy_id for expectation in self.policy_expectations)
        if len(set(claim_ids)) != len(claim_ids) or len(set(policy_ids)) != len(policy_ids):
            raise ValueError("claim and policy identifiers must be unique")
        return self


class ClaimVerdict(StrictFrozenModel):
    """One independently traceable judgement of a product claim."""

    claim_id: str = Field(min_length=1)
    kind: ClaimVerdictKind
    reason: str = Field(min_length=1)
    product_pointers: tuple[str, ...] = ()
    receipt_ids: tuple[str, ...] = ()
    policy_ids: tuple[str, ...] = ()


class AxisResult(StrictFrozenModel):
    """One decomposable evaluation metric with an explicit denominator."""

    name: str = Field(min_length=1)
    numerator: int = Field(ge=0)
    denominator: int = Field(gt=0)
    limitations: tuple[str, ...] = ()

    @model_validator(mode="after")
    def require_valid_ratio(self) -> "AxisResult":
        if self.numerator > self.denominator:
            raise ValueError("numerator cannot exceed denominator")
        return self

    @property
    def rate(self) -> float:
        """Return the transparent ratio represented by this metric."""
        return self.numerator / self.denominator


class EvaluationReport(StrictFrozenModel):
    """The stable output of an independent capsule evaluation."""

    schema_version: Literal[1] = 1
    capsule_id: str = Field(min_length=1)
    oracle_version: str = Field(min_length=1)
    contract_digest: str = Field(min_length=1)
    claim_verdicts: tuple[ClaimVerdict, ...]
    axes: tuple[AxisResult, ...]
    final_verdict: FinalVerdict
    limitations: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def require_unique_report_entries(self) -> "EvaluationReport":
        claim_ids = tuple(verdict.claim_id for verdict in self.claim_verdicts)
        axis_names = tuple(axis.name for axis in self.axes)
        if len(set(claim_ids)) != len(claim_ids) or len(set(axis_names)) != len(axis_names):
            raise ValueError("claim verdict and axis identifiers must be unique")
        return self
