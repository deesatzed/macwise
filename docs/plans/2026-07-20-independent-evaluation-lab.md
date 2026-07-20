# Independent Evaluation Lab Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a separately packaged evaluator that independently measures MacWise factual
accuracy, calibration, safety, decision-value proxy, macOS-version confidence, and reversibility.

**Architecture:** `evaluator/` is an isolated Python project and command-line application. It
consumes immutable evidence capsules, MacWise structured outputs, and predeclared scenario
oracles; it may share serialized formats but may not import or call production MacWise logic.
Deterministic judges own facts and safety, while an optional AI/human protocol is non-authoritative.

**Tech Stack:** Python 3.12+, uv, Pydantic v2, Typer, pytest, Ruff, Pyright, JSON/TOML fixtures,
GitHub Actions macOS runners.

---

### Task 1: Create the isolated evaluator project and enforce independence

**Files:**
- Create: `evaluator/pyproject.toml`
- Create: `evaluator/src/macwise_eval/__init__.py`
- Create: `evaluator/src/macwise_eval/cli.py`
- Create: `evaluator/tests/test_independence.py`
- Modify: `.gitignore`

**Steps:**

1. Write a failing repository test that walks evaluator imports and rejects `macwise`,
   `src/macwise`, relative path insertion, subprocess calls to `macwise`, and imports outside the
   evaluator package.
2. Run `uv run --directory evaluator pytest tests/test_independence.py -q` and observe the
   missing-project failure.
3. Add the minimal standalone project, `macwise-eval` entry point, strict tool configuration, and
   ignored private artifact directory `evaluator/private/`.
4. Add a `macwise-eval --version` smoke and prove that importing `macwise_eval` does not import
   `macwise`.
5. Run the focused tests, Ruff, and Pyright.
6. Commit with `build(eval): create independent evaluator project`.

### Task 2: Define immutable capsules, receipts, oracles, and reports

**Files:**
- Create: `evaluator/src/macwise_eval/models.py`
- Create: `evaluator/src/macwise_eval/io.py`
- Create: `evaluator/tests/test_models.py`
- Create: `evaluator/fixtures/synthetic/minimal/manifest.json`
- Create: `evaluator/fixtures/synthetic/minimal/reference.json`
- Create: `evaluator/fixtures/synthetic/minimal/oracle.json`

**Steps:**

1. Write failing tests for strict, frozen models: `EnvironmentIdentity`, `Receipt`,
   `CapsuleManifest`, `ExpectedClaim`, `PolicyExpectation`, `ScenarioOracle`, `ClaimVerdict`,
   `AxisResult`, and `EvaluationReport`.
2. Require product version, build, Darwin version, architecture, provenance class, disclosure
   class, SHA-256 receipt digests, oracle version, and limitations.
3. Reject extra fields, path traversal, missing digests, mismatched identifiers, naive timestamps,
   and public designation for `live_private` capsules.
4. Implement canonical JSON serialization and digest verification without importing MacWise.
5. Add the minimal sanitized fixture and prove byte-stable round trips.
6. Commit with `feat(eval): define evidence capsule contract`.

### Task 3: Add privacy classification and disclosure gates

**Files:**
- Create: `evaluator/src/macwise_eval/privacy.py`
- Create: `evaluator/tests/test_privacy.py`
- Create: `evaluator/fixtures/privacy/hostile-private-values.json`
- Create: `docs/evaluation/privacy.md`

**Steps:**

1. Write failing tests for usernames, home paths, volume paths, hostnames, serial-shaped values,
   control characters, prompt-shaped text, secrets, and real inventory in public capsules.
2. Implement a conservative disclosure scanner that reports findings but never silently rewrites
   evidence.
3. Require an explicit reviewed-sanitized flag and zero scanner findings before a capsule may be
   copied outside `evaluator/private/`.
4. Document what stays local, what may be committed, and how a human reviews redaction.
5. Run focused tests and the existing repository privacy tests.
6. Commit with `feat(eval): gate capsule disclosure`.

### Task 4: Implement the frozen scenario oracle and safety policy engine

**Files:**
- Create: `evaluator/policies/v1/safety.toml`
- Create: `evaluator/src/macwise_eval/policy.py`
- Create: `evaluator/src/macwise_eval/oracle.py`
- Create: `evaluator/tests/test_policy.py`
- Create: `evaluator/scripts/freeze_contract.py`
- Create: `evaluator/contract.lock`

**Steps:**

1. Write one failing test for each initial hard invariant in the design document.
2. Implement closed policy identifiers, severity, applicability, expected abstention, acceptable
   actions, and forbidden actions.
3. Make unknown policy IDs and weakened criticality fail closed.
4. Generate a lock containing digests for policy, oracle schema, metric definitions, and canonical
   fixtures.
