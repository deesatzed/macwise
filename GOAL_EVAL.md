# GOAL_EVAL.md — Build the Independent MacWise Evaluation Lab

## OUTCOME

Build a separately packaged, read-only `macwise-eval` side application that can independently
determine whether MacWise's structured findings and cleanup guidance are factually supported,
safely calibrated, useful for a bounded decision, compatible with the tested macOS environment,
and reversible where MacWise claims reversibility.

The evaluator must use independently captured evidence and predeclared expectations. It must not
import MacWise implementation code, copy MacWise recommendation rules, call an AI model as a truth
source, or let a high average hide one critical safety failure.

This is a multi-phase evaluation-infrastructure build. It supplements `GOAL.md`; it does not
change the public MacWise product contract or authorize publication, real cleanup, participant
recruitment, uploads, or spending.

## PROOF OF DONE

### A. Independent side application

1. `evaluator/` is an independently packaged Python 3.12+ project with a `macwise-eval` CLI, its
   own dependency lock, tests, models, policies, fixtures, and documentation.
2. Automated boundary tests prove evaluator code does not import production `macwise` modules,
   insert the product source path, invoke the `macwise` executable, or reuse product analysis,
   scoring, recommendation, planning, revalidation, execution, or reporting functions.
3. Only serialized interchange data may cross the boundary. The evaluator owns its parsers and
   rejects unknown schemas as inconclusive rather than silently accepting them.
4. `macwise-eval --version`, `capture --help`, `evaluate --help`, and the documented synthetic
   walkthrough run from a clean evaluator environment.

### B. Reality-grounded evidence capsules

1. Implement strict immutable schemas for environment identity, evidence receipts, manifests,
   scenario oracles, claim verdicts, metric axes, and final verdicts.
2. Every capsule records macOS product version, build, Darwin version, architecture, tool
   versions, provenance class, disclosure class, timestamps, receipt digests, oracle version,
   limitations, MacWise version, and audit schema.
3. Distinguish `synthetic`, `derived_sanitized`, `live_private`, and `controlled_mutation` evidence.
   Reports must never present one class as another.
4. Implement content-digest validation, deterministic serialization, path-containment checks,
   disclosure scanning, and explicit human-reviewed sanitization before any real-derived capsule
   may become public.
5. Store raw real-Mac evidence only under an ignored private directory. Commit no usernames,
   hostnames, home or volume paths, serials, private inventory, secrets, or personal data.
6. Label every capsule `development`, `frozen_acceptance`, or `fresh_holdout`. Once a holdout result
   is inspected and used to change MacWise or the evaluator, retire it into development and
   require a new holdout for the next generalization claim.

### C. Independent observations and oracle

1. Capture reference observations through bounded, fixed, shell-free read-only adapters using
   alternative system sources where practical.
2. Label a comparison `source_correlated` when MacWise and the reference must use the same
   authoritative source. Do not call it fully independent.
3. Every scenario oracle is created independently of the product output and declares eligible
   facts, acceptable findings/actions, forbidden findings/actions, expected uncertainty,
   criticality, and intended metamorphic transitions.
4. Version the safety policy separately from the product. Freeze policy, oracle schema, metric
   definitions, and canonical fixture digests after initial acceptance.
5. Require a documented decision and before/after comparison for evaluator-contract changes;
   never loosen a failing gate silently.

### D. Objective evaluation dimensions

Produce separate results for:

1. **Factual accuracy:** correct, incorrect, unsupported, missing, and unevaluable claims;
   precision and recall include explicit numerators and denominators.
2. **Calibration:** confidence and guidance become more conservative when evidence is missing,
   stale, conflicting, source-correlated, or outside a validated environment.
3. **Safety:** hard policy gates for dependencies, non-use, backup claims, mounted storage,
   overlap, ambiguity, protected targets, version support, and reversibility.
4. **Decision-value proxy:** top-three retrieval of verified priorities, bounded review burden,
   explanation completeness, safe next-step quality, and correct abstention.
5. **Version confidence:** one of `validated_live`, `validated_replay`, `provisional`,
   `unsupported`, or `unknown` for the exact environment tuple.
6. **Reversibility:** intended change, unrelated sentinel integrity, journal truth, and observed
   restoration for supported disposable actions.

Do not publish a single master score. The result must end with `PASS`, `FAIL`, or `INCONCLUSIVE`,
with every critical failure shown before aggregate metrics.

### E. Safety invariants and thresholds

The initial accepted corpus must demonstrate:

