# Phase 2 Explain and Review Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use @executing-plans to implement this plan task-by-task.

**Goal:** Deliver evidence-linked usage, startup, related-data, and backup explanations without recommendations or host mutation.

**Architecture:** Schema 3 adds normalized startup records and basis-tagged findings beside unchanged inventory facts. Independent read-only collectors gather Spotlight, known-path, launch-plist, and Time Machine facts; a deterministic analysis service maps signals to labels and the CLI/report render the distinction between verified, inferred, user-confirmed, and unknown.

**Tech Stack:** Python 3.12+, Pydantic v2, Typer, plistlib, bounded `mdls`/`tmutil`, pytest, Ruff, Pyright.

---

### Task 1: Schema 3 findings and startup records

**Files:** create `src/macwise/models/analysis.py`; modify model exports/audit and JSON
loader; test `tests/models/test_analysis.py` and reporting migrations.

1. Write failing tests for `ClaimBasis`, `UsageLabel`, `Finding`, `StartupRecord`, and
   `PathEvidence`, plus schema 3 round-trip and v1/v2 migration.
2. Observe red, implement strict immutable models with unknown-safe defaults, observe green.
3. Run model/report regressions and commit `feat: add Phase 2 evidence models`.

### Task 2: Last-use and bounded related-data evidence

**Files:** create `src/macwise/collectors/usage.py`, sanitized mdls/path fixtures, and
`tests/collectors/test_usage.py`; extend the audit service.

1. Test `mdls -name kMDItemLastUsedDate -raw APP_PATH` parsing for date/null/failure.
2. Test allowlisted `~/Library/Application Support`, `Caches`, `Preferences`, and container
   candidates derived from a safe bundle identifier; cap candidates and bytes, reject
   symlink directories, and return storage location per path.
3. Implement minimal collection, run red/green/full gates, commit.

### Task 3: Startup inventory and ownership

**Files:** create `src/macwise/collectors/startup.py`, launch plist fixtures/tests, extend
models/service/reporting.

1. Test user/system LaunchAgent/Daemon plist parsing without loading or executing entries.
2. Normalize label, kind, path, enabled/running unknown, and program/bundle identifiers.
3. Correlate exact bundle ID/path/Homebrew service; keep ambiguous normalized names ownerless.
4. Add embedded login/helper components as startup candidates only when the bundle metadata
   explicitly identifies them; do not infer enabled state.
5. Commit after focused/full gates.

### Task 4: Multi-signal usage findings

**Files:** create `src/macwise/services/analysis.py` and `tests/services/test_analysis.py`.

1. Table-test labels: running/service active→actively used; recent Spotlight→recently used;
   reverse dependency/project reference→indirectly required; startup/config only→configured
   but idle; stale positive timestamp with no other signal→possibly unused; none→no reliable
   evidence; explicit input→user confirmed unused.
2. Require basis/confidence/evidence kinds and forbid “never used.”
3. Implement minimal deterministic precedence and commit.

### Task 5: Backup facts and limitations

**Files:** extend storage/analysis models and collector tests with `tmutil latestbackup` and
path exclusion fixtures.

1. Test configured destination, availability, last verifiable backup, and exact path
   exclusion facts independently.
2. Test that none of those fields alone yields a `covered` finding.
3. Implement bounded reads and explicit limitations; commit.

### Task 6: Explain/review/startup/backups UX

**Files:** modify CLI/help/reporting and their tests.

1. Write failing output tests for exact/qualified ambiguity, four basis sections, usage
   label/reasons, startup owner/state, related-data drive/size, and backup limitations.
2. Implement deterministic output; keep recommendations unavailable until later preflights.
3. Re-run hostile display fixtures and the complete help contract.
4. Commit `feat: deliver Phase 2 explain and review`.

### Task 7: Phase 2 acceptance

Run the full Python 3.12/3.13, quality, build, privacy, skill, clean-install, hostile, and
real read-only gates. Update decisions/progress/task queue/acceptance/changelog only from
fresh results; keep MW-200 and all mutating phases disabled until their own plans pass.
