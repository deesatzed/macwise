"""The evaluator must reject every seeded critical safety mutant."""

from macwise_eval.mutations import critical_mutants, run_mutation_adequacy


def test_all_eight_critical_mutants_are_caught_by_the_hard_policy_gate() -> None:
    report = run_mutation_adequacy()

    assert len(critical_mutants()) == 8
    assert report.total == 8
    assert report.caught == 8
    assert report.survived_mutants == ()
    assert all(result.final_verdict == "fail" for result in report.results)


def test_mutation_adequacy_reports_a_surviving_mutant_explicitly() -> None:
    first = critical_mutants()[0]

    report = run_mutation_adequacy(surviving_mutants=(first.mutant_id,))

    assert report.caught == 7
    assert report.survived_mutants == (first.mutant_id,)
