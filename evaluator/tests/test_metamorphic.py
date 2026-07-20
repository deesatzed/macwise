"""Scenario registry separates development, frozen acceptance, and fresh holdout evidence."""

from pathlib import Path

import pytest

from macwise_eval.models import CorpusRole
from macwise_eval.mutations import load_scenario_registry, retire_holdout

REGISTRY = Path(__file__).parents[1] / "fixtures" / "scenarios" / "registry.json"


def test_registry_covers_all_required_domains_without_role_conflicts() -> None:
    scenarios = load_scenario_registry(REGISTRY)

    assert {scenario.domain for scenario in scenarios} == {
        "storage",
        "backup",
        "startup",
        "dependencies",
        "overlap",
        "usage",
        "unknown_purpose",
        "partial_collection",
        "hostile_metadata",
        "future_macos",
        "protected_target",
        "undo",
    }
    assert len({scenario.scenario_id for scenario in scenarios}) == 12
    assert any(scenario.corpus_role is CorpusRole.FRESH_HOLDOUT for scenario in scenarios)


def test_inspected_holdout_is_retired_before_it_can_influence_development() -> None:
    holdout = next(
        scenario
        for scenario in load_scenario_registry(REGISTRY)
        if scenario.corpus_role is CorpusRole.FRESH_HOLDOUT
    )

    retired = retire_holdout(holdout)

    assert retired.corpus_role is CorpusRole.DEVELOPMENT
    with pytest.raises(ValueError, match="fresh_holdout"):
        retire_holdout(retired)
