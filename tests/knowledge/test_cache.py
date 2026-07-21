"""Behavioral tests for the local public-purpose claim cache."""

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from pydantic import HttpUrl

from macwise.knowledge.cache import PublicClaimCache
from macwise.models.knowledge import (
    ClaimConfidence,
    LookupIdentity,
    LookupStatus,
    MatchMethod,
    PublicPurposeClaim,
    PublicSourceType,
)

NOW = datetime(2026, 7, 20, 12, tzinfo=UTC)


def identity(name: str = "Focus") -> LookupIdentity:
    return LookupIdentity(
        bundle_id=f"com.example.{name.casefold()}",
        name=name,
        publisher="Example, Inc.",
        version="2.4.1",
    )


def claim(name: str = "Focus", **overrides: object) -> PublicPurposeClaim:
    item = identity(name)
    values: dict[str, Any] = {
        "identity": item,
        "purpose": f"{name} is a focused writing application.",
        "source_url": HttpUrl(f"https://example.com/{name.casefold()}"),
        "source_type": PublicSourceType.PUBLISHER,
        "retrieved_at": NOW - timedelta(minutes=1),
        "expires_at": NOW + timedelta(days=30),
        "confidence": ClaimConfidence.HIGH,
        "match_method": MatchMethod.BUNDLE_ID_EXACT,
        "limitation": "Public information does not prove local use or safety.",
    }
    values.update(overrides)
    return PublicPurposeClaim(**values)


def test_exact_identity_gets_a_fresh_cached_claim(tmp_path: Path) -> None:
    cache = PublicClaimCache(tmp_path)
    expected = claim()

    assert cache.store(expected).status is LookupStatus.RESOLVED

    actual = cache.lookup(expected.identity, now=NOW)

    assert actual.status is LookupStatus.RESOLVED
    assert actual.claim == expected
    assert actual.reason == "Found fresh public app information in the local cache."


def test_cache_refuses_a_claim_at_its_exact_expiry_instant(tmp_path: Path) -> None:
    cache = PublicClaimCache(tmp_path)
    expected = claim()
    cache.store(expected)

    actual = cache.lookup(expected.identity, now=expected.expires_at)

    assert actual.status is LookupStatus.UNAVAILABLE
    assert actual.claim is None


def test_injected_clock_mismatch_degrades_to_unavailable_not_an_expiry_exception(
    tmp_path: Path,
) -> None:
    cache = PublicClaimCache(tmp_path)
    stale = claim(
        retrieved_at=NOW - timedelta(days=60),
        expires_at=NOW - timedelta(days=1),
    )
    entry = cache.path_for(stale.identity)
    entry.parent.mkdir(parents=True)
    entry.write_text(stale.model_dump_json(), encoding="utf-8")

    actual = cache.lookup(stale.identity, now=NOW - timedelta(days=2))

    assert actual.status is LookupStatus.UNAVAILABLE
    assert actual.claim is None


@pytest.mark.parametrize("case", ["expired", "mismatched", "malformed", "partial"])
def test_unusable_cache_data_is_refused(tmp_path: Path, case: str) -> None:
    cache = PublicClaimCache(tmp_path)
    expected = claim()
    cache.store(expected)
    entry = cache.path_for(expected.identity)
    if case == "expired":
        stale = claim(
            retrieved_at=NOW - timedelta(days=60),
            expires_at=NOW - timedelta(days=1),
        )
        entry.write_text(stale.model_dump_json(), encoding="utf-8")
    elif case == "mismatched":
        entry.write_text(claim("Other").model_dump_json(), encoding="utf-8")
    elif case == "malformed":
        entry.write_text("{not JSON", encoding="utf-8")
    else:
        entry.write_text('{"purpose":"partial"}', encoding="utf-8")

    actual = cache.lookup(expected.identity, now=NOW)

    assert actual.status is LookupStatus.UNAVAILABLE
    assert actual.claim is None
    assert actual.identity == expected.identity


def test_symlinked_cache_data_is_refused_without_reading_the_target(tmp_path: Path) -> None:
    cache = PublicClaimCache(tmp_path)
    expected = claim()
    outside = tmp_path / "outside.json"
    outside.write_text(expected.model_dump_json(), encoding="utf-8")
    entry = cache.path_for(expected.identity)
    entry.parent.mkdir(parents=True)
    entry.symlink_to(outside)

    actual = cache.lookup(expected.identity, now=NOW)

    assert actual.status is LookupStatus.UNAVAILABLE
    assert actual.claim is None


def test_directory_swap_cannot_redirect_an_entry_read_to_a_symlink_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = PublicClaimCache(tmp_path)
    expected = claim()
    replacement = claim(purpose="Outside cache data must never be read.")
    assert cache.store(expected).status is LookupStatus.RESOLVED
    outside = tmp_path / "outside"
    outside.mkdir()
    outside_entry = outside / cache.path_for(expected.identity).name
    outside_entry.write_text(replacement.model_dump_json(), encoding="utf-8")
    original_open = os.open
    swapped = False

    def swap_directory_before_entry_open(
        path: str | os.PathLike[str], flags: int, mode: int = 0o777, *, dir_fd: int | None = None
    ) -> int:
        nonlocal swapped
        if not swapped and str(path).endswith(".json"):
            swapped = True
            cache.cache_dir.rename(tmp_path / "saved-cache")
            cache.cache_dir.symlink_to(outside, target_is_directory=True)
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr("macwise.knowledge.cache.os.open", swap_directory_before_entry_open)
    try:
        actual = cache.lookup(expected.identity, now=NOW)
    finally:
        if cache.cache_dir.is_symlink():
            cache.cache_dir.unlink()

    assert actual.status is LookupStatus.RESOLVED
    assert actual.claim == expected


