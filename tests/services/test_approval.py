import pytest

from macwise.services.approval import (
    ApprovalError,
    apply_approval_phrase,
    approval_fingerprint,
    require_approval,
    undo_approval_phrase,
)

DIGEST = "abcdef0123456789" * 4


def test_approval_fingerprint_and_phrases_bind_exact_full_digest() -> None:
    assert approval_fingerprint(DIGEST) == "ABCDEF0123456789"
    assert apply_approval_phrase(DIGEST) == "APPLY ABCDEF0123456789"
    assert undo_approval_phrase(DIGEST) == "UNDO ABCDEF0123456789"
    require_approval(DIGEST, "APPLY ABCDEF0123456789", verb="APPLY")


@pytest.mark.parametrize(
    "provided",
    (
        "apply ABCDEF0123456789",
        " APPLY ABCDEF0123456789",
        "APPLY ABCDEF0123456789 ",
        "APPLY ABCDEF012345678",
        "APPLY ABCDEF0123456789 extra",
    ),
)
def test_approval_refuses_normalization_prefix_and_suffix_tricks(provided: str) -> None:
    with pytest.raises(ApprovalError, match="exact approval phrase"):
        require_approval(DIGEST, provided, verb="APPLY")


def test_approval_rejects_malformed_full_digest() -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        approval_fingerprint("a" * 16)
