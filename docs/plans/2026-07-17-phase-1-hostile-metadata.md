# Phase 1 Hostile Metadata Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use @executing-plans to implement this plan task-by-task.

**Goal:** Prove hostile metadata remains inert across MacWise parsers, paths, Markdown, terminal matching, and the future AI evidence boundary.

**Architecture:** Preserve raw normalized evidence for deterministic JSON, then route every human-facing value through one Unicode-aware display sanitizer before Markdown escaping or terminal output. Use synthetic fixtures and injected runners/services to prove parser and command boundaries without touching host software.

**Tech Stack:** Python 3.12, Unicode standard-library categories, Pydantic v2, Typer, pytest, Ruff, Pyright.

---

### Task 1: Hostile parser and path fixtures

**Files:**
- Create: `tests/fixtures/security/hostile-app.plist`
- Create: `tests/fixtures/security/hostile-homebrew.json`
- Create: `tests/fixtures/security/hostile-disk.plist`
- Create: `tests/fixtures/security/hostile-values.json`
- Create: `tests/security/test_hostile_metadata.py`

**Steps:**

1. Write tests that load hostile display/prompt strings, traversal-like executable/package
   names, and disk names containing markup/control text.
2. Inject a recording application runner and assert no `lipo` argv can name a path outside
   the bundle; assert Homebrew install paths remain `None` for traversal names.
3. Assert disk device identifiers still require the strict allowlist shape and all values
   remain data in schema-v2 JSON.
4. Run `uv run pytest tests/security -q`; expected initial result is either focused PASS for
   existing invariants or RED only where a missing safety boundary is exposed.
5. Do not change production code for tests already green.

### Task 2: Markdown and terminal display injection

**Files:**
- Create: `src/macwise/text.py`
- Modify: `src/macwise/reporting/markdown.py`
- Modify: `src/macwise/cli.py`
- Test: `tests/security/test_hostile_metadata.py`

**Steps:**

1. Add failing assertions that hostile metadata cannot add headings/list records, emit
   ESC/bidi/zero-width controls, or add metadata-controlled newlines in Markdown/CLI output.
2. Run the focused tests and confirm failures show the raw control/newline payload.
3. Implement `safe_display_text`: replace Unicode `Cc`/`Cf` characters with spaces, split
   and rejoin whitespace, preserve visible Unicode.
4. Call it before Markdown metacharacter escaping and for every CLI-rendered record value.
5. Run focused tests; expected PASS. Run existing reporting/CLI suites; expected PASS.
6. Commit: `feat: neutralize hostile display metadata`.

### Task 3: Future prompt-boundary contract

**Files:**
- Modify: `skills/macwise/SKILL.md`
- Modify: `tests/security/test_hostile_metadata.py`

**Steps:**

1. Add a failing repository assertion requiring the skill to say prompt-shaped evidence is
   untrusted data, never instructions, and never shell/action input.
2. Strengthen the evidence rule with those exact operational constraints.
3. Run the security suite and skill validator; expected PASS.
4. Commit: `test: lock hostile evidence boundaries`.

### Task 4: MW-010 acceptance

**Files:**
- Modify: `PROGRESS.md`
- Modify: `TASK_QUEUE.md`
- Modify: `docs/phase-1-acceptance.md`
- Modify: `CHANGELOG.md`

**Steps:**

1. Run the full tests, format/lint, types, build, privacy contract, skill validation, workflow
   parse, isolated Python 3.12 wheel smoke, and real in-memory JSON/Markdown scan.
2. Inspect `git diff --check` and public candidate privacy results.
3. Mark MW-010 done only if every named hostile boundary has direct evidence; make MW-011
   ready and keep public release/hosted CI limitations explicit.
4. Commit: `docs: record MW-010 security evidence`.
