# Opportunity and Usefulness Score Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a deterministic read-only scorecard, evaluate it privately on this Mac, and publish only sanitized aggregate evidence.

**Architecture:** Immutable score models remain separate from the stable audit schema. A pure scoring service consumes an existing `AuditDocument`, applies explicit capped thresholds, and returns reasons/counts/limitations. CLI and report renderers expose the same scorecard without adding collection, persistence, web access, or cleanup authority.

**Tech Stack:** Python 3.12+, Pydantic v2, Typer, pytest, existing MacWise audit models and render/write safeguards.

---

### Task 1: Define immutable score models

**Files:**
- Create: `src/macwise/models/score.py`
- Modify: `src/macwise/models/__init__.py`
- Create: `tests/models/test_score.py`

1. Write failing validation tests for a `ScoreComponent` with key, label, integer score/max,
   observed count, reason, and limitations, plus a `MacWiseScorecard` with exactly six opportunity
   and five usefulness components.
2. Run `uv run pytest tests/models/test_score.py -q`; expect import failure.
3. Implement frozen, extra-forbidden Pydantic models with total-score consistency validators.
4. Export the models and rerun the focused test; expect pass.
5. Commit `feat: add MacWise scorecard models`.

### Task 2: Implement the pure scoring service

**Files:**
- Create: `src/macwise/services/scoring.py`
- Modify: `src/macwise/services/__init__.py`
- Create: `tests/services/test_scoring.py`

1. Build compact synthetic audits for empty, mixed, capped, partial, stale-backup, unknown-heavy,
   recommendation-heavy, and complementary-only cases.
2. Assert exact component totals, counts, reasons, and safety limitations. Assert unknown usage never
   adds non-use points and complementary relations never add overlap points.
3. Run the focused tests and observe missing-service failures.
4. Implement explicit helper functions for capped thresholds and coverage ratios. Compute only from
   `AuditDocument`; do not perform I/O or modify schema version 4.
5. Run the focused models/scoring tests and commit `feat: score audit opportunity and usefulness`.

### Task 3: Add terminal, JSON, and Markdown score output

**Files:**
- Create: `src/macwise/reporting/score.py`
- Modify: `src/macwise/reporting/__init__.py`
- Modify: `src/macwise/help_text.py`
- Modify: `src/macwise/cli.py`
- Create: `tests/cli/test_score.py`
- Modify: `tests/cli/test_help_contract.py`

1. Write failing CLI tests for `macwise score`, three formats, explicit output paths, overwrite
   refusal, read-only wording, component reasons, limitations, and next commands.
2. Add help-contract expectations and observe failures for the missing command.
3. Implement renderers and a `score` command that audits once, calls the pure scorer, and reuses
   `_write_or_print` with score-specific saved-file wording if necessary.
4. Keep terminal output bounded and ensure JSON contains no raw software names or paths.
5. Run focused CLI/help/report tests and commit `feat: add read-only score command`.

### Task 4: Evaluate privately on this Mac and calibrate thresholds

**Files:**
- Modify only tests/scoring thresholds if aggregate evidence disproves a threshold
- Create: `docs/scorecard-evaluation.md`

1. Run `uv run macwise score --format json --output /tmp/macwise-score-private.json`.
2. Cross-check aggregate component counts with `startup`, `overlap`, `review largest`,
   `review unused`, `review unknown`, and `backups`, redirecting any detailed output to `/tmp`.
3. Judge each component for signal, false incentives, and missing evidence. Adjust thresholds only
   with a failing synthetic regression first.
4. Record only totals, component scores/counts, runtime, limitations, and assessment of usefulness;
   exclude names, paths, username, host name, and raw inventory.
5. Commit `docs: record private scorecard evaluation`.

### Task 5: Add the sanitized public example

**Files:**
- Modify: `README.md`
- Modify: `docs/index.html`
- Modify: `docs/assets/macwise.css`
- Modify: `docs/getting-started.md`
- Modify: `docs/demo.md`
- Modify: `tests/repository/test_public_foundation.py`

1. Add failing contracts for both metric names, the “not a bad Mac” and “not personalized proof”
   caveats, and no raw private inventory.
2. Add a compact README score example and a landing-page scorecard using sanitized aggregate or
   fictional values shaped by the private evaluation.
3. Explain how to interpret and reproduce the score in getting-started/demo documentation.
4. Render desktop/mobile pages and correct any clipping or hierarchy regression.
5. Run repository contracts and commit `docs: explain MacWise scorecard`.

### Task 6: Close project truth and verification

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `DECISIONS.md`
- Modify: `PROGRESS.md`
- Modify: `TASK_QUEUE.md`
- Modify: `docs/phase-7-acceptance.md`

1. Record the metric boundary, private aggregate proof, and remaining external release gates.
2. Run the full suite, Ruff format/lint, Pyright, build, privacy contracts, workflow parsing,
   scoped TODO/skip scan, and `git diff --check`.
3. Clone the pushed commit into a fresh temporary directory and run version, doctor, score, and
   score contracts without saving public inventory.
4. Push `main`, watch all hosted CI jobs, and report exact evidence. Do not create a tag, publish a
   package/site/database, or mutate installed software.

