"""MacWise application services."""

from macwise.services.analysis import analyze_usage
from macwise.services.approval import (
    ApprovalError,
    apply_approval_phrase,
    approval_fingerprint,
    require_approval,
    undo_approval_phrase,
)
from macwise.services.audit import AuditService
from macwise.services.overlap import OverlapAnalysis, analyze_overlaps
from macwise.services.planning import PlanningResult, add_candidate

__all__ = [
    "ApprovalError",
    "AuditService",
    "OverlapAnalysis",
    "PlanningResult",
    "add_candidate",
    "analyze_overlaps",
    "analyze_usage",
    "apply_approval_phrase",
    "approval_fingerprint",
    "require_approval",
    "undo_approval_phrase",
]