5. Add a verification mode that refuses silent contract drift and prints the changed digest path.
6. Commit with `feat(eval): freeze independent safety oracle`.

### Task 5: Extract typed claims from MacWise structured outputs

**Files:**
- Create: `evaluator/src/macwise_eval/product_output.py`
- Create: `evaluator/src/macwise_eval/claims.py`
- Create: `evaluator/tests/test_product_output.py`
- Create: `evaluator/fixtures/product_outputs/`
- Create: `scripts/generate_eval_product_outputs.py`
- Create: `tests/evaluation/test_product_output_driver.py`

**Steps:**

1. Add sanitized audit-schema-4, checkup, plan-schema-2, execution-schema-1, partial, malformed,
   and future-schema fixtures.
2. Write failing tests that convert output into typed fact, inference, uncertainty, priority,
   guidance, action, and undo claims.
3. Implement local strict adapters from serialized JSON only; do not import Pydantic models from
   MacWise.
4. Preserve source JSON pointers so every verdict can cite the exact product claim.
5. Refuse unsupported schemas as `inconclusive`, not pass or product failure.
6. Add a product-side driver outside `evaluator/` that generates serialized outputs from
   sanitized fixtures. The evaluator may read those files but may not import or execute the
   driver.
7. Commit with `feat(eval): normalize MacWise claims independently`.

### Task 6: Build deterministic comparison and multi-axis reporting

**Files:**
- Create: `evaluator/src/macwise_eval/evaluate.py`
- Create: `evaluator/src/macwise_eval/metrics.py`
- Create: `evaluator/src/macwise_eval/reporting.py`
- Create: `evaluator/tests/test_evaluate.py`
- Create: `evaluator/tests/test_metrics.py`

**Steps:**

1. Write failing tests for correct, incorrect, unsupported, missing, and unevaluable claim
   verdicts with explicit denominators.
2. Implement factual precision/recall, unsupported-claim counts, calibration transitions,
   top-three priority retrieval, review burden, correct abstention, policy gates, version status,
   and reversibility counts.
3. Implement `PASS`, `FAIL`, and `INCONCLUSIVE`; any critical violation must force `FAIL` and may
   not be averaged away.
4. Render deterministic JSON and concise Markdown with capsule IDs, contract digest, product
   version, numerators, denominators, and limitations.
5. Add CLI command `macwise-eval evaluate CAPSULE --product-output PATH --output-dir PATH`.
6. Commit with `feat(eval): evaluate claims with hard safety gates`.

### Task 7: Add metamorphic cases and evaluator mutation adequacy

**Files:**
- Create: `evaluator/src/macwise_eval/mutations.py`
- Create: `evaluator/tests/test_metamorphic.py`
- Create: `evaluator/tests/test_mutation_adequacy.py`
- Create: `evaluator/fixtures/scenarios/`

**Steps:**

1. Create at least twelve scenario families covering storage, backup, startup, dependencies,
   overlap, usage, unknown purpose, partial collection, hostile metadata, future macOS, protected
   targets, and undo.
2. Label every capsule `development`, `frozen_acceptance`, or `fresh_holdout`; fail if one capsule
   appears in incompatible roles or a previously inspected case is claimed as a holdout.
3. Add negative controls, isolated positive controls, and mixed ranking cases. Report every domain,
   provenance class, environment tuple, and corpus role separately.
4. For every controlled mutation, declare the only expected claim transitions before running the
   product.
5. Seed the eight critical output mutants listed in the design and assert the evaluator catches
   all of them with the expected policy IDs.
6. Fail the adequacy gate if any critical mutant survives.
7. Save a deterministic mutation-adequacy JSON report.
8. Commit with `test(eval): prove evaluator mutation adequacy`.

### Task 8: Build independent read-only reference capture

**Files:**
- Create: `evaluator/src/macwise_eval/system.py`
- Create: `evaluator/src/macwise_eval/reference/`
- Create: `evaluator/src/macwise_eval/capture.py`
- Create: `evaluator/tests/reference/`
- Create: `docs/evaluation/real-mac-protocol.md`

**Steps:**

1. Write fake-runner tests proving fixed executable paths, `shell=False`, bounded output, timeouts,
   no Homebrew update/analytics, explicit approved roots, and no filesystem writes outside the
   chosen private output directory.
2. Implement independent observations for mounted storage, approved-root applications, Homebrew
   inventory/dependents, startup configuration, and Time Machine facts using alternative sources
   where practical.
3. Label unavoidable shared-source observations as source-correlated.
4. Add `macwise-eval capture --private-output DIR` with an explicit preview of collected fields and
   no upload/network behavior.
5. Document exact commands for capturing MacWise output close in time and preventing time drift.
6. Commit with `feat(eval): capture independent private receipts`.

### Task 9: Test disposable planning, apply, verification, and undo

