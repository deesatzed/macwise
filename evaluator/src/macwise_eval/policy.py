"""Versioned safety policy that remains independent of product recommendation logic."""

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from macwise_eval.models import PolicyExpectation, Severity

PolicyOutcome = Literal["pass", "fail", "inconclusive"]


@dataclass(frozen=True)
class SafetyRule:
    """One closed safety invariant with its non-negotiable severity."""

    policy_id: str
    severity: Severity
    rule: str


@dataclass(frozen=True)
class PolicyViolation:
    """A traceable difference between expected and independently observed policy outcome."""

    policy_id: str
    severity: Severity
    expected_outcome: PolicyOutcome
    observed_outcome: PolicyOutcome


def load_policy(path: Path) -> dict[str, SafetyRule]:
    """Read a regular TOML policy file and reject malformed or duplicate rules."""
    if path.is_symlink() or not path.is_file():
        raise ValueError("policy must be a regular file")
    try:
        document = cast(dict[str, object], tomllib.loads(path.read_text(encoding="utf-8")))
    except tomllib.TOMLDecodeError as error:
        raise ValueError("policy is not valid TOML") from error
    raw_rules = document.get("policy")
    if not isinstance(raw_rules, list):
        raise ValueError("policy must define a policy list")

    rules: dict[str, SafetyRule] = {}
    for raw_rule in cast(list[object], raw_rules):
        if not isinstance(raw_rule, dict):
            raise ValueError("policy entries must be tables")
        rule_document = cast(dict[str, object], raw_rule)
        identifier = rule_document.get("id")
        raw_severity = rule_document.get("severity")
        rule = rule_document.get("rule")
        if not isinstance(identifier, str) or not identifier:
            raise ValueError("policy identifier is required")
        if not isinstance(raw_severity, str):
            raise ValueError(f"policy {identifier} requires a severity")
        if not isinstance(rule, str) or not rule:
            raise ValueError(f"policy {identifier} requires a rule")
        if identifier in rules:
            raise ValueError(f"duplicate policy identifier: {identifier}")
        try:
            severity = Severity(raw_severity)
        except ValueError as error:
            raise ValueError(f"policy {identifier} has an unknown severity") from error
        rules[identifier] = SafetyRule(policy_id=identifier, severity=severity, rule=rule)
    return rules


def evaluate_policy_expectations(
    policy: Mapping[str, SafetyRule],
    expectations: tuple[PolicyExpectation, ...],
    *,
    observed_outcomes: Mapping[str, str],
) -> tuple[PolicyViolation, ...]:
    """Compare predeclared policy outcomes, failing closed on unknown or weakened rules."""
    violations: list[PolicyViolation] = []
    allowed = {"pass", "fail", "inconclusive"}
    for expectation in expectations:
        rule = policy.get(expectation.policy_id)
        if rule is None:
            raise ValueError(f"unknown policy: {expectation.policy_id}")
        if expectation.severity is not rule.severity:
            raise ValueError(f"policy severity does not match frozen rule: {expectation.policy_id}")
        observed = observed_outcomes.get(expectation.policy_id)
        if observed not in allowed:
            raise ValueError(f"policy outcome is missing or invalid: {expectation.policy_id}")
        expected = expectation.expected_outcome
        typed_observed = cast(PolicyOutcome, observed)
        if typed_observed != expected:
            violations.append(
                PolicyViolation(
                    policy_id=expectation.policy_id,
                    severity=rule.severity,
                    expected_outcome=expected,
                    observed_outcome=typed_observed,
                )
            )
    return tuple(violations)
