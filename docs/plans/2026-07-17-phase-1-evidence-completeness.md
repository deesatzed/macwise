# Phase 1 Evidence Completeness Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use @executing-plans to implement this plan task-by-task.

**Goal:** Close MW-009's named application, Homebrew, and storage inventory gaps while preserving read-only collection, explicit unknowns, and saved-audit compatibility.

**Architecture:** Extend the shared immutable records once, migrate schema-v1 JSON into schema v2 at the reporting boundary, then enrich each independent collector through fixture-driven parsers and fixed read-only adapters. The audit service performs only deterministic cross-record correlation; CLI options are the explicit approval boundary for non-default roots.

**Tech Stack:** Python 3.12, Pydantic v2, Typer, pytest, Ruff, Pyright, macOS `codesign`/`lipo`/`ps`/`diskutil`/`tmutil`, Homebrew JSON v2.

---

Execution mode is the current isolated feature branch with Codex implementing directly.
The controlling autonomous goal already authorizes continuation; no subagents or user
choice are needed between tasks.

### Task 1: Schema v2 and saved-audit migration

**Files:**
- Modify: `src/macwise/models/software.py`
- Modify: `src/macwise/models/storage.py`
- Modify: `src/macwise/models/audit.py`
- Modify: `src/macwise/reporting/json_report.py`
- Modify: `src/macwise/reporting/__init__.py`
- Test: `tests/models/test_audit.py`
- Test: `tests/reporting/test_reports.py`

**Step 1: Write the failing tests**

Add model construction assertions for the optional fields named in
`IMPLEMENTATION_PACKET.md`. Add a literal schema-v1 JSON fixture that omits those fields
and assert `parse_json` upgrades it to schema 2 with safe defaults. Assert schema 2
round-trips and schema 3 is rejected with an actionable validation error.

**Step 2: Run tests to verify red**

Run: `uv run pytest tests/models/test_audit.py tests/reporting/test_reports.py -q`

Expected: FAIL because schema 2 fields and `parse_json` do not exist.

**Step 3: Implement the minimal schema and migration**

Add typed optional/tuple fields only; keep defaults unknown or empty. Change
`AuditDocument.schema_version` to `Literal[2]`. Implement `parse_json(text)` by loading a
JSON object, accepting versions 1 and 2, changing version 1 to 2, then validating through
`AuditDocument`. Reject non-objects and versions outside `{1, 2}`.

**Step 4: Verify green and regressions**

Run: `uv run pytest tests/models tests/reporting -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/macwise/models src/macwise/reporting tests/models tests/reporting
git commit -m "feat: version expanded audit evidence schema"
```

### Task 2: Safe command surface for metadata evidence

**Files:**
- Modify: `src/macwise/system/commands.py`
- Test: `tests/system/test_commands.py`

**Step 1: Write the failing tests**

Parameterize `CODESIGN`, `LIPO`, `PS`, and `TMUTIL` and assert each resolves only to its
fixed Apple path, uses `shell=False`, preserves hostile arguments as one inert argv item,
and applies a bounded output limit. Retain existing Homebrew environment assertions.

**Step 2: Run tests to verify red**

Run: `uv run pytest tests/system/test_commands.py -q`

Expected: FAIL because the enum members and fixed paths do not exist.

**Step 3: Implement the minimal allowlist additions**

Add enum values and fixed candidates `/usr/bin/codesign`, `/usr/bin/lipo`, `/bin/ps`, and
`/usr/bin/tmutil`, each with a one-megabyte default output bound. Do not add a generic
executable escape hatch.

**Step 4: Verify green**

Run: `uv run pytest tests/system/test_commands.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/macwise/system/commands.py tests/system/test_commands.py
git commit -m "feat: allow bounded macOS metadata commands"
```

### Task 3: Application evidence completeness

**Files:**
- Modify: `src/macwise/collectors/applications.py`
- Modify: `src/macwise/cli.py`
- Modify: `tests/fixtures/apps/Example.app/Contents/Info.plist`
- Create: `tests/fixtures/apps/codesign-example.txt`
- Test: `tests/collectors/test_applications.py`
- Test: `tests/cli/test_scan.py`

**Step 1: Write the failing collector tests**

