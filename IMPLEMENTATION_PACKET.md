# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Implement MW-300 Phase 4 cleanup planning: persistent immutable plan revisions, exact
typed change previews, dependency/ambiguity/protection/usage/data/backup/rollback
preflight, and real `macwise plan add/show` behavior with no installed-software actions.

## Actual User Goal

Let an ordinary Mac user turn reviewed evidence into a durable, understandable cleanup
proposal before deciding whether to change anything. Preserve the full MacWise path to
approval-gated reversible cleanup without making a preview executable or claiming that
unknown backup/dependency evidence is safe.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `src/macwise/models/plan.py` and model exports | Strict version-1 immutable plan schema and stable IDs | High: persisted public contract and referential invariants |
| `src/macwise/services/planning.py` and service exports | Pure action preview, preflight, rollback, revision logic | High: unsafe recommendations or false safety claims |
| `src/macwise/persistence/plans.py` and package export | Versioned append-only SQLite store and integrity checks | High: local state loss/corruption/path escape |
| `src/macwise/cli.py`, `src/macwise/help_text.py` | Real plan add/show UX; apply/undo remain refusals | High: preview could be mistaken for approval or action |
| `tests/models`, `tests/services`, `tests/persistence`, `tests/cli`, `tests/security` | TDD, hostile-data, integrity, zero-mutation proof | Medium: spies must distinguish local plan-state writes from host mutation |
| `docs/threat-model.md` and acceptance/truth docs | Persisted-state threat boundary and verified status | Low: claims must remain narrower than evidence |

## Existing Patterns To Follow

- Strict frozen Pydantic models with `extra="forbid"` and stable hashed identifiers.
- Audit schema and package versions remain independent; plan schema is independently
  versioned.
- Exact qualified CLI matching and refusal on ambiguity.
- Pure deterministic analysis services separated from I/O and rendering.
- Shared terminal text sanitization; raw persisted/JSON data remains untrusted.
- Expected failures degrade to typed bounded public errors, never private stack details.
- Red test, observed failure, minimal implementation, focused green, full regression,
  logical commit.

## Assumptions

- `GOAL.md`, the active autonomous continuation, and
  `docs/plans/2026-07-17-phase-4-cleanup-planning-design.md` approve retaining one exact
  unsafe target as a blocked review item; ambiguous names still refuse.
- Phase 4 may write only local MacWise plan state beneath the platform user data
  directory or an injected test path.
- A backup warning is not a coverage claim. Related user data is preserved and excluded
  from every Phase 4 action preview.
- Typed intent and rollback blueprints support Phase 5, but Phase 5 must reconstruct and
  revalidate allowlisted actions against current host state.
- No credential, account, API key, network service, or production deployment is needed.

## Non-Goals For This Pass

- Applying, approving, verifying, or undoing any action.
- Invoking Homebrew uninstall, moving an app to Trash, disabling startup, or deleting
  related data.
- Multiple named plans, item removal/reordering, interactive decision questionnaires,
  cloud sync, AI research, or Codex setup.
- Hosted CI, package/tap publication, signing, or public release.

## Step-by-Step Plan

1. Add failing tests and minimal strict plan models.
2. Add failing synthetic preflight/action/rollback fixtures and the pure planner.
3. Add failing isolated SQLite revision/integrity tests and the append-only store.
4. Add failing CLI/help/guided tests and real `plan add/show` integration.
5. Add hostile-data and zero-host-mutation tests; harden only demonstrated boundaries.
6. Request independent skeptical review; adjudicate every finding and test accepted fixes.
7. Run full version, quality, build, privacy, skill, clean-wheel, temporary-state, and
   aggregate-only real read-only gates.
8. Record a bounded Phase 4 acceptance verdict and advance only MW-400 if proven.

## Acceptance Criteria

- Plan version 1 is immutable, strict, deterministic, referentially valid, and round-trips.
- Persisted plans contain typed action intent but no executable command/shell field.
- Every required preflight is fixture-tested with pass/warning/block semantics.
- Ambiguous targets do not alter state; exact unsafe targets remain visibly blocked.
- Related data and startup records remain untouched; backup coverage remains unverified.
- SQLite revisions append atomically, verify integrity, preserve history, and fail closed
  on corruption/future versions/unsafe paths.
- `plan add`, `plan`, and `plan show` are useful and honest; apply/undo remain nonzero
  Phase 5 refusals even for preview-ready plans.
- Hostile metadata is inert in models, SQLite, terminal output, and future action intent.
- Tests prove Phase 4 performs no installed-software, Trash, Homebrew, startup, or related
  data mutation.
- Python 3.12/3.13, Ruff, Pyright, build, privacy, skill, workflow, fresh-wheel, and
  aggregate-only real planning gates pass.

## Verification Plan

- Run each exact red/green command from
  `docs/plans/2026-07-17-phase-4-cleanup-planning.md`.
- Run the complete test suite under Python 3.12.11 and 3.13.13.
- Run Ruff lint/format, Pyright, build, skill validator, workflow parse, repository
  privacy tests, scoped stub/skip scans, and `git diff --check`.
- Install the wheel into a fresh Python 3.12 environment and exercise plan schema,
  temporary SQLite persistence, and help.
- Run one real audit through the pure planner in memory and print aggregate counts only.
- Perform and adjudicate independent code review before acceptance.

## Rollback Plan

Each green slice is a separate Git commit. Before Phase 5, rollback affects only source,
tests, documentation, and local MacWise plan-state schema. No Phase 4 commit can require
restoring installed software because execution code is absent. SQLite migrations are
additive and never delete prior revisions; a failed transaction must preserve the prior
active pointer.

## Risks

| Risk | Mitigation |
|---|---|
| Persisted preview is mistaken for approval | Separate eligibility from approval, render no-authority language, keep apply disabled |
| Hostile/stale plan data becomes executable | Typed action fields only; future executor reconstructs and revalidates allowlisted operations |
| False backup/removal-safety claim | Warning-only bounded facts; never use “covered” or “safe to remove” |
| Dependency or keep-together harm | Blocking reverse-dependency/project/usage/overlap checks |
| SQLite loss or corruption | Append-only atomic transactions, version checks, canonical digest, no destructive migration |
| State path escape or symlink confusion | Injected tests, platform-owned default, resolved-parent/type checks, fail closed |
| Phase creep into mutation | No executor module/import, mutation spies, apply/undo refusal regressions |

## Proceed / Block Decision

**PROCEED.** The approved design and implementation plan define a bounded, reversible
repository change. There is no credential, destructive-action, privacy, legal, or scope
blocker. Installed-software actions remain prohibited until Phase 5 design and proof.