1. zero critical safety-policy violations;
2. zero confident destructive guidance based on unknown or missing evidence;
3. 100% refusal of protected and ambiguous action targets;
4. 100% restoration across supported seeded undo scenarios;
5. at least 98% precision and 95% recall across eligible deterministic facts;
6. at least 90% top-three retrieval of oracle-designated priority issues;
7. 100% correct abstention in critical insufficient-evidence scenarios; and
8. explicit denominators, evidence class, environment tuple, and limitations for every reported
   ratio.

A single critical violation forces `FAIL`; averaging is forbidden. `INCONCLUSIVE` is required when
reference truth is insufficient or the schema/environment cannot be evaluated safely.

### F. Realism and version variance

1. Include at least twelve scenario families: storage, backup, startup, dependencies, overlap,
   usage, unknown purpose, partial collection, hostile metadata, future/unknown macOS, protected
   targets, and undo.
2. Add controlled one-variable mutations and test that only declared conclusions change.
3. Replay fixed capsules across new MacWise versions to detect methodology drift.
4. Run seeded read-only comparisons on every available hosted macOS image already in the project
   CI matrix. Record exact product/build/Darwin/architecture tuples; never substitute “latest.”
5. Run one private live comparison on the current Mac, close in time, and retain only a sanitized
   aggregate report in the repository.
6. An unfamiliar future tuple must be labeled provisional, unsupported, or unknown and must not
   inherit validated status from another macOS version.
7. Include negative controls with no actionable issue, isolated positive controls with one
   verified issue, and mixed cases for ranking. Report metrics separately by domain, environment,
   provenance class, and corpus role; do not pool groups to hide a weak result.
8. State explicitly that one private live Mac validates only its exact environment and does not
   prove population-wide accuracy. Include sample counts and uncertainty intervals when the corpus
   supports them.

### G. Test the evaluator itself

Seed at least these evaluator-adequacy mutants:

1. reverse a dependency relationship;
2. change unknown usage to unused;
3. alter backup age or coverage meaning;
4. replace mounted free space with zero;
5. change complementary tools to duplicates;
6. mark an unsupported OS as validated;
7. omit a required safety limitation; and
8. claim undo succeeded while a protected sentinel remains changed.

The frozen evaluator must catch every critical mutant and identify the expected policy. A passing
unit suite without mutation-adequacy proof is not completion.

### H. Disposable action lab

1. Exercise planning, apply, verification, recovery, and undo only with temporary application
   bundles, fake command adapters, synthetic startup fixtures, and explicit sentinels.
2. Capture before and after identities, hashes, state, journal revisions, intended scope, and
   forbidden side effects.
3. Never uninstall, disable, move, launch, or modify real user software, Homebrew packages,
   services, startup items, backups, or volumes during evaluator development or acceptance.
4. Refuse to call an operation reversible unless observed undo restores all declared invariants.

### I. Human-value pilot readiness

Create a complete, dry-run protocol for a later blinded five-to-eight-person pilot. It must define
participant strata, randomized order, fixed tasks, acceptable and forbidden choices, delayed
comprehension questions, confidence calibration, help requests, completion time, privacy review,
and aggregate reporting.

An optional AI reviewer may score clarity using a fixed anonymized rubric, but it may not establish
facts, safety, ground truth, or release status. Do not recruit, compensate, upload data, spend
money, or claim the pilot ran without separate explicit user authorization.

### J. Required verification

Run and record fresh evidence for:

```bash
uv lock --project evaluator --check
uv run --project evaluator pytest evaluator/tests -q
uv run --project evaluator ruff format --check evaluator
uv run --project evaluator ruff check evaluator
uv run --project evaluator pyright evaluator/src evaluator/tests
uv run pytest
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv build
git diff --check
```

Also run and save:

1. frozen-contract verification;
2. mutation-adequacy report;
3. all canonical scenario replays;
4. disposable action-lab report;
5. clean evaluator installation and synthetic walkthrough;
6. hosted macOS matrix evidence;
7. private current-Mac aggregate evaluation;
8. disclosure/privacy scan of every tracked evaluator artifact; and
9. an independence audit proving no forbidden imports, calls, paths, or tracked private capsules.

## SCOPE

### May create or modify

- `evaluator/**`
- `.github/workflows/ci.yml` for bounded evaluator jobs
- `.gitignore` for private evaluator artifacts
- `docs/evaluation/**`
- `tests/evaluation/**` for product-side serialized fixture/action drivers
- `tests/repository/**` for repository/privacy contracts
- `scripts/generate_eval_product_outputs.py` and `scripts/run_action_lab.py`
- `GOAL_EVAL.md`
- `STANDARDS.md`, `IMPLEMENT.md`, `DECISIONS.md`, `PROGRESS.md`, and `TASK_QUEUE.md` only for
  accepted evaluation architecture, progress, and evidence
- MacWise product tests or structured-export adapters only when an evaluator-discovered defect
  requires a minimal compatible fix

### Read and preserve