Inject captured command results/process paths and assert the Example bundle reports its
team/publisher/signing identity, `arm64` and `x86_64` architectures, `running=True` only
when the exact executable path appears, and sorted nested `.appex`, `.xpc`, helper-app,
and login-item component paths. Assert `/System/Applications` is protected and missing
metadata remains `None` plus a limitation rather than a false value.

**Step 2: Verify collector red**

Run: `uv run pytest tests/collectors/test_applications.py -q`

Expected: FAIL because the fields and metadata seam do not exist.

**Step 3: Implement minimal application collection**

Read `CFBundleExecutable` from `Info.plist`; call only fixed `codesign -dv --verbose=4`
and `lipo -archs` argument vectors; take one bounded `ps -axo comm=` snapshot; parse
known keys conservatively. Discover components by suffix/known bundle directories without
following symlinks. Mark Apple system roots protected. Emit command limitations per item.

**Step 4: Add and verify explicit-root CLI red/green**

Add a repeatable `--app-root PATH` scan option. Tests assert defaults remain
`/Applications` and `~/Applications`, supplied roots are appended/deduplicated, and no
mounted-volume directory is scanned implicitly.

Run: `uv run pytest tests/collectors/test_applications.py tests/cli/test_scan.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/macwise/collectors/applications.py src/macwise/cli.py tests/collectors/test_applications.py tests/cli/test_scan.py tests/fixtures/apps
git commit -m "feat: enrich application inventory evidence"
```

### Task 4: Homebrew installation and project evidence

**Files:**
- Modify: `src/macwise/collectors/homebrew.py`
- Modify: `src/macwise/cli.py`
- Modify: `src/macwise/services/audit.py`
- Modify: `tests/fixtures/homebrew/formulae.json`
- Modify: `tests/fixtures/homebrew/casks.json`
- Create: `tests/fixtures/projects/sample/pyproject.toml`
- Test: `tests/collectors/test_homebrew.py`
- Test: `tests/cli/test_scan.py`

**Step 1: Write failing metadata tests**

Extend sanitized JSON fixtures with `linked_keg`, `pinned`, and `caveats`. Create bounded
synthetic Cellar/Caskroom directories with executables. Assert records contain install
path, measured size, executable basenames, linked/pinned state, and caveats. Assert names
containing traversal syntax cannot escape the supplied roots and symlink directories are
not followed.

**Step 2: Verify metadata red**

Run: `uv run pytest tests/collectors/test_homebrew.py -q`

Expected: FAIL because the new fields/root discovery do not exist.

**Step 3: Implement minimal installation enrichment**

Capture `brew --prefix`, `brew --cellar`, and `brew --caskroom`. Resolve item roots using
safe basenames and containment checks. Measure with `lstat`/`os.walk(...,
followlinks=False)` and record executable basenames under `bin` and `sbin`. Parse the
machine-readable JSON fields without executing formulae or casks.

**Step 4: Add approved project-reference red/green**

Add a pure bounded manifest scanner for recognized lock/manifests. It receives explicit
project roots, rejects unavailable/symlink roots, caps file size/count, and records only
matching relative paths. Add repeatable `--project-root PATH`; no default home scan.
Thread those roots through `AuditService.run` to the Homebrew collector while retaining
empty defaults for callers that do not opt in.

Run: `uv run pytest tests/collectors/test_homebrew.py tests/cli/test_scan.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/macwise/collectors/homebrew.py src/macwise/cli.py tests/collectors/test_homebrew.py tests/cli/test_scan.py tests/fixtures/homebrew tests/fixtures/projects
git commit -m "feat: enrich Homebrew inventory evidence"
```

### Task 5: Exact Homebrew cask/application relationships

**Files:**
- Modify: `src/macwise/services/audit.py`
- Test: `tests/services/test_audit_service.py`

**Step 1: Write the failing test**

Create one application and one cask whose normalized artifact path exactly matches the
application bundle path/name. Assert both immutable records receive each other's stable
ID and the application install source becomes `homebrew_cask:<token>`. Add an ambiguous
same-basename case and assert no relationship is claimed.

**Step 2: Verify red**

Run: `uv run pytest tests/services/test_audit_service.py -q`

Expected: FAIL because no correlation exists.

