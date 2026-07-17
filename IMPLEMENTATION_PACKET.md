# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Complete MW-009 by closing the named Phase 1 application, Homebrew, and storage
inventory field gaps without weakening MacWise's read-only or privacy boundaries.

## Actual User Goal

Give ordinary Mac users a truthful, versioned inventory substrate that can later
support explanations and cleanup decisions. A value is either backed by a named
local source, explicitly unknown, or qualified by a limitation; MacWise does not
guess and does not mutate the host while auditing.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `src/macwise/models/software.py` | Add optional application and Homebrew evidence fields and relationship IDs. | Medium: public JSON schema change. |
| `src/macwise/models/storage.py` | Add physical/APFS hierarchy, ownership, and Time Machine fields. | Medium: public JSON schema change. |
| `src/macwise/models/audit.py` | Advance the emitted audit schema version. | Medium: saved-audit compatibility. |
| `src/macwise/reporting/json_report.py` | Add a schema-v1-to-v2 read migration. | Medium: invalid input must fail safely. |
| `src/macwise/system/commands.py` | Add fixed read-only `codesign`, `lipo`, `ps`, and `tmutil` adapters. | Medium: host subprocess boundary. |
| `src/macwise/collectors/applications.py` | Collect signing, architecture, running, component, protection, and source evidence. | Medium: metadata varies by macOS/app. |
| `src/macwise/collectors/homebrew.py` | Collect install roots, sizes, executables, linked/pinned/caveat fields, and approved project references. | Medium: Homebrew JSON and filesystem layouts vary. |
| `src/macwise/collectors/storage.py` | Parse disk topology and Time Machine destination/exclusion evidence. | Medium: plist fields vary across macOS versions. |
| `src/macwise/services/audit.py` | Correlate application bundles with Homebrew cask artifacts. | Low: deterministic in-memory enrichment only. |
| `src/macwise/cli.py` | Accept repeatable, explicit app/project roots while retaining safe defaults. | Medium: public CLI contract. |
| `src/macwise/reporting/markdown.py` | Render new verified fields and retain explicit unknown/backup limitations. | Low: user-facing presentation. |
| `tests/models/`, `tests/system/`, `tests/collectors/`, `tests/services/`, `tests/cli/` | Add red-first migration, parser, command, relationship, and approval-boundary tests. | Low. |
| `tests/fixtures/` | Add sanitized signing, topology, Time Machine, and project-reference fixtures. | Low: privacy scan required. |
| `DECISIONS.md`, `PROGRESS.md`, `TASK_QUEUE.md`, `docs/phase-1-acceptance.md` | Record the schema/evidence decisions and verified milestone state. | Low. |

## Existing Patterns To Follow

- Immutable Pydantic records with strict extra-field rejection.
- `Evidence` entries carrying source, collection time, reliability, and limitations.
- Fixed `ReadCommand` executables, argument vectors, `shell=False`, timeouts, bounded
  output, and a restricted environment.
- Parser functions that accept captured fixture data and never need the host.
- Independent collector degradation to `partial` or `unavailable`.
- Red, observed failure, minimal green implementation, full regression gate, commit.

## Assumptions

- Additive fields still require an audit schema increment because strict schema-v1
  readers reject unknown keys; schema-v1 documents will be upgraded on read.
- `codesign -d`, `lipo -archs`, `ps -axo`, `diskutil ... -plist`, and the selected
  `tmutil` queries are read-only evidence sources on supported macOS versions.
- Project reference and external application scans occur only for roots explicitly
  supplied by the user. The absence of approved roots remains unknown, not false.
- Homebrew installation sizes are bounded filesystem measurements of the installed
  keg/cask directories and exclude unrelated user data.
- Time Machine role/destination evidence does not prove that a particular software
  item or data path is backed up.

## Non-Goals For This Pass

- No usage scoring, recommendations, overlap analysis beyond exact cask/app identity,
  or related-user-data estimation.
- No launch, unload, uninstall, move, delete, backup, restore, or configuration writes.
- No unbounded scan of the user's home folder or mounted drives.
- No package publication, Homebrew tap mutation, remote repository creation, or
  production deployment.
- No claim that an unobserved process, project reference, or backup is absent.

## Step-by-Step Plan

1. Add schema-v2 model expectations and a schema-v1 migration test; observe red.
2. Implement only the optional fields and migration needed for green.
3. Add fixed-command safety tests for the new read-only tools; observe red, then green.
4. Add application fixture tests for signing, architecture, running state, nested
   helpers/extensions, protection, and explicitly approved roots; observe red, then green.
5. Add Homebrew fixture tests for size, executables, linked/pinned state, caveats,
   approved project references, and exact app/cask relationships; observe red, then green.
6. Add storage fixture tests for whole-disk/APFS parentage, ownership, backup role,
   destinations, and explicit path exclusion evidence; observe red, then green.
7. Add cross-collector correlation and CLI approval-boundary tests; observe red, then green.
8. Add report assertions that expose verified enrichment and do not overstate unknowns.
9. Run all tests, format/lint, types, build, privacy scan, isolated wheel smoke, and a
   read-only real scan that persists no machine inventory.
10. Update durable truth only with results from the fresh gates.

## Acceptance Criteria

- Audit JSON emits schema version 2, schema-v1 fixtures remain readable, and invalid or
  future versions fail explicitly.
- Application records can carry publisher/signing identity, architectures, tri-state
  running status, nested component names, protected context, and verified install source.
- Homebrew records can carry installed size, executable names, linked/pinned state,
  caveats, user-approved project references, and exact cask/application relationship IDs.
- Storage records can carry whole-disk/APFS hierarchy, ownership state, and Time Machine
  role/destination evidence without claiming path backup coverage.
- Every new subprocess remains allowlisted, bounded, `shell=False`, and inert when given
  hostile metadata arguments.
- Missing tools, permissions, malformed metadata, and unapproved roots yield explicit
  unknowns/limitations while preserving other records.
- The complete local quality, packaging, privacy, and read-only smoke gates pass.

## Verification Plan

- Narrow `uv run pytest ... -q` after every red/green cycle.
- `uv run pytest -q`
- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run pyright`
- `uv build`
- Existing repository privacy contract and skill validator.
- Install the wheel into a fresh Python 3.12 environment and smoke version/help/scan.
- Run JSON and Markdown scans without `--output`; validate structure in memory and discard.

## Rollback Plan

- Each collector slice is a separate commit and can be reverted independently.
- Schema v2 remains uncommitted until its migration test passes.
- No host mutation occurs, so rollback concerns only repository files.
- Generated build artifacts and ephemeral scan output are excluded from commits.

## Risks

| Risk | Mitigation |
|---|---|
| Metadata keys differ by macOS/Homebrew version. | Parse conservatively, fixture multiple shapes, preserve unknowns. |
| Per-app commands make scans slow. | Tight per-command timeouts, bounded output, and partial degradation. |
| Process matching yields false positives. | Match normalized executable paths inside the exact bundle, never names alone. |
| Path traversal through package names or symlinks. | Use safe basenames, containment checks, `lstat`, and no directory symlink following. |
| Project scans expose unrelated files. | Scan only approved roots, recognized small manifests, and store matching paths rather than contents. |
| Backup metadata is overinterpreted. | Separate volume role/destination facts from path coverage and state limitations. |
| Schema bump strands saved audits. | Test a deterministic v1-to-v2 migration and reject unknown future versions. |

## Proceed / Block Decision

**PROCEED.** The work is bounded, read-only, fixture-testable, and has no current
credential, destructive-action, production, sensitive-data, or product-scope blocker.
