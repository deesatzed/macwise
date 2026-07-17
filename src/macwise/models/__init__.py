"""Public normalized models used across MacWise interfaces."""

from macwise.models.analysis import (
    BackupStatus,
    ClaimBasis,
    Finding,
    FindingTopic,
    PathEvidence,
    StartupKind,
    StartupRecord,
    UsageLabel,
    stable_path_evidence_id,
    stable_startup_id,
)
from macwise.models.audit import AuditDocument, CollectorState, CollectorStatus
from macwise.models.evidence import Evidence, Reliability
from macwise.models.overlap import (
    CatalogAssessment,
    GuardedRecommendation,
    LearningValue,
    OverlapCategory,
    OverlapRelation,
    RecommendationAction,
    stable_overlap_id,
    stable_recommendation_id,
)
from macwise.models.software import EntityType, InstallRole, SoftwareRecord, stable_software_id
from macwise.models.storage import StorageLocation, VolumeRecord, stable_volume_id

__all__ = [
    "AuditDocument",
    "BackupStatus",
    "CatalogAssessment",
    "ClaimBasis",
    "CollectorState",
    "CollectorStatus",
    "EntityType",
    "Evidence",
    "Finding",
    "FindingTopic",
    "GuardedRecommendation",
    "InstallRole",
    "LearningValue",
    "OverlapCategory",
    "OverlapRelation",
    "PathEvidence",
    "RecommendationAction",
    "Reliability",
    "SoftwareRecord",
    "StartupKind",
    "StartupRecord",
    "StorageLocation",
    "UsageLabel",
    "VolumeRecord",
    "stable_overlap_id",
    "stable_path_evidence_id",
    "stable_recommendation_id",
    "stable_software_id",
    "stable_startup_id",
    "stable_volume_id",
]
