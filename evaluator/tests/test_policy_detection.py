"""Safety outcomes must be derived from serialized product claims, never caller flags."""

from macwise_eval.mutations import critical_mutants
from macwise_eval.policy_detection import derive_policy_outcomes


def test_each_seeded_mutant_is_detected_from_its_parsed_product_claim() -> None:
    for mutant in critical_mutants():
        outcomes = derive_policy_outcomes(mutant.product_output())
        assert outcomes[mutant.policy_id] == "fail"


def test_absent_unsafe_claims_default_to_passing_each_policy() -> None:
    outcomes = derive_policy_outcomes(critical_mutants()[0].without_violation())

    assert outcomes["MW-EVAL-001"] == "pass"
