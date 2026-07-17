# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Implement MW-400 Phase 5 reversible cleanup: schema-2 ordered execution previews,
fresh action-time revalidation, exact fingerprint approval, append-only crash-visible
execution manifests, dedicated Trash/Homebrew/startup adapters, post-action verification,
and separately approved `macwise undo`.

## Actual User Goal

Let an ordinary Mac user safely act on one fully reviewed MacWise plan and recover when
technically possible. No stale preview, hostile persisted value, ambiguous identity,
unverified external command, crash, or convenience shortcut may silently become mutation
authority. Preserve related data, refuse system/privileged targets, make partial truth
visible, and keep standalone CLI behavior understandable without Codex.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `src/macwise/models/plan.py` and exports | Schema-2 ordered removal/startup action targets while retaining schema-1 reads | High: persisted contract and migration safety |
| `src/macwise/models/execution.py` and exports | Strict immutable run/action/observation/verification/undo manifest models | High: false success or reversibility claims |
| `src/macwise/services/approval.py` | Exact plan/run digest fingerprints and phrases | High: approval replay or normalization confusion |
| `src/macwise/persistence/locking.py` | Shared non-symlink advisory state lock | Critical: cross-database/process race boundary |
| `src/macwise/persistence/plans.py` | Public canonical plan digest and lock-aware append | High: stale approval and existing-state compatibility |
| `src/macwise/persistence/executions.py` | Append-only execution-manifest revisions and active pointer | Critical: crash truth and recovery continuity |
| `src/macwise/services/planning.py` | Fresh schema-2 plans and opt-in supported startup previews | High: hidden or unordered mutation |
| `src/macwise/services/revalidation.py` | Fresh plan/policy/path/package/startup checks and reconstructed operations | Critical: stale or substituted target execution |
| `src/macwise/execution/filesystem.py` | Descriptor-relative synthetic/production Trash rename and inverse | Critical: wrong path, data loss, TOCTOU |
| `src/macwise/execution/commands.py` | Closed exact Homebrew/launchctl mutation operations | Critical: command injection or overly broad uninstall |
| `src/macwise/services/execution.py` | Lock/journal/revalidate/execute/verify/stop/undo coordinator | Critical: partial actions, replay, missing journal |
| `src/macwise/collectors/homebrew.py`, audit/software models | Cask artifact behavior needed for fail-closed action scope | High: cask side effects hidden from approval |
| `src/macwise/cli.py`, `src/macwise/help_text.py` | Real apply/undo approvals, states, recovery, and help | High: accidental action or misleading UX |
| `tests/models`, `tests/persistence`, `tests/services`, `tests/execution`, `tests/cli`, `tests/security` | TDD, exact fake runners, synthetic rename, crash/race/hostile/replay proof | Critical: tests must never reach live mutators |
| `docs/threat-model.md` and acceptance/truth docs | Mutation boundary, limitations, review, and verified local scope | Medium: claims must remain narrower than proof |

## Existing Patterns To Follow

- Strict frozen Pydantic models with `extra="forbid"`, explicit schema versions, and
  stable hashed IDs.
- Canonical JSON plus SHA-256 and append-only SQLite revisions with transactional active
  pointers.
- Full ancestor-symlink checks, read-only schema validation, bound SQL, and optimistic
  concurrency from Phase 4.
- Pure planner/analyzer/revalidator services separated from persistence, subprocesses,
  filesystem mutation, and rendering.
- Exact qualified matching and fail-closed unknown/ambiguity behavior.
- Fixed executable candidates, argv vectors, `shell=False`, safe environment, timeout,
  bounded output, and injected runners/resolvers.
- Shared human-output neutralization while raw model/manifest evidence remains inert.
- Red test, observed intended failure, minimal implementation, focused green, full
  regression, logical commit.

## Assumptions

