# Phase 1 Public Read-Only CLI Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task.

**Goal:** Build and verify MacWise's installable, guided, strictly read-only Phase 1 CLI with application, Homebrew, and drive inventory plus JSON and Markdown audits.

**Architecture:** A thin Typer/Rich CLI calls an audit service. Isolated collectors use a safe bounded command adapter and emit versioned Pydantic records; reporters consume the resulting audit document without host access.

**Tech Stack:** Python 3.12+, Typer, Rich, Pydantic v2, platformdirs, pytest, Ruff, Pyright, uv/hatchling.

---

### Task 1: Public package and guided CLI vertical slice

**Files:**
- Create: `pyproject.toml`
- Create: `src/macwise/__init__.py`
- Create: `src/macwise/__main__.py`
- Create: `src/macwise/cli.py`
- Create: `tests/cli/test_root.py`
- Create: `tests/conftest.py`
- Create: `.gitignore`

**Step 1: Write the failing test**

Use Typer's `CliRunner` to invoke the app with no arguments in a non-TTY test. Assert exit code zero, the `MacWise` heading, all nine numbered choices from `GOAL.md`, and the direct-command recovery sentence. Add a second test that `--help` contains a plain-English purpose, read-only statement, examples, and next action.

**Step 2: Verify the test fails for the missing package**

Run: `uv run pytest tests/cli/test_root.py -q`

Expected: collection error because `macwise.cli` does not exist.

**Step 3: Add the minimal package and CLI**

Create a Typer app with `invoke_without_command=True`, `no_args_is_help=False`, and a callback that prints the fixed guided menu when no subcommand was invoked. Keep the callback side-effect free. Export `main()` and wire the `macwise` console script.

**Step 4: Verify green and run static gates**

Run:

```bash
uv run pytest tests/cli/test_root.py -q
uv run ruff check .
uv run pyright
uv build
```

Expected: all commands exit zero.

**Step 5: Update project truth and commit**

Mark MW-001 verified in `PROGRESS.md`/`TASK_QUEUE.md`, record exact command results, then commit package, test, and truth changes as one vertical slice.

### Task 2: Versioned evidence and audit models

**Files:**
- Create: `src/macwise/models/evidence.py`
- Create: `src/macwise/models/software.py`
- Create: `src/macwise/models/storage.py`
- Create: `src/macwise/models/audit.py`
- Create: `src/macwise/models/__init__.py`
- Create: `tests/models/test_evidence.py`
- Create: `tests/models/test_audit.py`

**Step 1: Write failing model tests**

Assert reliability/entity enums, timezone-aware collection times, stable IDs, schema version `1`, round-trip JSON, and collector limitations. Assert an absent last-use source is encoded as an unknown limitation and no serialized value contains the claim `never used`.

**Step 2: Verify red**

Run: `uv run pytest tests/models -q`

Expected: imports fail because the model modules are absent.

**Step 3: Implement minimal strict Pydantic models**

Use `ConfigDict(extra="forbid", frozen=True)` for evidence and normalized record models. Use enums for entity/reliability/status values, timezone validators, and a `schema_version: Literal[1] = 1` audit field. Keep raw evidence JSON-safe and recommendations out of Phase 1 models.

**Step 4: Verify green/full suite**

Run: `uv run pytest -q && uv run ruff check . && uv run pyright`

Expected: zero failures/errors.

**Step 5: Update truth and commit**

Record schema decision if it changed and commit models/tests.

### Task 3: Safe read-command adapter

**Files:**
- Create: `src/macwise/system/commands.py`
- Create: `src/macwise/system/__init__.py`
- Create: `tests/system/test_commands.py`

**Step 1: Write failing behavioral tests**

Inject a process function and assert the adapter passes a sequence, `shell=False`, a timeout, bounded environment, and capture settings. Test allowlist rejection, timeout, missing executable, nonzero exit, invalid UTF-8 replacement, and output truncation. Include an argument containing `$(touch /tmp/macwise-injection)` and prove it remains one inert argument.

**Step 2: Verify red**

