# Simple First-Run UX Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use test-driven-development and executing-plans to implement this plan task-by-task.

**Goal:** Give a first-time user one bounded, evidence-linked checkup journey from first command to a clear next step and no-change summary.

**Architecture:** Add immutable checkup summary models, a pure deterministic prioritization service, and terminal rendering separated from collection. Expose them through `macwise checkup` and the guided menu while preserving `scan`, `score`, structured reports, planning, and execution boundaries.

**Tech Stack:** Python 3.12+, Pydantic v2, Typer, pytest, Ruff, Pyright, uv.

---

### Task 1: Checkup summary contract

**Files:**
- Create: `src/macwise/models/checkup.py`
- Create: `src/macwise/services/checkup.py`
- Modify: `src/macwise/models/__init__.py`
- Modify: `src/macwise/services/__init__.py`
- Test: `tests/models/test_checkup.py`
- Test: `tests/services/test_checkup.py`

1. Write failing tests for immutable priority cards, supported focus commands, deterministic
   ranking, three-to-five bounds when enough domains exist, and safe unknown/non-use language.
2. Run the focused tests and observe failures caused by missing checkup types/service.
3. Implement the minimal pure models and audit-to-checkup transformation.
4. Run focused tests to green and refactor only after green.

### Task 2: Terminal checkup and first-run routing

**Files:**
- Create: `src/macwise/reporting/checkup.py`
- Modify: `src/macwise/reporting/__init__.py`
- Modify: `src/macwise/cli.py`
- Modify: `src/macwise/help_text.py`
- Test: `tests/cli/test_checkup_command.py`
- Modify: `tests/cli/test_guided_menu.py`
- Modify: `tests/cli/test_help_contract.py`

1. Write failing CLI tests for `macwise checkup`, collection freshness, bounded cards, benefit,
   non-claim, next action, and no-change confirmation.
2. Write failing guided tests proving choice 1 is recommended, reuses one fresh audit for a
   focused follow-up, offers a safe stop, and emits a final session summary.
3. Observe the focused failures, implement the renderer/command/routing, then rerun to green.
4. Preserve non-TTY safe exit and deterministic direct commands.

### Task 3: Unknown item and cleanup-plan handoff

**Files:**
- Modify: `src/macwise/cli.py`
- Test: `tests/cli/test_checkup_command.py`
- Test: `tests/cli/test_phase_four_planning.py`

1. Write failing tests for numbered unknown-item choices, verified-local-facts display, explicit
   leave-unknown behavior, and no web search/upload claim.
2. Write failing tests for adding an eligible explained item to an immutable plan preview without
   applying it.
3. Observe failures, implement the minimal in-process guided handlers, and rerun focused planning
   and execution-safety regressions.

### Task 4: Score and freshness language

**Files:**
- Modify: `src/macwise/reporting/score.py`
- Modify: `src/macwise/services/scoring.py`
- Modify: `src/macwise/help_text.py`
- Test: `tests/cli/test_score_command.py`
- Test: `tests/reporting/test_reports.py`
- Test: `tests/services/test_scoring.py`

1. Write failing tests for “Review opportunities found,” explicit report-confidence meaning, and
   the largest missing evidence explanation.
2. Implement only presentation/additive limitation changes; keep JSON schema compatible unless a
   tested additive migration is needed.
3. Prove score, scan, and checkup each state whether evidence is freshly collected or explicitly
   saved.

### Task 5: Documentation and sanitized acceptance artifact

**Files:**
- Modify: `README.md`
- Modify: `docs/getting-started.md`
- Modify: `docs/demo.md`
- Modify: `docs/index.html`
- Create: `docs/simple-ux-acceptance.md`
- Modify: `tests/repository/test_public_foundation.py`

1. Write failing repository contracts for one consistent first step, `uv` explanation, current
   unpublished-install truth, and matching terminal examples.
2. Update all public surfaces and add a sanitized transcript answering the eight acceptance
   questions in `GOAL_SIMPLE_UX.md`.
3. Render the static page at desktop and mobile widths and inspect it for clipping and stale flow.

### Task 6: Full evidence and durable state

**Files:**
- Modify: `DECISIONS.md`
- Modify: `PROGRESS.md`
- Modify: `TASK_QUEUE.md`
- Modify: `docs/phase-7-acceptance.md`

1. Run focused CLI/model/service/safety tests.
2. Run the full pytest, Ruff format/lint, Pyright, build, privacy/repository, workflow, and
   `git diff --check` gates.
3. Install the built wheel into isolated UV tool directories and run the sanitized journey.
4. Run one real-Mac read-only checkup and retain aggregate evidence only.
5. Audit every goal requirement, record exact results and limitations, commit coherent changes,
   push `main`, and verify hosted CI before completion.
