"""Deterministic JSON rendering for MacWise audit documents."""

from macwise.models import AuditDocument


def render_json(audit: AuditDocument) -> str:
    """Return schema-backed, indented JSON with a trailing newline."""
    return f"{audit.model_dump_json(indent=2)}\n"
