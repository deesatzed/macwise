"""Exact-environment compatibility classification for evaluator evidence."""

from enum import StrEnum

from macwise_eval.models import EnvironmentIdentity


class CompatibilityStatus(StrEnum):
    """Evidence strength for one exact platform tuple."""

    VALIDATED_LIVE = "validated_live"
    VALIDATED_REPLAY = "validated_replay"
    PROVISIONAL = "provisional"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


def _key(environment: EnvironmentIdentity) -> tuple[object, ...]:
    return (
        environment.macos_product_version,
        environment.macos_build,
        environment.darwin_version,
        environment.architecture,
        tuple((tool.name, tool.version) for tool in environment.tools),
    )


def classify_environment(
    environment: EnvironmentIdentity,
    *,
    validated_live: tuple[EnvironmentIdentity, ...] = (),
    validated_replay: tuple[EnvironmentIdentity, ...] = (),
    provisional: tuple[EnvironmentIdentity, ...] = (),
    unsupported: tuple[EnvironmentIdentity, ...] = (),
) -> CompatibilityStatus:
    """Classify only exact tuples; no product, build, or tool-version drift is inherited."""
    target = _key(environment)
    for status, known in (
        (CompatibilityStatus.VALIDATED_LIVE, validated_live),
        (CompatibilityStatus.VALIDATED_REPLAY, validated_replay),
        (CompatibilityStatus.PROVISIONAL, provisional),
        (CompatibilityStatus.UNSUPPORTED, unsupported),
    ):
        if any(_key(item) == target for item in known):
            return status
    return CompatibilityStatus.UNKNOWN
