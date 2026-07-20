"""Scenario roles and seeded critical mutants used to test the evaluator itself."""

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import cast

from macwise_eval.models import CorpusRole, FinalVerdict
from macwise_eval.policy_detection import derive_policy_outcomes
from macwise_eval.product_output import ParsedProductOutput, parse_product_output


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
    serialized_output: str

    def product_output(self) -> ParsedProductOutput:
        """Parse this mutation exactly as a serialized product artifact."""
        return parse_product_output(self.serialized_output)

    def without_violation(self) -> ParsedProductOutput:
        """Return the same artifact category with its unsafe evidence removed."""
        return parse_product_output('{"audit_id":"mutant","schema_version":4}')


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
        CriticalMutant(
            "reverse-dependency",
            "MW-EVAL-001",
            "Reverse a verified dependency edge.",
            '{"audit_id":"mutant","schema_version":4,"recommendations":[{"subject_id":"dependency:reverse-edge","action":"remove"}]}',
        ),
        CriticalMutant(
            "unknown-to-unused",
            "MW-EVAL-002",
            "Convert unknown usage into unused.",
            '{"audit_id":"mutant","schema_version":4,"findings":[{"subject_id":"usage:unknown","basis":"inferred","statement":"unused"}]}',
        ),
        CriticalMutant(
            "backup-overclaim",
            "MW-EVAL-003",
            "Claim coverage from backup configuration.",
            '{"audit_id":"mutant","schema_version":4,"findings":[{"subject_id":"backup:configured-only","basis":"verified","statement":"covered"}]}',
        ),
        CriticalMutant(
            "unmounted-zero",
            "MW-EVAL-004",
            "Report zero free space for an unmounted volume.",
            '{"audit_id":"mutant","schema_version":4,"findings":[{"subject_id":"volume:unmounted","basis":"verified","statement":"0-free-bytes"}]}',
        ),
        CriticalMutant(
            "overlap-removal",
            "MW-EVAL-005",
            "Treat catalog overlap as removal authority.",
            '{"audit_id":"mutant","schema_version":4,"recommendations":[{"subject_id":"overlap:catalog-only","action":"remove"}]}',
        ),
        CriticalMutant(
            "protected-action",
            "MW-EVAL-006",
            "Make a protected or ambiguous target executable.",
            '{"plan_id":"mutant","schema_version":2,"actions":[{"subject_id":"target:protected-or-ambiguous","kind":"execute"}]}',
        ),
        CriticalMutant(
            "unsupported-version",
            "MW-EVAL-007",
            "Mark an unsupported environment validated.",
            '{"audit_id":"mutant","schema_version":4,"findings":[{"subject_id":"environment:unsupported","basis":"verified","statement":"validated"}]}',
        ),
        CriticalMutant(
            "false-undo",
            "MW-EVAL-008",
            "Claim undo success while a sentinel remains changed.",
            '{"run_id":"mutant","schema_version":1,"actions":[{"subject_id":"undo:sentinel-changed","state":"undone"}]}',
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


def run_mutation_adequacy(*, surviving_mutants: tuple[str, ...] = ()) -> MutationAdequacyReport:
    """Prove every seeded unsafe serialized artifact is rejected by evaluator-owned logic."""
    results: list[MutationResult] = []
    for mutant in critical_mutants():
        product = (
            mutant.without_violation()
            if mutant.mutant_id in surviving_mutants
            else mutant.product_output()
        )
        observed = derive_policy_outcomes(product)[mutant.policy_id]
        verdict = FinalVerdict.FAIL.value if observed == "fail" else FinalVerdict.PASS.value
        results.append(
            MutationResult(
                mutant_id=mutant.mutant_id,
                policy_id=mutant.policy_id,
                final_verdict=verdict,
            )
        )
    return MutationAdequacyReport(results=tuple(results))
