# Independent Evaluation Lab Design

## Decision

Build a separately packaged `macwise-eval` side application under `evaluator/`. It will live in
the MacWise repository initially for reproducible development, but it may not import production
`macwise` modules, reuse recommendation logic, or treat MacWise output as truth. Automated tests
will enforce that boundary.

The evaluator will compare three independently versioned inputs:

1. an evidence capsule containing reference observations and provenance;
2. MacWise's structured audit, checkup, plan, and optional execution result; and
3. a scenario oracle containing expectations and safety policy written before the run.

It will issue a multi-axis evaluation and a hard-gated release verdict. It will not compress
factual accuracy, safety, value, version support, and reversibility into one flattering score.

## Why this is the optimal first architecture

Three approaches were considered.

### Put more assertions inside MacWise

This is the least expensive option, but it is not independent. Shared parsing, categories, and
assumptions can make product code and tests agree while both are wrong.

### Start with a separate remote repository and independent maintainers

This provides the strongest governance independence, but it adds repository, release, schema,
and contributor coordination before the methodology is stable. It also creates an avoidable
account/publication block during the first build.

### Use an isolated subproject with enforced independence, then extract if needed

This is the selected approach. Separate packaging, a separate lock, no imports from MacWise,
frozen evaluator contracts, predeclared oracles, and mutation-adequacy tests provide technical
independence now. Moving the subtree to a separately governed repository remains possible after
the interfaces and evidence corpus stabilize.

## What the evaluator can and cannot prove

The evaluator can objectively test whether:

- structured claims agree with independent observations;
- important supported facts were omitted;
- confidence matches evidence strength;
- the safest acceptable decision set includes MacWise's guidance;
- forbidden or destructive guidance appears;
- the most important planted or verified issues appear near the top;
- unsupported macOS versions trigger conservative behavior;
- a supported reversible action changes only its intended target and can be undone.

It cannot prove that every user personally values the same outcome. Personalized usefulness
remains a human outcome. The lab therefore measures an objective **decision-value proxy**:
important-issue retrieval, review burden, explanation completeness, correct abstention, and safe
next-step quality. A later blinded user pilot measures comprehension and personal value separately.

## Separation of powers

```text
Independent reference capture ----> evidence capsule ----┐
                                                         |
MacWise run ------------------------> product outputs -----+--> macwise-eval
                                                         |
Predeclared scenario author --------> oracle + policy -----┘
                                                               |
                                                               v
                facts | calibration | safety | value | version | reversibility
                                                               |
                                                    PASS / FAIL / INCONCLUSIVE
```

No single input is sufficient:

- A MacWise report without reference evidence cannot prove factual correctness.
- Reference evidence without an oracle cannot establish the expected decision.
- A policy without real observations can pass unrealistic simulations.
- An AI reviewer cannot replace deterministic facts or safety invariants.

## Evidence capsules

An evaluation capsule is immutable and content-addressed. Its manifest records:

- capsule schema and identifier;
- provenance class;
- capture time and monotonic run identifier;
- macOS product version, build, Darwin version, and architecture;
- relevant tool versions;
- reference-observation receipt digests;
- the MacWise version and audit schema under test;
- sanitization status and disclosure class;
- scenario-oracle version;
- limitations and unavailable evidence.

Four provenance classes prevent simulated evidence from masquerading as real evidence:

1. `synthetic`: entirely authored fixtures;
2. `derived_sanitized`: a deidentified derivative of a real Mac;
3. `live_private`: evaluated locally and never committed;
4. `controlled_mutation`: one declared change applied to another capsule.

Public capsules must be synthetic or explicitly reviewed sanitized derivatives. Raw private
receipts stay in an ignored local directory. Sanitized aggregate results may enter documentation,
but application names, usernames, paths, serials, and personal inventory may not.

Capsules also have one evaluation role:

- `development`: visible cases used to build and debug either system;
- `frozen_acceptance`: stable regression cases whose contract cannot drift silently;
- `fresh_holdout`: previously unused real or generated cases used to test generalization.

Once a holdout result is inspected and used to change MacWise or the evaluator, that capsule is
retired into development. A later generalization claim requires a new holdout. Results are
reported by domain, environment, provenance, and role; they are not pooled to hide a weak group.

## Independent reference observations

Reference capture should use different mechanisms where practical:

- mounted capacity: `statvfs` or `df`, cross-checked against the mounted path;
- application bundles: explicit approved-root traversal and direct plist parsing;
- Homebrew: installed package and reverse-dependency queries independent of MacWise's derived
  classifications;
- startup: launch configuration and service-state receipts separated from plist presence;
- backups: exact destination and latest-backup receipts without inferring file recoverability;
- action verification: before/after filesystem identities, hashes, state, and sentinel checks.

When the operating system exposes only one authoritative source, the evaluator may use it, but it
must retain the raw receipt digest and mark the check as source-correlated rather than independent.
Source-correlated checks cannot be advertised as fully independent confirmation.

## Scenario oracle and frozen policy

Every scenario declares before execution:

- eligible facts that should be present;
- acceptable findings or actions;
- forbidden findings or actions;
- required uncertainty or abstention;
- criticality for each violation;
- expected changes after one controlled mutation;
- evidence that is intentionally unavailable.

Safety policy is versioned separately from MacWise. Initial hard invariants include:

- never recommend removal when verified reverse dependencies exist;
- never convert missing usage evidence into non-use;
- never claim backup coverage from configuration, destination, or non-exclusion alone;
- never describe an unmounted volume as having measured zero free space;
- never treat catalog overlap alone as removal authority;
- never permit ambiguous or protected targets to become executable actions;
- never claim an unsupported macOS environment is validated;
- never call an action reversible unless an observed undo restores the declared invariants.

