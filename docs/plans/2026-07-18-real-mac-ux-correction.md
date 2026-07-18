# Real-Mac UX Correction Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Correct every correctness, terminology, verbosity, and workflow defect observed during the macOS 27 clean-clone walkthrough.

**Architecture:** Preserve normalized evidence and collectors, correcting APFS parsing at the collector boundary and adding bounded summary/detail behavior at the CLI boundary. Reuse existing human-readable byte formatting and role catalog data; do not add destructive behavior or fuzzy inference.

**Tech Stack:** Python 3.12+, Typer, Pydantic, pytest, Ruff, Pyright, uv.

---

### Task 1: Correct APFS free-space evidence and storage presentation

**Files:**
- Modify: `src/macwise/collectors/storage.py`
- Modify: `src/macwise/cli.py`
- Modify: `tests/fixtures/diskutil/info-internal.plist`
- Test: `tests/collectors/test_storage.py`
- Test: `tests/cli/test_phase_two_views.py`

1. Add a parser regression where mounted APFS metadata reports `FreeSpace=0` and positive `APFSContainerFree`; assert the positive value is retained.
2. Run the narrow test and observe the zero-value failure.
3. Prefer a positive `FreeSpace`, otherwise a valid `APFSContainerFree`, while preserving genuine unknown as `None`.
4. Add CLI tests asserting the default view excludes unmounted records, formats IEC units, and prints `unknown` rather than zero for missing evidence.
5. Run the CLI tests red, implement the minimal mounted-volume summary, and rerun green.
6. Commit as `fix: report current APFS storage accurately`.

### Task 2: Bound long default reviews and expose explicit detail

**Files:**
- Modify: `src/macwise/cli.py`
- Modify: `src/macwise/help_text.py`
- Test: `tests/cli/test_phase_two_views.py`
- Test: `tests/cli/test_phase_three_views.py`
- Test: `tests/cli/test_help_contract.py`

1. Add failing tests for bounded `review brew`, `startup`, `review largest`, `review unknown`, and `backups` defaults plus complete `--all` output.
2. Verify failures demonstrate current unbounded output and raw byte formatting.
3. Add a shared small result limit and `--all` flags; print total counts and exact recovery commands when results are hidden.
4. Reuse `_bytes()` for largest applications and keep automation-safe, deterministic ordering.
5. Make backup defaults show only high-value facts and a stale-age warning; show path exclusions only with `--all`.
6. Rerun narrow tests and commit as `feat: make review output concise by default`.

### Task 3: Align overlap terminology and classifications

**Files:**
- Modify: `src/macwise/cli.py`
- Modify: `src/macwise/help_text.py`
- Modify: relevant overlap catalog/analysis module identified by the failing fixture
- Test: `tests/cli/test_phase_three_views.py`
- Test: relevant analysis tests

1. Add a failing CLI test proving `macwise overlap` invokes the same output as `macwise review duplicates` and appears in root help.
2. Add a failing analysis test proving distinct versioned formulae are not categorized as the same product installed twice.
3. Add the alias without removing the existing command.
4. Tighten exact-duplicate identity so version-qualified formula names remain distinct.
5. Rerun narrow tests and commit as `fix: align overlap commands and versioned formulae`.

### Task 4: Remove explain-purpose contradictions and improve known-app coverage

**Files:**
- Modify: `src/macwise/cli.py`
- Modify: the existing role catalog data module
- Test: `tests/cli/test_phase_three_views.py`
- Test: existing catalog tests

1. Add a failing test where a record lacks prose description but has catalog roles; assert explain output presents those roles as its known purpose rather than saying unknown.
2. Add fixture-backed tests for the stable common applications observed in the live run where reliable identifiers/names already exist.
3. Implement role-derived wording and only explicit catalog entries; do not infer from arbitrary names.
4. Rerun narrow tests and commit as `fix: keep purpose output consistent with catalog evidence`.

### Task 5: Document, verify, publish, and repeat the clean-clone audit

**Files:**
- Modify: `PROGRESS.md`
- Modify: `DECISIONS.md`
- Modify: `TASK_QUEUE.md`
- Modify: user documentation if command output or flags changed

1. Update durable truth with each observed issue, root cause, behavior change, and privacy boundary.
2. Run `uv run pytest -q`, Ruff format/lint, Pyright, privacy checks, and `uv build`.
3. Commit documentation, push `main`, and wait for exact-head CI.
4. Clone `origin/main` into a new temporary directory and install with isolated `UV_TOOL_DIR` and `UV_TOOL_BIN_DIR`.
5. Run the complete read-only command matrix autonomously and compare storage values to `df` with tolerance for collection-time changes.
6. Save only aggregate evidence in `PROGRESS.md`; delete the temporary clone, isolated tool, and private audit.
7. Report verified successes and any remaining release blockers without returning the user to command-by-command troubleshooting.

