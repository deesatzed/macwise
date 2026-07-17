"""Pure exact approval fingerprints and phrases for reviewed digests."""

import hmac
import re

_SHA256 = re.compile(r"[0-9a-f]{64}")


class ApprovalError(ValueError):
    """The caller did not provide the exact review-bound approval phrase."""


def approval_fingerprint(full_digest: str) -> str:
    """Return the visible 16-character fingerprint for one full digest."""
    if _SHA256.fullmatch(full_digest) is None:
        raise ValueError("Approval requires a full lowercase SHA-256 digest")
    return full_digest[:16].upper()


def apply_approval_phrase(full_digest: str) -> str:
    """Return the exact phrase consenting to one plan digest."""
    return f"APPLY {approval_fingerprint(full_digest)}"


def undo_approval_phrase(full_digest: str) -> str:
    """Return the exact phrase consenting to one execution-manifest digest."""
    return f"UNDO {approval_fingerprint(full_digest)}"


def require_approval(full_digest: str, provided: str, *, verb: str) -> None:
    """Reject anything except the exact phrase for the requested supported verb."""
    if verb not in {"APPLY", "UNDO"}:
        raise ValueError("Approval verb must be APPLY or UNDO")
    expected = f"{verb} {approval_fingerprint(full_digest)}"
    if not hmac.compare_digest(provided, expected):
        raise ApprovalError("MacWise requires the exact approval phrase shown for this review.")