**Step 3: Implement deterministic correlation**

Index exact normalized cask artifact basenames. Enrich only one-to-one matches; preserve
unknown install source for zero or multiple matches. Do not infer broader functional
overlap.

**Step 4: Verify green**

Run: `uv run pytest tests/services/test_audit_service.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/macwise/services/audit.py tests/services/test_audit_service.py
git commit -m "feat: link exact Homebrew application records"
```

### Task 6: Storage topology, ownership, and Time Machine evidence

**Files:**
- Modify: `src/macwise/collectors/storage.py`
- Modify: `tests/fixtures/diskutil/list.plist`
- Modify: `tests/fixtures/diskutil/info-internal.plist`
- Create: `tests/fixtures/tmutil/destinationinfo.txt`
- Create: `tests/fixtures/tmutil/exclusions.txt`
- Test: `tests/collectors/test_storage.py`

**Step 1: Write failing topology tests**

Add sanitized plist keys for `WholeDisk`, `ParentWholeDisk`, `Content`,
`APFSContainerReference`, `APFSPhysicalStores`, `GlobalPermissionsEnabled`, and APFS
roles. Assert typed hierarchy and ownership fields preserve identifiers only after the
existing disk-identifier validation.

**Step 2: Verify topology red**

Run: `uv run pytest tests/collectors/test_storage.py -q`

Expected: FAIL because topology fields do not exist.

**Step 3: Implement minimal topology parsing**

Parse hierarchy fields from each `diskutil info -plist` result and use
`AllDisksAndPartitions` only to supplement validated parent relationships. Unknown or
malformed references remain absent with a limitation.

**Step 4: Add Time Machine red/green**

Fixture and parse `tmutil destinationinfo -X` plus `tmutil isexcluded` only for explicit
approved paths. Store destination identity/role and tri-state exclusion evidence without
turning it into a backup-coverage claim. Command failure makes the backup fields unknown
and storage status partial.

Run: `uv run pytest tests/collectors/test_storage.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/macwise/collectors/storage.py tests/collectors/test_storage.py tests/fixtures/diskutil tests/fixtures/tmutil
git commit -m "feat: enrich storage and backup-role evidence"
```

### Task 7: Full acceptance and durable truth

**Files:**
- Modify: `src/macwise/reporting/markdown.py`
- Test: `tests/reporting/test_reports.py`
- Modify: `DECISIONS.md`
- Modify: `PROGRESS.md`
- Modify: `TASK_QUEUE.md`
- Modify: `docs/phase-1-acceptance.md`
- Modify: `CHANGELOG.md`

**Step 1: Write and pass human-readable report tests**

Add failing assertions that verified signing/architecture, Homebrew install evidence,
and storage topology/Time Machine role facts render in Markdown while unknown running,
project-reference, and path-backup states remain explicitly unknown. Implement the
smallest deterministic renderer changes, then run `uv run pytest tests/reporting -q`.

Expected: RED before renderer changes, then PASS.

**Step 2: Run the complete local gate**

```bash
uv run pytest -q
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv build
python3 /Users/o2satz/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/macwise
```

Expected: every command succeeds with no warnings or errors.

**Step 3: Run privacy and packaging smokes**

Run the repository privacy contract, install the wheel into a fresh Python 3.12 virtual
environment, and smoke version/help/JSON/Markdown scan paths. Keep real scan output in
memory only and discard it.

Expected: no private fixture data, install succeeds, reports validate, no host mutation.

**Step 4: Audit every MW-009 acceptance row**

Change only directly evidenced gaps from PARTIAL to PASS. Keep Time Machine path coverage,
public `pipx`, Homebrew tap, and hosted CI limitations explicit where still unproven.

**Step 5: Update durable state and commit**

```bash
git add IMPLEMENTATION_PACKET.md docs/plans DECISIONS.md PROGRESS.md TASK_QUEUE.md docs/phase-1-acceptance.md CHANGELOG.md
git commit -m "docs: record MW-009 acceptance evidence"
```

**Step 6: Continue**

Begin MW-010 malicious metadata fixtures if MW-009 passes; otherwise retain MW-009 as
ready/in-progress with the exact failed gate and mitigation in `PROGRESS.md`.