After initial acceptance, policy, oracle, and metric definitions receive a recorded digest.
MacWise changes may not silently edit that frozen contract to obtain a passing result. Evaluator
contract changes require their own rationale, review, and before/after result comparison.

## Evaluation dimensions

### Factual accuracy

Every eligible claim receives `correct`, `incorrect`, `unsupported`, `missing`, or `unevaluable`.
The report includes precision, recall, unsupported-claim rate, and explicit denominators. An
unknown or unavailable reference is not scored as a product failure or a success.

### Calibration

Confidence must fall when evidence is removed, becomes stale, conflicts, or comes from an
unsupported version. Metamorphic tests verify monotonic changes rather than relying on subjective
confidence labels.

### Safety

Safety uses hard gates, not an average. One critical violation blocks the scenario and the release
verdict even when every low-risk fact is correct.

### Decision-value proxy

The evaluator measures whether verified high-priority issues appear in the bounded first results,
whether irrelevant findings create review burden, whether each result supplies evidence and a
safe next step, and whether the product abstains when the oracle says evidence is insufficient.

### Version confidence

Compatibility is reported per tuple of macOS product version, build, Darwin version,
architecture, and relevant tool versions. Status is one of:

- `validated_live`;
- `validated_replay`;
- `provisional`;
- `unsupported`;
- `unknown`.

A moving marketing name such as “latest macOS” is never sufficient evidence.

### Reversibility

Only disposable, explicitly seeded targets are mutated. Verification checks intended change,
unrelated sentinels, journal state, and exact undo. Real personal software is never part of
automated action testing.

## No misleading master score

The evaluator reports a dashboard rather than one weighted total:

```text
Factual accuracy        98.7% precision / 96.2% recall
Unsupported claims      0 critical / 2 low-risk
Safety gates            PASS
Decision-value proxy    11/12 priority scenarios passed
Version confidence      validated_live on listed environments only
Reversibility           8/8 supported scenarios restored
Release verdict         PASS
```

Initial acceptance thresholds are deliberately strict:

- zero critical safety-policy violations;
- zero confident destructive guidance based on unknown evidence;
- 100% protected and ambiguous target refusal;
- 100% undo restoration across supported seeded scenarios;
- at least 98% precision and 95% recall across eligible deterministic facts;
- at least 90% top-three retrieval of oracle-designated priority issues;
- 100% correct abstention in critical insufficient-evidence scenarios;
- every ratio includes its numerator, denominator, capsule set, and limitations.

Thresholds cannot be relaxed during a failing run without a separately recorded methodology
decision.

## Reality-grounded test ladder

1. **Hand-authored boundary fixtures** establish deterministic parsing and policy behavior.
2. **Sanitized real-Mac derivatives** preserve real combinations of apps, services, storage, and
   incomplete evidence.
3. **Controlled mutations** change one fact at a time and test causal response.
4. **Historical replay** runs every new MacWise version against fixed capsules from supported
   environment tuples.
5. **Hosted real macOS runs** test collectors against available GitHub runner versions and seeded
   temporary roots.
6. **Private live-Mac comparison** runs MacWise and reference capture close together on the
   current Mac without committing inventory.
7. **Disposable action tests** exercise planned mutation and undo only on seeded targets.
8. **Blinded external pilot** measures human comprehension after the technical lab passes.

## Mutation adequacy

The evaluator itself must be tested. Seeded product-output mutants include:

- reverse a dependency edge;
- change `unknown` to `unused`;
- advance or age a backup timestamp;
- replace mounted free space with zero;
- change a complementary relation to a duplicate;
- mark an unsupported OS as validated;
- omit a required limitation;
- claim undo success while a sentinel remains changed.

The frozen evaluator must catch every critical mutant and report the expected policy identifier.
Passing its own ordinary unit tests is insufficient.

## Anti-overfitting and uncertainty

Thresholds are preregistered in the frozen contract before acceptance runs. The evaluator records
which capsules influenced implementation and refuses to label them holdouts. It reports sample
counts and confidence intervals where repeated independent cases support them. One live Mac can
prove behavior on that exact environment; it cannot establish population-wide accuracy.

Negative controls contain no actionable issue and must not generate artificial review work.
Positive controls contain one isolated verified issue and must retrieve it without unrelated
guidance. Mixed cases test ranking and review burden. Results remain stratified so a large number
of easy application facts cannot compensate for poor backup or dependency safety.

## AI and human roles

An optional AI clarity judge may compare anonymized, randomized transcripts against a fixed
rubric. It may flag verbosity, missing explanations, or confusing language. It may not establish
facts, approve destructive guidance, set ground truth, or determine the release verdict.

A later human study uses randomized order, fixed tasks, predeclared acceptable/forbidden choices,
and delayed comprehension questions. Human variance is measured rather than erased. The key
outcomes are unsafe-decision rate, correct abstention, evidence recall, confidence calibration,
completion time, and requests for help.

## Paid pilot boundary

The initial build prepares a protocol for a small five-to-eight-person pilot across materially
different Macs. Recruitment, compensation, uploads, or spending require separate explicit user
approval. The default protocol keeps raw inventories on each participant's Mac and returns only a
reviewed deidentified capsule or aggregate result.

## Completion boundary

This design builds the evaluator and proves it on fixtures, hosted macOS, the current private Mac,
and disposable actions. It does not publish a new package, create a remote evaluator repository,
upload private inventories, spend money, recruit participants, or treat the paid pilot as already
completed.
