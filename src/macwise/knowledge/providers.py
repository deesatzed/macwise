"""Privacy-bounded interfaces for public app-purpose providers.

Network transport and source parsing deliberately belong to a later layer.
"""

from collections.abc import Iterable
from typing import Protocol

from macwise.models.knowledge import LookupIdentity, LookupStatus, PublicLookupResult


class PublicPurposeProvider(Protocol):
    """Looks up one sanitized application identity at a time."""

    def lookup(self, identity: LookupIdentity) -> PublicLookupResult:
        """Return a typed result without receiving any local audit data."""

        ...


class RecordingPublicPurposeProvider:
    """In-memory provider for tests and deterministic caller exercises."""

    def __init__(self, results: Iterable[PublicLookupResult]) -> None:
        self._results = tuple(results)
        self.calls: list[LookupIdentity] = []

    def lookup(self, identity: object) -> PublicLookupResult:
        """Record one identity and return its configured typed outcome."""

        if not isinstance(identity, LookupIdentity):
            raise TypeError("public lookup accepts exactly one LookupIdentity")
        self.calls.append(identity)
        for result in self._results:
            if result.identity == identity:
                return result
        return PublicLookupResult(
            identity=identity,
            status=LookupStatus.UNRESOLVED,
            reason="No in-memory public result is configured for this identity.",
        )
