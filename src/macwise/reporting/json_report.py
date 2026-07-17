"""Deterministic JSON rendering for MacWise audit documents."""

import json
from typing import Any, cast

from macwise.models import AuditDocument


def render_json(audit: AuditDocument) -> str:
    """Return schema-backed, indented JSON with a trailing newline."""
    return f"{audit.model_dump_json(indent=2)}\n"


def parse_json(text: str) -> AuditDocument:
    """Read a supported audit JSON document and migrate schema 1 in memory."""
    loaded: object = json.loads(text)
    if not isinstance(loaded, dict):
        raise ValueError("Audit JSON must contain an object at the top level.")
    document = cast(dict[str, Any], loaded)
    version = document.get("schema_version")
    if not isinstance(version, int) or isinstance(version, bool) or version not in {1, 2, 3, 4}:
        raise ValueError(f"Unsupported audit schema version {version}.")
    if version in {1, 2, 3}:
        document = {**document, "schema_version": 4}
    return AuditDocument.model_validate(document)
