# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Implement MW-100: Phase 2 explain/review with stable matching, multi-signal usage,
startup ownership, bounded related-data estimates, and honest backup limitations.

## Actual User Goal

Turn the Phase 1 inventory into understandable, evidence-linked answers about what an
item is, whether it appears directly or indirectly used, what starts automatically,
which related data was measured, and what backup facts remain unknown—without making a
cleanup recommendation or changing the Mac.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `src/macwise/models/analysis.py` | Add startup, usage, claim-basis, and path-evidence models. | High: public schema. |
| `src/macwise/models/audit.py`, `src/macwise/reporting/json_report.py` | Emit schema 3 and migrate v1/v2 audits. | Medium: saved-audit compatibility. |
| `src/macwise/collectors/usage.py` | Read bounded Spotlight and approved related-data metadata. | Medium: privacy/performance. |
| `src/macwise/collectors/startup.py` | Parse approved/system launch plist locations and map owners conservatively. | Medium: ownership ambiguity. |
| `src/macwise/services/analysis.py` | Produce multi-signal usage findings with explicit basis/confidence. | High: user-facing inference. |
| `src/macwise/services/audit.py` | Assemble raw evidence, startup records, and findings without losing partial results. | Medium. |
| `src/macwise/cli.py`, `src/macwise/reporting/markdown.py` | Replace Phase 2 refusals with evidence-linked read-only views. | Medium: UX truthfulness. |
| `tests/` and sanitized fixtures | Prove every label, unknown, failure, and no-mutation boundary. | Low. |
| Truth/docs files | Record decisions and acceptance evidence. | Low. |

## Existing Patterns To Follow

- Immutable strict Pydantic models and explicit schema migration.
- Fixed bounded commands and filesystem scans that do not follow directory symlinks.
- Independent collector partial/unavailable status.
- Raw evidence stays separate from inference; unknown is never a negative claim.
- Human display sanitization and hostile metadata fixtures remain mandatory.

## Assumptions

- Current running state, active Homebrew service, and recent Spotlight metadata are direct
  signals; dependencies/project references are indirect signals.
- A 30-day Spotlight date supports `recently_used`; old or missing metadata alone never
  supports “unused.”
- Related data is a bounded estimate only for known identifier/name-derived locations and
  excludes arbitrary home scans, caches outside the allowlist, and symlinked directories.
- Startup ownership requires an exact bundle identifier, executable path inside a known
  app, exact Homebrew service name, or unique normalized label match; ambiguity stays unknown.
- Time Machine configuration/last-backup facts do not prove a specific path is recoverable.

## Non-Goals For This Pass

- No overlap categories, learning value, cleanup recommendation, plan, apply, or undo.
- No user decision persistence yet; `user_confirmed` is modeled but not claimed without input.
- No broad shell-history, browser-history, telemetry, or full-home content scan.
- No arbitrary launchctl mutation or startup disable.
- No public release or hosted CI mutation.

## Step-by-Step Plan

1. Add schema-3 analysis/startup/path models and v1/v2 migrations test-first.
2. Add Spotlight last-use and bounded related-data evidence test-first.
3. Add launch plist/Homebrew startup normalization and conservative ownership test-first.
4. Add multi-signal usage analysis with all required labels and explicit unknowns test-first.
5. Add path-specific backup configuration/last-backup limitations without coverage claims.
6. Replace explain/review/startup/backups Phase 2 refusals with deterministic output.
7. Run hostile fixtures, full quality/build/privacy/install/real-read-only gates.
8. Update MW-100 truth; keep Phase 3+ behavior disabled.

## Acceptance Criteria

- Schema 3 round-trips startup records and basis-tagged findings; v1/v2 remain readable.
- Stable exact/qualified matching is tested across app/cask/formula ambiguity.
- Usage labels arise only from defined signal combinations and never from missing evidence.
- Startup records cover launch agents/daemons, Homebrew services, and embedded components,
  with ambiguous owners explicit.
- Related-data estimates are bounded, location-qualified, and do not follow symlinks.
- Backup output states configuration/last verifiable backup/exclusion facts and explicitly
  refuses path coverage when not proven.
- `explain`, `review unused`, `startup`, and `backups` are useful and read-only.
- Full tests, static checks, build, privacy, hostile fixtures, clean install, and real smoke pass.

## Verification Plan

- Red/green focused tests per slice, then `uv run pytest -q`.
- Ruff format/lint, Pyright, build, skill validation, workflow parse, privacy contract.
- Python 3.12/3.13 tests and isolated wheel/pipx smokes.
- Real scans summarized in memory only with no saved inventory.

## Rollback Plan

- One commit per schema/collector/analysis/UX slice.
- Schema migration lands with its tests before collectors emit schema 3.
- No host mutation means rollback is repository-only.

## Risks

| Risk | Mitigation |
|---|---|
| Usage inference overstates absence. | No negative label from missing evidence; basis/confidence/reasons are required. |
| Related-data scan becomes invasive/slow. | Known allowlisted locations, size/file caps, no symlink directory following. |
| Startup ownership false match. | Exact identifiers/paths first, unique normalized label last, ambiguity explicit. |
| Backup configuration is mistaken for coverage. | Separate configuration/last-backup/exclusion facts from path recoverability. |
| Schema churn breaks audits. | Explicit tested v1/v2-to-v3 migration. |

## Proceed / Block Decision

**PROCEED** with the local read-only Phase 2 slices. Hosted CI/public release blockers do
not block these changes.