Run: `uv run pytest tests/system/test_commands.py -q`

Expected: module import failure.

**Step 3: Implement the adapter**

Return a typed immutable result with stdout/stderr, return code, status, duration, and limitation. Accept only a declared `ReadCommand` enum mapped to fixed candidates. Never accept a raw executable from a collector.

**Step 4: Verify green/full gates**

Run: `uv run pytest -q && uv run ruff check . && uv run pyright`

Expected: zero failures/errors.

**Step 5: Update truth and commit**

Record verified safety properties and commit.

### Task 4: Application inventory

**Files:**
- Create: `src/macwise/collectors/applications.py`
- Create: `src/macwise/collectors/__init__.py`
- Create: `tests/collectors/test_applications.py`
- Create: `tests/fixtures/apps/Example.app/Contents/Info.plist`

**Step 1: Write failing fixture-backed tests**

Build synthetic roots for `/Applications` and `~/Applications` equivalents. Assert stable identity, display name, bundle ID/version, path, bundle size, external-volume flag supplied by the storage resolver, and limitation evidence for missing/malformed plists. Assert the collector never calls an app executable.

**Step 2: Verify red**

Run: `uv run pytest tests/collectors/test_applications.py -q`

Expected: collector import failure.

**Step 3: Implement minimal filesystem/plist collection**

Use `pathlib`, `plistlib`, and non-following traversal rules. Read configured roots only, never launch applications, and turn per-item errors into limitations.

**Step 4: Verify green/full gates**

Run: `uv run pytest -q && uv run ruff check . && uv run pyright`

Expected: zero failures/errors.

**Step 5: Update truth and commit**

Record collector coverage and commit sanitized fixtures/code/tests.

### Task 5: Homebrew inventory and dependency distinction

**Files:**
- Create: `src/macwise/collectors/homebrew.py`
- Create: `tests/collectors/test_homebrew.py`
- Create: `tests/fixtures/homebrew/formulae.json`
- Create: `tests/fixtures/homebrew/casks.json`
- Create: `tests/fixtures/homebrew/leaves.txt`
- Create: `tests/fixtures/homebrew/services.json`

**Step 1: Write failing parser/orchestration tests**

Assert formula/cask normalization, explicit leaf status, dependencies, reverse dependencies, descriptions/homepages, installed versions, service relationship, and cask-to-app mapping. Include `openssl@3` as an indirect dependency and assert it is not an ordinary removal candidate.

**Step 2: Verify red**

Run: `uv run pytest tests/collectors/test_homebrew.py -q`

Expected: collector import failure.

**Step 3: Implement machine-readable collection**

Request only Homebrew JSON/text surfaces through the command adapter. Keep parsing pure and independently testable. If Homebrew is absent or a subcommand fails, return an explicit unavailable/partial collector status.

**Step 4: Verify green/full gates**

Run: `uv run pytest -q && uv run ruff check . && uv run pyright`

Expected: zero failures/errors.

**Step 5: Update truth and commit**

Record dependency-classification evidence and commit.

### Task 6: Drive inventory

**Files:**
- Create: `src/macwise/collectors/storage.py`
- Create: `tests/collectors/test_storage.py`
- Create: `tests/fixtures/diskutil/list.plist`
- Create: `tests/fixtures/diskutil/info-internal.plist`
- Create: `tests/fixtures/diskutil/info-external.plist`

**Step 1: Write failing plist-fixture tests**

Assert mount point, filesystem, capacity/free space, internal/external classification, removable/read-only/encryption fields, and per-volume limitations. Include one unmounted and one unavailable volume.

**Step 2: Verify red**

Run: `uv run pytest tests/collectors/test_storage.py -q`

Expected: collector import failure.

**Step 3: Implement structured disk collection**

Use `diskutil ... -plist` only through the adapter. Parse with `plistlib`, preserve unknown fields as unknown rather than guessing, and expose a deterministic path-to-volume resolver.

**Step 4: Verify green/full gates**

Run: `uv run pytest -q && uv run ruff check . && uv run pyright`

Expected: zero failures/errors.