- The active `/goal`, `GOAL.md`, accepted Phase 4 state, and
  `docs/plans/2026-07-18-phase-5-reversible-cleanup-design.md` approve local Phase 5
  implementation but not real installed-software actions.
- Schema-1 plans remain readable but apply refuses them; users create/refresh a schema-2
  plan before approval.
- A displayed 16-character fingerprint is consent evidence, not authentication; internal
  binding always compares the full plan/run SHA-256.
- Synthetic same-filesystem `.app` moves under canonical `/private/tmp` are safe test
  mutations. The real Applications folders and real Trash are prohibited in tests.
- Homebrew and launchctl actions use fake/injected runners throughout local acceptance.
- Related data is never an action target. Homebrew casks with uninstall/zap/pkg,
  privileged, or unknown removal artifacts are blocked.
- No privilege elevation, account, credential, API key, network service, publication, or
  production deployment is needed.

## Non-Goals For This Pass

- Real installed-app, real Trash, real Homebrew, real launchctl, system, privileged, or
  production mutations.
- Recursive deletion, permanent deletion, Trash emptying, copy fallback, force/zap/
  cleanup/autoremove, shell execution, arbitrary argv, sudo, or Finder authorization.
- System LaunchDaemons, privileged helpers, system/kernel extensions, ambiguous startup
  owners, or startup kinds without a stable inverse.
- Automatic rollback, guaranteed historical Homebrew version restoration, official
  vendor uninstaller execution, related-data deletion, or “safe to remove” claims.
- Remote/background approval, scheduling, daemonization, Codex mutation tools, hosted CI,
  package/tap publication, signing, or release.

## Step-by-Step Plan

1. Add schema-2 plan/order/startup-preview and shared-lock tests; implement minimal
   migration-compatible planning/persistence changes.
2. Add strict execution/observation/approval/manifest model tests and pure helpers.
3. Add append-only execution-store integrity/concurrency/crash tests and persistence.
4. Add fresh revalidation and cask/startup/path reconstruction tests and read-only logic.
5. Add descriptor-relative synthetic Trash apply/verify/undo tests and coordinator slice.
6. Add injected exact Homebrew/startup runner tests and adapter/coordinator support.
7. Add TTY/non-TTY apply/undo/help/recovery tests and CLI integration.
8. Add hostile/race/replay/crash/partial-action safety tests; harden only proven gaps.
9. Request skeptical review; classify every recommendation and fix accepted findings
   test-first.
10. Run full version/quality/build/privacy/skill/clean-wheel/synthetic-action gates and
    record a bounded Phase 5 verdict.

Exact commands, files, expected failures, commits, and rollback notes are in
`docs/plans/2026-07-18-phase-5-reversible-cleanup.md`.

## Acceptance Criteria

- New plans are schema 2 with deterministic ordered targets; schema 1 remains readable
  and is refused by apply with a safe refresh command.
- Every approval binds the full exact active plan/run digest; TTY and non-TTY calls fail
  without the exact visible 16-character phrase/fingerprint.
- Plan append, apply, and undo share one safe advisory state lock; stale/concurrent
  writers cannot interleave plan and execution state.
- Prepared operations are reconstructed from typed kinds plus canonical current roots
  after fresh audit/action checks. Persisted path/command text is never executed directly.
- An append-only integrity-checked manifest revision is durable before every mutator call
  and after every observed outcome. Interrupted state is visible and blocks blind action.
- Manual apps use descriptor-relative, same-filesystem, no-overwrite rename to canonical
  Trash and exact reverse rename; no copying, following symlinks, or deletion.
- Homebrew uses only exact formula/cask uninstall and inverse install forms with fake-
  runner-proven environment/limits; risky/unknown cask artifacts and extra flags block.
- Supported startup disable is opt-in, ordered, current-user only, exactly owned, verified,
  and reversible only while its recorded identity/plist hash remains unchanged.
- Exit status never proves success. Fresh filesystem/Homebrew/startup observation verifies
  each action and inverse; verification failure stops the run.
