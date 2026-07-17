"""Normalized Phase 3 catalog, overlap, and recommendation results."""

from enum import StrEnum
from hashlib import sha256

from pydantic import BaseModel, ConfigDict, Field, model_validator

from macwise.models.analysis import ClaimBasis
from macwise.models.evidence import Reliability


class OverlapCategory(StrEnum):
    """Role-aware relationships allowed by the product contract."""

    EXACT_DUPLICATE = "exact_duplicate"
    SAME_PRODUCT_INSTALLED_TWICE = "same_product_installed_twice"
    STRONG_SUBSTITUTE = "strong_substitute"
    PARTIAL_OVERLAP = "partial_overlap"
    COMPLEMENTARY_TOOLS = "complementary_tools"
    RUNTIME_AND_FRONTEND = "runtime_and_frontend"
    DEPENDENCY_AND_USER_FACING_APP = "dependency_and_user_facing_app"
    LEGACY_AND_SUCCESSOR = "legacy_and_successor"
    NOT_ACTUALLY_RELATED = "not_actually_related"


class LearningValue(StrEnum):
    """Coarse catalog context, not a personalized productivity promise."""

    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    UNKNOWN = "unknown"


class RecommendationAction(StrEnum):
    """Read-only guidance that cannot authorize a host change."""

    KEEP = "keep"
    LEARN = "learn"
    KEEP_TOGETHER = "keep_together"
    REVIEW_CONSOLIDATION = "review_consolidation"
    NO_RECOMMENDATION = "no_recommendation"


class CatalogAssessment(BaseModel):
    """An exact, versioned catalog match for one installed record."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    subject_id: str = Field(min_length=1)
    catalog_key: str = Field(min_length=1)
    catalog_version: str = Field(min_length=1)
    catalog_source: str = Field(min_length=1)
    roles: tuple[str, ...] = Field(min_length=1)
    capabilities: tuple[str, ...] = ()
    unique_capabilities: tuple[str, ...] = ()
    learning_value: LearningValue = LearningValue.UNKNOWN
    learning_statement: str = Field(min_length=1)
    basis: ClaimBasis
    confidence: Reliability
    limitations: tuple[str, ...] = ()


class OverlapRelation(BaseModel):
    """One evidence-qualified relationship between two installed records."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    left_subject_id: str = Field(min_length=1)
    right_subject_id: str = Field(min_length=1)
    category: OverlapCategory
    statement: str = Field(min_length=1)
    shared_capabilities: tuple[str, ...] = ()
    left_unique_capabilities: tuple[str, ...] = ()
    right_unique_capabilities: tuple[str, ...] = ()
    basis: ClaimBasis
    confidence: Reliability
    limitations: tuple[str, ...] = ()

    @model_validator(mode="after")
    def require_distinct_subjects(self) -> "OverlapRelation":
        """A relationship must connect two different installed records."""
        if self.left_subject_id == self.right_subject_id:
            raise ValueError("overlap subjects must be distinct")
        return self


class GuardedRecommendation(BaseModel):
    """Evidence-linked guidance with explicit prerequisites and limitations."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    subject_ids: tuple[str, ...] = Field(min_length=1)
    action: RecommendationAction
    statement: str = Field(min_length=1)
    basis: ClaimBasis
    confidence: Reliability
    learning_value: LearningValue = LearningValue.UNKNOWN
    prerequisites: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    @model_validator(mode="after")
    def require_unique_subjects(self) -> "GuardedRecommendation":
        """Prevent duplicate subjects from inflating recommendation scope."""
        if len(set(self.subject_ids)) != len(self.subject_ids):
            raise ValueError("recommendation subjects must be unique")
        return self


def _stable_id(scope: str, *values: str) -> str:
    normalized = "\0".join(value.strip().casefold() for value in values)
    digest = sha256(f"{scope}\0{normalized}".encode()).hexdigest()[:20]
    return f"{scope}:{digest}"


def stable_overlap_id(
    category: OverlapCategory,
    left_subject_id: str,
    right_subject_id: str,
) -> str:
    """Return an order-independent relationship ID without raw identifiers."""
    left, right = sorted((left_subject_id, right_subject_id), key=str.casefold)
    return _stable_id("overlap", category.value, left, right)


def stable_recommendation_id(
    action: RecommendationAction,
    subject_ids: tuple[str, ...],
) -> str:
    """Return an order-independent guidance ID without raw identifiers."""
    subjects = tuple(sorted(subject_ids, key=str.casefold))
    return _stable_id("recommendation", action.value, *subjects)
