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
from macwise.services.execution import ExecutionService, ExecutionServiceError
from macwise.services.overlap import OverlapAnalysis, analyze_overlaps
from macwise.services.planning import PlanningResult, add_candidate
from macwise.services.revalidation import PreparedExecution, RevalidationError, prepare_execution

__all__ = [
    "ApprovalError",
    "AuditService",
    "ExecutionService",
    "ExecutionServiceError",
    "OverlapAnalysis",
    "PlanningResult",
    "PreparedExecution",
    "RevalidationError",
    "add_candidate",
    "analyze_overlaps",
    "analyze_usage",
    "apply_approval_phrase",
    "approval_fingerprint",
    "prepare_execution",
    "require_approval",
    "undo_approval_phrase",
]