def test_permissive_existing_cache_directory_is_refused(tmp_path: Path) -> None:
    cache = PublicClaimCache(tmp_path)
    cache.cache_dir.mkdir(parents=True)
    cache.cache_dir.chmod(0o755)

    assert cache.store(claim()).status is LookupStatus.UNAVAILABLE
    assert cache.lookup(identity(), now=NOW).status is LookupStatus.UNAVAILABLE


def test_permissive_existing_state_root_is_refused(tmp_path: Path) -> None:
    state_root = tmp_path / "state"
    state_root.mkdir(mode=0o700)
    cache = PublicClaimCache(state_root)
    state_root.chmod(0o755)

    assert cache.store(claim()).status is LookupStatus.UNAVAILABLE
    assert cache.lookup(identity(), now=NOW).status is LookupStatus.UNAVAILABLE


def test_write_stages_then_atomically_activates_a_complete_claim(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = PublicClaimCache(tmp_path)
    original = claim()
    replacement = claim(purpose="A replacement purpose.")
    assert cache.store(original).status is LookupStatus.RESOLVED

    def interrupted_replace(source: object, destination: object, **kwargs: object) -> None:
        assert isinstance(source, str)
        assert destination == cache.path_for(original.identity).name
        directory_descriptor = kwargs["src_dir_fd"]
        assert isinstance(directory_descriptor, int)
        descriptor = os.open(source, os.O_RDONLY, dir_fd=directory_descriptor)
        try:
            staged = os.read(descriptor, 16_384)
        finally:
            os.close(descriptor)
        assert json.loads(staged)["purpose"] == replacement.purpose
        assert cache.lookup(original.identity, now=NOW).claim == original
        raise OSError("simulated interrupted activation")

    monkeypatch.setattr("macwise.knowledge.cache.os.replace", interrupted_replace)

    result = cache.store(replacement)

    assert result.status is LookupStatus.UNAVAILABLE
    assert cache.lookup(original.identity, now=NOW).claim == original
    assert list(cache.cache_dir.glob("*.tmp")) == []


def test_write_does_not_activate_a_partially_written_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = PublicClaimCache(tmp_path)
    expected = claim()
    original_write = os.write
    first_write = True

    def short_write(descriptor: int, data: bytes) -> int:
        nonlocal first_write
        if first_write:
            first_write = False
            return original_write(descriptor, data[:7])
        return original_write(descriptor, data)

    monkeypatch.setattr("macwise.knowledge.cache.os.write", short_write)

    assert cache.store(expected).status is LookupStatus.RESOLVED
    assert cache.lookup(expected.identity, now=NOW).claim == expected


def test_retention_removes_only_old_claim_entries_not_other_state(tmp_path: Path) -> None:
    audit = tmp_path / "audits" / "audit.json"
    audit.parent.mkdir()
    audit.write_text('{"private":"audit"}', encoding="utf-8")
    history = tmp_path / "history.json"
    history.write_text('{"private":"history"}', encoding="utf-8")
    cache = PublicClaimCache(tmp_path, max_entries=2)

    for name in ("First", "Second", "Third"):
        assert cache.store(claim(name)).status is LookupStatus.RESOLVED

    assert len(list(cache.cache_dir.glob("*.json"))) == 2
    assert audit.read_text(encoding="utf-8") == '{"private":"audit"}'
    assert history.read_text(encoding="utf-8") == '{"private":"history"}'


def test_pruning_failure_after_atomic_activation_does_not_report_storage_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = PublicClaimCache(tmp_path)
    expected = claim()

    def pruning_failure(directory_descriptor: int) -> None:
        assert directory_descriptor >= 0
        raise OSError("simulated retention failure")

    monkeypatch.setattr(cache, "_prune", pruning_failure)

    assert cache.store(expected).status is LookupStatus.RESOLVED
    assert cache.lookup(expected.identity, now=NOW).claim == expected


def test_cache_record_contains_one_claim_and_no_inventory_or_lookup_history(tmp_path: Path) -> None:
    cache = PublicClaimCache(tmp_path)
    expected = claim()

    cache.store(expected)

    record = json.loads(cache.path_for(expected.identity).read_text(encoding="utf-8"))
    assert record == expected.model_dump(mode="json")
    assert "inventory" not in record
    assert "lookup_history" not in record
    assert "audit" not in record


def test_cache_read_and_write_errors_become_explicit_unavailable_results(tmp_path: Path) -> None:
    cache = PublicClaimCache(tmp_path)
    expected = claim()
    cache.cache_dir.mkdir(parents=True)
    cache.cache_dir.chmod(0o400)
    try:
        write_result = cache.store(expected)
    finally:
        cache.cache_dir.chmod(0o700)

    assert write_result.status is LookupStatus.UNAVAILABLE
    assert write_result.claim is None
    assert cache.lookup(expected.identity, now=NOW).status is LookupStatus.UNRESOLVED

    cache.path_for(expected.identity).parent.mkdir(parents=True, exist_ok=True)
    cache.path_for(expected.identity).write_text(expected.model_dump_json(), encoding="utf-8")
    cache.cache_dir.chmod(0o000)
    try:
        read_result = cache.lookup(expected.identity, now=NOW)
    finally:
        cache.cache_dir.chmod(0o700)

    assert read_result.status is LookupStatus.UNAVAILABLE
    assert read_result.claim is None