- `GOAL.md` and `GOAL_SIMPLE_UX.md`
- audit schema 4, plan schema 2, and execution schema 1 compatibility
- verified/inferred/user-confirmed/unknown evidence semantics
- immutable plans, exact approval, fresh revalidation, recovery journal, and undo safety
- existing CI, release-candidate packaging, public CLI behavior, and privacy contracts

### Out of scope

- creating or publishing a remote evaluator repository
- publishing `macwise-eval` to PyPI or Homebrew
- changing the MacWise public command hierarchy for evaluator convenience
- production deployment or a release tag
- live web enrichment or a shared Hugging Face knowledge database
- using an LLM as factual ground truth or cleanup authority
- telemetry, accounts, automatic uploads, or central inventory storage
- recruiting or compensating pilot participants without separate approval
- destructive testing against real installed software

## CONSTRAINTS

1. The evaluator must fail closed on unknown schemas, policies, or critical evidence conflicts.
2. It must not import, execute, monkeypatch, or copy MacWise decision logic. Serialized contracts
   are the only product boundary.
3. Fixtures and policies must be written independently of the observed output they judge.
4. Acceptance thresholds and corpus roles must be recorded before the run. Do not tune against a
   holdout and continue calling it a holdout.
5. Every conclusion must cite receipt paths or product JSON pointers and policy/oracle IDs.
6. Unknown and unevaluable evidence must remain visible and outside scored denominators unless the
   metric explicitly measures correct abstention.
7. Critical safety failures cannot be averaged, waived by a total score, or relabeled as
   limitations.
8. AI judgments are optional and non-authoritative.
9. Reference capture is read-only, shell-free, bounded, opt-in, and local by default.
10. Do not add network access, uploads, analytics, credentials, or remote dependencies.
11. Do not weaken existing tests or evaluator policies to make a run pass.
12. Keep evaluation reports deterministic, schema-versioned, content-addressed, and reviewable.
13. Do not expose private inventories in test output, logs, documentation, commits, or CI.
14. If MacWise and the evaluator rely on the same source, disclose correlation.
15. Preserve exact macOS environment tuples; never infer compatibility from marketing names.

## ITERATION

1. Read all repository truth files and the accepted design and implementation plan before editing.
2. Establish the evaluator import/process boundary first and keep it green throughout the build.
3. Work test-first in small vertical slices: models, privacy, policy, product adapters, comparison,
   metrics, mutation adequacy, reference capture, action lab, version matrix, and real-Mac proof.
4. Create expected scenarios and policy outcomes before generating or inspecting corresponding
   MacWise results.
5. After each slice, run the focused evaluator tests, independence audit, and nearest product
   regression tests.
6. Treat evaluator defects and product defects separately. Record which side changed and why.
7. When a metric fails, investigate the individual claim ledger before changing thresholds,
   policies, weights, fixtures, or product behavior.
8. Freeze the evaluator contract before final product comparison. Any later contract change must
   regenerate its digest and show its result impact.
9. Use only private ignored paths for real evidence. Run disclosure scanning before copying any
   aggregate artifact into tracked documentation.
10. Update `PROGRESS.md`, `TASK_QUEUE.md`, and `DECISIONS.md` only from observed evidence.

## STOP

Pause and provide an evidence-backed blocker report only if:

1. required work would weaken a MacWise or evaluator safety/privacy invariant;
2. a second remote repository, publication, deployment, account, credential, upload, participant
   recruitment, compensation, or spending becomes necessary;
3. private data cannot be kept local or safely reduced to reviewed aggregate evidence;
4. a real installed item would need to be mutated;
5. required verification cannot run in the available environment;
6. the same failure remains after three distinct documented mitigation attempts; or
7. a product or methodology decision would materially expand this goal.

At every apparent block, first ask: **Can the human resolve this very easily?** If yes, provide one
small exact action and wait. If no, exhaust safe local alternatives before stopping.

## COMPLETE

Mark this goal complete only when:

1. every proof item A-J has current evidence;
2. every required command exits successfully;
3. all critical evaluator mutants are caught;
4. all hard safety thresholds pass;
5. a clean evaluator environment completes the synthetic walkthrough;
6. hosted macOS and private current-Mac results state exact supported and unsupported tuples;
7. the action lab proves supported undo without touching real installed software;
8. every tracked evaluator artifact passes privacy/disclosure review;
9. the acceptance report lists changed files, exact commands/results, contract digest, capsule
   classes, metric denominators, limitations, and deferred human pilot; and
10. no publication, upload, recruitment, spending, or destructive real-Mac action occurred.

Implementation alone is not completion. The frozen independent evaluator, mutation adequacy,
real-version evidence, and privacy-reviewed receipts arbitrate the claim.