**Step 5: Update truth and commit**

Record drive coverage and commit.

### Task 7: Audit orchestration and JSON/Markdown reporting

**Files:**
- Create: `src/macwise/services/audit.py`
- Create: `src/macwise/services/__init__.py`
- Create: `src/macwise/reporting/json_report.py`
- Create: `src/macwise/reporting/markdown.py`
- Create: `src/macwise/reporting/__init__.py`
- Create: `tests/services/test_audit.py`
- Create: `tests/reporting/test_reports.py`

**Step 1: Write failing integration/golden tests**

Inject fake collectors and assert aggregation continues after one partial failure, timestamps/schema are present, record ordering is stable, and JSON round-trips. Assert Markdown separates verified inventory from collection limitations and never claims missing usage/backup data is negative evidence.

**Step 2: Verify red**

Run: `uv run pytest tests/services tests/reporting -q`

Expected: missing modules.

**Step 3: Implement the service/reporters**

Use collector protocols and immutable results. Sort records by stable public keys. Serialize with the audit model, not ad hoc dictionaries. Markdown is a pure rendering function.

**Step 4: Verify green/full gates**

Run: `uv run pytest -q && uv run ruff check . && uv run pyright`

Expected: zero failures/errors.

**Step 5: Update truth and commit**

Record report evidence and commit.

### Task 8: Complete Phase 1 CLI hierarchy and help contract

**Files:**
- Modify: `src/macwise/cli.py`
- Create: `src/macwise/help_text.py`
- Create: `tests/cli/test_help_contract.py`
- Create: `tests/cli/test_scan.py`
- Create: `tests/cli/test_guided_menu.py`

**Step 1: Write failing command-matrix tests**

Parameterize required root and nested commands. For every command assert a plain-English opening, useful-when explanation, change/read-only statement, two examples, and next command. Test guided selections route to scan/review/startup/storage/explain/plan/help services. Test `scan --format terminal|json|markdown` and explicit output-file behavior.

**Step 2: Verify red**

Run: `uv run pytest tests/cli -q`

Expected: failures enumerate missing commands/help clauses.

**Step 3: Implement honest Phase 1 commands**

Wire `scan` and Phase 1 review views to real services. Provide the required hierarchy without fake Phase 2–5 claims: commands outside the mature slice explain their current safe capability or explicit availability status and never mutate. Keep all host access behind injected services.

**Step 4: Verify green/full gates**

Run: `uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run pyright && uv build`

Expected: zero failures/errors.

**Step 5: Update truth and commit**

Mark applicable Phase 1 tasks verified and commit.

### Task 9: Public foundation, CI, and Phase 1 acceptance audit

**Files:**
- Create: `README.md`
- Create: `LICENSE`
- Create: `SECURITY.md`
- Create: `CONTRIBUTING.md`
- Create: `CHANGELOG.md`
- Create: `docs/privacy.md`
- Create: `docs/threat-model.md`
- Create: `.github/workflows/ci.yml`
- Modify: `PROGRESS.md`
- Modify: `TASK_QUEUE.md`

**Step 1: Add failing documentation/package checks**

Add a test or script that asserts required public files, README section order, install/usage/safety/Codex examples, and no forbidden real-user path patterns in tracked content.

**Step 2: Verify red**

Run the new check and confirm it lists missing public files.

**Step 3: Add truthful public documentation and CI**

Document only current capabilities, clearly label later-phase roadmap items, include uninstall/privacy/security limitations, and configure macOS plus a portable test job where useful.

**Step 4: Run the complete acceptance surface**

Run:

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv build
```

Install the wheel in a fresh temporary environment and run `macwise --help`, `macwise`, `macwise scan --help`, and fixture-backed JSON/Markdown scan smokes. On macOS, run the bounded real read-only scan and inspect its limitation reporting without saving local inventory to Git.

**Step 5: Audit Phase 1 requirements and commit**

Map each Phase 1 deliverable and relevant global invariant to direct evidence in `PROGRESS.md`. Leave incomplete items open. Commit only after fresh full verification and privacy scan.