- First failure stops remaining actions. Earlier applied actions remain truthfully
  manifested and require separately approved reverse-order undo; no auto-rollback occurs.
- Replays, changed targets, blocked/stale plans, unsafe paths, manifest corruption,
  future schemas, concurrent writers, and ambiguous crash recovery fail without broader
  mutation.
- Tests prove that only synthetic temporary bundle renames and fake command runners are
  used. Local acceptance invokes no live installed-software mutator.
- Python 3.12/3.13, Ruff, Pyright, build, privacy, skill, workflow, clean-wheel,
  independent review, and synthetic/fake action gates pass.

## Verification Plan

- Run each exact red/green command in the Phase 5 implementation plan and preserve the
  intended RED evidence in `PROGRESS.md`.
- Run the complete suite in separate isolated Python 3.12.11 and 3.13.13 project
  environments to avoid shared `.venv` races.
- Run Ruff lint/format, Pyright, build, repository privacy, skill validation, workflow
  parse, scoped marker/skip scans, and `git diff --check`.
- Install the wheel into fresh Python 3.12 and prove schema-2 plan/model/store imports,
  apply/undo help, synthetic `/private/tmp` bundle move/verify/undo, and fake
  Homebrew/startup calls only.
- Run a real aggregate-only read audit/revalidation preparation if safe, printing counts
  and states only; never approve or invoke a live adapter.
- Use @requesting-code-review and adjudicate with @receiving-code-review before acceptance.
- Use @claim-validation and @verification-before-completion before any Phase 5 completion
  statement.

## Rollback Plan

Each green slice is a separate Git commit. Revert source/tests/docs commits only. Never
delete, reset, rewrite, or “clean up” an execution journal: it may be the only recovery
record for an interrupted or applied action. Preserve schema-1 plan reads across every
commit. If CLI execution must be disabled, return `apply`/`undo` to an honest refusal
while retaining manifest readers and recovery guidance. Synthetic test roots may expire
naturally; do not run recovery commands against real state during rollback.

## Risks

| Risk | Mitigation |
|---|---|
| Approval applies to changed plan | Full digest, schema-2 requirement, shared state lock, re-read before every action |
| Path/inode replacement after validation | Trusted parent directory descriptors, no-follow lstat, device/inode/identity compare, descriptor-relative rename |
| Persisted destination escapes Trash | Reconstruct from current canonical Trash/action ID and require exact preview equality |
| Homebrew performs wider cask effects | Fresh artifact classification; block uninstall/zap/pkg/privileged/unknown artifacts; no force/zap/cleanup/autoremove |
| LaunchAgent undo executes changed content | Capture and compare exact plist hash/label/owner/path/domain before inverse |
| Crash leaves unknown action result | Commit in-progress first; read-only recovery probe; ambiguous state stays interrupted and blocks mutation |
| Later action fails after earlier success | Stop immediately, record partial truth, require separately approved reverse-order undo |
| Manifest write fails around mutation | Failure before mutation prevents adapter; failure after mutation leaves durable in-progress truth and recovery gate |
| Tests call live mutator | Inject all roots/runners, reject production paths in tests, mutation spies, fake-only acceptance |
| Permission/elevation temptation | Never elevate; report concrete recovery and leave state unchanged |
| External tool/version drift | Unknown parse or verification state blocks; local acceptance does not claim live behavior |
| Scope broadens into related/system data | Closed action enums, plan validators, adapter-specific allowlists, adversarial review |

## Proceed / Block Decision

**PROCEED with local staged implementation only.** `RANKED_OPTIONS.md` estimates the
selected typed staged approach at 84%; `LOOPHOLE_REVIEW.md` raises post-mitigation
confidence to 88% and records required fixes now incorporated in the design and plan.
There is no credential, account, legal, privacy, or local repository blocker. Real
installed-software actions, privilege elevation, production deployment, and publication
remain explicit stop conditions requiring user authority.