**Files:**
- Create: `evaluator/src/macwise_eval/action_lab.py`
- Create: `evaluator/tests/test_action_lab.py`
- Create: `evaluator/fixtures/actions/`
- Create: `tests/evaluation/test_action_lab_driver.py`
- Create: `scripts/run_action_lab.py`
- Create: `docs/evaluation/action-lab-protocol.md`

**Steps:**

1. Write failing tests around temporary fake application bundles, fake command runners, startup
   fixtures, protected sentinels, and seeded related data.
2. Record before-state identities and hashes, expected action scope, forbidden side effects, and
   exact restoration requirements.
3. Add a product-side test driver that runs MacWise planning/apply/undo through existing injected
   test boundaries and emits only serialized before/after receipts. Keep this driver outside the
   evaluator package; never mutate real installed software or services.
4. Have the evaluator judge those receipts without importing or launching MacWise. Require
   intended-change verification, zero unrelated sentinel changes, durable journal truth, and
   exact supported undo restoration.
5. Save an aggregate action-lab report with no private paths.
6. Commit with `test(eval): verify disposable action safety and undo`.

### Task 10: Add macOS-version replay and hosted real-run matrix

**Files:**
- Create: `evaluator/src/macwise_eval/versioning.py`
- Create: `evaluator/tests/test_versioning.py`
- Modify: `.github/workflows/ci.yml`
- Create: `docs/evaluation/version-matrix.md`

**Steps:**

1. Write failing tests proving that product version, build, Darwin version, architecture, and tool
   versions determine compatibility status.
2. Implement `validated_live`, `validated_replay`, `provisional`, `unsupported`, and `unknown`.
3. Ensure an unknown/future tuple lowers confidence and triggers conservative guidance tests.
4. Run fixture replay on Linux and seeded reference/product comparison on every available hosted
   macOS image already supported by CI.
5. Keep local macOS 27 evidence separate from hosted image claims.
6. Commit with `ci(eval): test versioned evaluator matrix`.

### Task 11: Run a private live-Mac evaluation and publish only sanitized aggregates

**Files:**
- Create: `docs/evaluation/current-private-mac-result.md`
- Modify: `PROGRESS.md`

**Steps:**

1. Build the MacWise wheel and evaluator in isolated environments.
2. Capture reference evidence and MacWise structured outputs close in time under an ignored
   private directory.
3. Designate the run as a fresh holdout before inspecting it. If its result drives a product or
   evaluator change, retire it to development and obtain a new holdout before claiming
   generalization.
4. Run the evaluator and inspect every critical or unsupported verdict manually.
5. Run the privacy scanner against the proposed aggregate report.
6. Save only environment tuple, counts, ratios, policy verdicts, limitations, and runtime in the
   public document.
7. State explicitly that one Mac validates only its exact environment, not all Macs.
8. Commit with `docs(eval): record private real-Mac aggregate evaluation`.

### Task 12: Prepare the blinded paid pilot without spending or uploading

**Files:**
- Create: `docs/evaluation/paid-pilot-protocol.md`
- Create: `docs/evaluation/pilot-score-sheet.json`
- Create: `docs/evaluation/pilot-consent-checklist.md`
- Create: `tests/repository/test_evaluation_docs.py`

**Steps:**

1. Define five to eight participant strata, randomized task order, acceptable and forbidden
   choices, delayed comprehension questions, confidence recording, and help-request counts.
2. Keep raw inventories local and define a deidentified return artifact.
3. State that recruitment, compensation, external uploads, and spending require separate explicit
   authorization.
4. Dry-run the protocol using synthetic capsules and confirm score-sheet determinism.
5. Do not claim that the human pilot happened.
6. Commit with `docs(eval): prepare blinded external pilot`.

### Task 13: Complete the frozen evaluator acceptance gate

**Files:**
- Create: `docs/evaluation/acceptance.md`
- Modify: `DECISIONS.md`
- Modify: `PROGRESS.md`
- Modify: `TASK_QUEUE.md`

**Steps:**

1. Run `uv lock --directory evaluator --check`.
2. Run `uv run --directory evaluator pytest tests -q`.
3. Run `uv run --directory evaluator ruff format --check .`,
   `uv run --directory evaluator ruff check .`, and `uv run --directory evaluator pyright`.
4. Run `uv run pytest`, root Ruff/Pyright, `uv build`, privacy contracts, frozen-contract
   verification, mutation adequacy, scenario replay, private live-Mac evaluation, and
   `git diff --check`.
5. Verify the evaluator never imports or executes MacWise logic and that no private capsule is
   tracked.
6. Record exact results and any unsupported environment as limitations.
7. Mark MW-604 done only when every `GOAL_EVAL.md` completion condition has current evidence.
8. Commit with `docs(eval): accept independent evaluation lab`.
