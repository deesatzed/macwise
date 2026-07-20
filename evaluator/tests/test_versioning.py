"""Compatibility claims require exact environment tuples, never marketing-name guesses."""

from macwise_eval.models import EnvironmentIdentity, ToolVersion
from macwise_eval.versioning import CompatibilityStatus, classify_environment


def environment(build: str = "24A123") -> EnvironmentIdentity:
    return EnvironmentIdentity(
        macos_product_version="27.0.0",
        macos_build=build,
        darwin_version="27.0.0",
        architecture="arm64",
        tools=(ToolVersion(name="python", version="3.12.11"),),
    )


def test_exact_live_tuple_is_validated_but_build_drift_is_not_inherited() -> None:
    validated = (environment(),)

    assert (
        classify_environment(environment(), validated_live=validated)
        is CompatibilityStatus.VALIDATED_LIVE
    )
    assert (
        classify_environment(environment("24A124"), validated_live=validated)
        is CompatibilityStatus.UNKNOWN
    )


def test_replay_and_future_environment_statuses_remain_explicit() -> None:
    current = environment()
    future = EnvironmentIdentity(
        macos_product_version="28.0.0",
        macos_build="25A1",
        darwin_version="28.0.0",
        architecture="arm64",
        tools=(ToolVersion(name="python", version="3.12.11"),),
    )

    assert (
        classify_environment(current, validated_replay=(current,))
        is CompatibilityStatus.VALIDATED_REPLAY
    )
    assert classify_environment(future, validated_live=(current,)) is CompatibilityStatus.UNKNOWN
