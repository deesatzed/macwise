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
from macwise.services.checkup import build_checkup
from macwise.services.execution import ExecutionService, ExecutionServiceError
from macwise.services.overlap import OverlapAnalysis, analyze_overlaps
from macwise.services.planning import PlanningResult, add_candidate
from macwise.services.revalidation import PreparedExecution, RevalidationError, prepare_execution
from macwise.services.scoring import score_audit

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
    "build_checkup",
    "prepare_execution",
    "require_approval",
    "score_audit",
    "undo_approval_phrase",
]
