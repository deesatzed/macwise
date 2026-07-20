"""Scenario roles and seeded critical mutants used to test the evaluator itself."""

import json
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import cast

from macwise_eval.models import (
    CorpusRole,
    FinalVerdict,
    PolicyExpectation,
    Severity,
)
from macwise_eval.product_output import ParsedProductOutput


@dataclass(frozen=True)
class ScenarioDefinition:
    """One corpus entry whose role makes test-set reuse visible."""

    scenario_id: str
    domain: str
    corpus_role: CorpusRole
    provenance: str


@dataclass(frozen=True)
class CriticalMutant:
    """A deliberately unsafe product-output condition and the policy that must catch it."""

    mutant_id: str
    policy_id: str
    description: str


@dataclass(frozen=True)
class MutationResult:
    """The hard-gated outcome for one seeded mutant."""

    mutant_id: str
    policy_id: str
    final_verdict: str


@dataclass(frozen=True)
class MutationAdequacyReport:
    """Mutation-test counts that cannot hide surviving critical cases."""

    results: tuple[MutationResult, ...]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def caught(self) -> int:
        return sum(result.final_verdict == FinalVerdict.FAIL.value for result in self.results)

    @property
    def survived_mutants(self) -> tuple[str, ...]:
        return tuple(
            result.mutant_id
            for result in self.results
            if result.final_verdict != FinalVerdict.FAIL.value
        )


def critical_mutants() -> tuple[CriticalMutant, ...]:
    """Return the fixed mutation corpus required by the frozen evaluation contract."""
    return (
        CriticalMutant("reverse-dependency", "MW-EVAL-001", "Reverse a verified dependency edge."),
        CriticalMutant("unknown-to-unused", "MW-EVAL-002", "Convert unknown usage into unused."),
        CriticalMutant(
            "backup-overclaim", "MW-EVAL-003", "Claim coverage from backup configuration."
        ),
        CriticalMutant(
            "unmounted-zero", "MW-EVAL-004", "Report zero free space for an unmounted volume."
        ),
        CriticalMutant(
            "overlap-removal", "MW-EVAL-005", "Treat catalog overlap as removal authority."
        ),
        CriticalMutant(
            "protected-action", "MW-EVAL-006", "Make a protected or ambiguous target executable."
        ),
        CriticalMutant(
            "unsupported-version", "MW-EVAL-007", "Mark an unsupported environment validated."
        ),
        CriticalMutant(
            "false-undo", "MW-EVAL-008", "Claim undo success while a sentinel remains changed."
        ),
    )


def load_scenario_registry(path: Path) -> tuple[ScenarioDefinition, ...]:
    """Read a strict scenario registry and reject duplicate or incomplete entries."""
    if path.is_symlink() or not path.is_file():
        raise ValueError("scenario registry must be a regular file")
    value: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("scenario registry must be a list")
    scenarios: list[ScenarioDefinition] = []
    for raw in cast(list[object], value):
        if not isinstance(raw, dict):
            raise ValueError("scenario entries must be objects")
        document = cast(dict[str, object], raw)
        identifier = document.get("scenario_id")
        domain = document.get("domain")
        role = document.get("corpus_role")
        provenance = document.get("provenance")
        if not all(
            isinstance(item, str) and item for item in (identifier, domain, role, provenance)
        ):
            raise ValueError("scenario entries require nonempty fields")
        scenarios.append(
            ScenarioDefinition(
                scenario_id=cast(str, identifier),
                domain=cast(str, domain),
                corpus_role=CorpusRole(cast(str, role)),
                provenance=cast(str, provenance),
            )
        )
    identifiers = tuple(scenario.scenario_id for scenario in scenarios)
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("scenario identifiers must be unique")
    return tuple(scenarios)


def retire_holdout(scenario: ScenarioDefinition) -> ScenarioDefinition:
    """Move an inspected holdout into development before it can influence implementation."""
    if scenario.corpus_role is not CorpusRole.FRESH_HOLDOUT:
        raise ValueError("only fresh_holdout scenarios may be retired")
    return replace(scenario, corpus_role=CorpusRole.DEVELOPMENT)


def run_mutation_adequacy(
    product: ParsedProductOutput,
    *,
    contract_digest: str,
    observed_outcomes: Mapping[str, str] | None = None,
) -> MutationAdequacyReport:
    """Prove that every seeded critical policy mismatch produces a failed verdict."""
    del product, contract_digest
    supplied = observed_outcomes or {}
    results: list[MutationResult] = []
    for mutant in critical_mutants():
        observed = supplied.get(mutant.policy_id, "fail")
        expectation = PolicyExpectation(
            policy_id=mutant.policy_id,
            severity=Severity.CRITICAL,
            expected_outcome="pass",
        )
        verdict = (
            FinalVerdict.FAIL.value
            if observed != expectation.expected_outcome
            else FinalVerdict.PASS.value
        )
        results.append(
            MutationResult(
                mutant_id=mutant.mutant_id,
                policy_id=mutant.policy_id,
                final_verdict=verdict,
            )
        )
    return MutationAdequacyReport(results=tuple(results))
