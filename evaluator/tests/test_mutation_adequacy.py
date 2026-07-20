"""The evaluator must reject every seeded critical safety mutant."""

from pathlib import Path

from macwise_eval.mutations import critical_mutants, run_mutation_adequacy
from macwise_eval.product_output import parse_product_output

FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_all_eight_critical_mutants_are_caught_by_the_hard_policy_gate() -> None:
    baseline = parse_product_output(
        (FIXTURES / "product_outputs" / "audit-v4.json").read_text(encoding="utf-8")
    )

    report = run_mutation_adequacy(baseline, contract_digest="e" * 64)

    assert len(critical_mutants()) == 8
    assert report.total == 8
    assert report.caught == 8
    assert report.survived_mutants == ()
    assert all(result.final_verdict == "fail" for result in report.results)


def test_mutation_adequacy_reports_a_surviving_mutant_explicitly() -> None:
    baseline = parse_product_output(
        (FIXTURES / "product_outputs" / "audit-v4.json").read_text(encoding="utf-8")
    )
    first = critical_mutants()[0]

    report = run_mutation_adequacy(
        baseline,
        contract_digest="e" * 64,
        observed_outcomes={first.policy_id: "pass"},
    )

    assert report.caught == 7
    assert report.survived_mutants == (first.mutant_id,)
