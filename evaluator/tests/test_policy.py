"""Frozen policy is the independent safety authority for evaluation scenarios."""

import subprocess
import sys
from pathlib import Path

import pytest

from macwise_eval.models import PolicyExpectation, Severity
from macwise_eval.oracle import contract_digest
from macwise_eval.policy import PolicyViolation, evaluate_policy_expectations, load_policy

POLICY_PATH = Path(__file__).parents[1] / "policies" / "v1" / "safety.toml"
FREEZE_SCRIPT = Path(__file__).parents[1] / "scripts" / "freeze_contract.py"


def test_policy_contains_closed_critical_safety_invariants() -> None:
    policy = load_policy(POLICY_PATH)

    assert set(policy) == {
        "MW-EVAL-001",
        "MW-EVAL-002",
        "MW-EVAL-003",
        "MW-EVAL-004",
        "MW-EVAL-005",
        "MW-EVAL-006",
        "MW-EVAL-007",
        "MW-EVAL-008",
    }
    assert policy["MW-EVAL-001"].severity is Severity.CRITICAL
    assert "reverse dependency" in policy["MW-EVAL-001"].rule.lower()


def test_unknown_policy_or_weakened_criticality_fails_closed() -> None:
    policy = load_policy(POLICY_PATH)

    with pytest.raises(ValueError, match="unknown policy"):
        evaluate_policy_expectations(
            policy,
            (
                PolicyExpectation(
                    policy_id="MW-EVAL-999",
                    severity=Severity.CRITICAL,
                    expected_outcome="pass",
                ),
            ),
            observed_outcomes={},
        )
    with pytest.raises(ValueError, match="severity"):
        evaluate_policy_expectations(
            policy,
            (
                PolicyExpectation(
                    policy_id="MW-EVAL-001",
                    severity=Severity.LOW,
                    expected_outcome="pass",
                ),
            ),
            observed_outcomes={"MW-EVAL-001": "pass"},
        )


def test_policy_outcome_mismatch_is_traceable_and_critical() -> None:
    policy = load_policy(POLICY_PATH)

    violations = evaluate_policy_expectations(
        policy,
        (
            PolicyExpectation(
                policy_id="MW-EVAL-001",
                severity=Severity.CRITICAL,
                expected_outcome="pass",
            ),
        ),
        observed_outcomes={"MW-EVAL-001": "fail"},
    )

    assert violations == (
        PolicyViolation(
            policy_id="MW-EVAL-001",
            severity=Severity.CRITICAL,
            expected_outcome="pass",
            observed_outcome="fail",
        ),
    )


def test_contract_digest_changes_when_a_frozen_input_changes(tmp_path: Path) -> None:
    policy_copy = tmp_path / "safety.toml"
    policy_copy.write_text(POLICY_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    original = contract_digest((policy_copy,))
    policy_copy.write_text(
        policy_copy.read_text(encoding="utf-8") + "\n# reviewed change\n", encoding="utf-8"
    )

    assert contract_digest((policy_copy,)) != original


def test_freeze_script_refuses_silent_contract_drift(tmp_path: Path) -> None:
    policy_copy = tmp_path / "safety.toml"
    lock_path = tmp_path / "contract.lock"
    policy_copy.write_text(POLICY_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    write = subprocess.run(
        (sys.executable, str(FREEZE_SCRIPT), "--write", str(lock_path), str(policy_copy)),
        check=False,
        capture_output=True,
        text=True,
    )
    check = subprocess.run(
        (sys.executable, str(FREEZE_SCRIPT), "--check", str(lock_path), str(policy_copy)),
        check=False,
        capture_output=True,
        text=True,
    )
    policy_copy.write_text(policy_copy.read_text(encoding="utf-8") + "# drift\n", encoding="utf-8")
    drift = subprocess.run(
        (sys.executable, str(FREEZE_SCRIPT), "--check", str(lock_path), str(policy_copy)),
        check=False,
        capture_output=True,
        text=True,
    )

    assert write.returncode == 0
    assert check.returncode == 0
    assert drift.returncode == 2
    assert "contract digest differs" in drift.stderr
