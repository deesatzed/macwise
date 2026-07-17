# LOOPHOLE_REVIEW.md

## Strategy Under Review

Fingerprint-approved Phase 5 execution using fresh revalidation, dedicated allowlisted
Trash/Homebrew/startup adapters, append-only execution-manifest revisions, verification,
and separately approved undo.

## Confidence Estimate Before Review

| Area | Confidence | Reason |
|---|---:|---|
| Approval and replay | 82% | Plan digests bind consent, but cross-database races and old plans need explicit treatment. |
| Filesystem safety | 76% | Same-filesystem rename is narrow, but path checks alone leave TOCTOU windows. |
| Homebrew safety | 72% | Exact argv is strong, but cask uninstall behavior and interrupted commands can have wider effects. |
| Startup reversibility | 68% | Scope is narrow, but re-enabling a changed plist could execute changed content. |
| Crash recovery | 78% | Pre-action manifest revisions expose interruption, but recovery classification needs exact rules. |
| UX and scope truth | 86% | Public workflow is clear; warnings, partial runs, and schema migration need visible recovery. |

## Loopholes Found

| Loophole | Severity | Why It Matters | Fix |
|---|---|---|---|
| A plan can change between approval/revalidation and mutation because plans and executions use separate databases. | Critical | Consent could apply to a revision other than the one rendered. | Add one advisory state lock acquired by plan append, apply, and undo; re-read and compare plan ID/revision/digest after acquiring it and before every action. |
| A 12-character digest is unnecessarily short for the only visible consent binding. | Important | Local collision risk is small but avoidable. | Use 16 hexadecimal characters and compare the full digest internally. |
| Applying a schema-1 plan created before the execution contract can bypass schema-2 target/order guarantees. | Important | Compatibility could silently weaken new safety invariants. | Keep schema 1 readable but refuse apply; require a freshly collected schema-2 preview. |
| Check-then-rename path validation can race symlink or inode replacement. | Critical | A validated app path could be replaced before mutation. | Open trusted source/Trash parent directory descriptors, capture device/inode and bundle identity, and use descriptor-relative `os.rename`; revalidate immediately before it. |
| A persisted Trash destination could point outside Trash. | Critical | Typed persisted text is still attacker-controlled state. | Reconstruct the destination from plan/action IDs and the canonical Trash root; require exact equality with the preview and never execute the persisted path directly. |
| `brew uninstall --cask` may run cask uninstall artifacts or privileged behavior beyond an app move. | Important | It can exceed the preserve-related-data and no-privilege expectations. | Query fresh cask JSON and block casks with uninstall/zap/pkg/privileged artifacts; never use `--zap`, `--force`, or autoremove. |
| Exit status alone can misclassify an interrupted Homebrew or launchctl action. | Important | Partial side effects could be called success or safe undo. | Verify with fresh read evidence; unresolved/contradictory state becomes interrupted/manual-recovery and blocks further apply. |
| Re-enabling a LaunchAgent whose plist changed after apply can execute new content. | Critical | Undo could launch attacker-controlled or unrelated code. | Capture the exact plist SHA-256, label, owner, path, and prior state; refuse undo if any changed. Never load a system or ambiguous plist. |
| Multiple actions for one candidate can run in unsafe order. | Important | Uninstall before service/agent disable can destroy recovery context. | Schema 2 records and validates a deterministic phase/order: startup disable before removal, reverse order for undo. |
| A manifest write failure after mutation leaves only an in-progress record. | Important | The next command cannot trust whether the action occurred. | Treat in-progress as interrupted; inspect exact before/after state without mutating, append a recovery classification when conclusive, otherwise require manual recovery. |
| Automatic cleanup of successful earlier actions after a later failure would be an unapproved second mutation. | Important | “Safety rollback” can itself cause harm and Homebrew restoration is best effort. | Keep stop-on-first-failure and require separately fingerprint-approved undo. |
| Concurrent apply/undo or plan-add processes can interleave. | Critical | State and host actions could diverge from both manifests. | Hold the advisory state lock for the full apply/undo critical section and reject a second writer quickly with recovery guidance. |
| A test could accidentally call a live mutator. | Critical | Local acceptance must never uninstall or disable real software. | Production mutators require explicit injected boundaries; tests monkeypatch/spies reject live subprocess/real Trash paths, and acceptance runs only synthetic roots/fake runners. |

## Revised Strategy

- Introduce a shared advisory state lock used by plan append, apply, and undo.
- Centralize full canonical plan digest computation; display a 16-character approval
  fingerprint while comparing the full digest internally.
- Emit schema-2 plans for Phase 5 and refuse apply of schema-1 plans with a safe rebuild
  command; retain read-only history compatibility.
- Reconstruct every operation from typed kind plus canonical current roots, then compare
  it with the preview. For Trash, use directory-descriptor-relative rename and captured
  device/inode/bundle identity.
- Add action ordering invariants and reverse-order undo.
- Restrict cask execution to fresh metadata without privileged/uninstall/zap/pkg
  artifacts; never use force, zap, cleanup, or autoremove.
- Hash LaunchAgent plist content and refuse undo or bootstrap if it changed.
- Classify pre-action journal records left in progress through read-only recovery probes;
  ambiguous results remain interrupted and block further mutation.
- Keep all live mutators unavailable to tests and local acceptance through injected
  roots/runners plus explicit mutation spies.

## Confidence Estimate After Fixes

High enough to proceed with staged implementation: 88% overall. Trash rises to 91%,
approval/replay to 92%, manifests/crash handling to 88%, Homebrew to 83%, and startup to
80%. Homebrew and launchctl remain the least certain because external tool behavior can
change and local acceptance intentionally does not mutate live state.

## Remaining Uncertainty

- Homebrew cask metadata shapes may evolve; unknown shapes must block rather than pass.
- Launchctl domain/state behavior differs across macOS versions; unsupported or
  inconclusive output must refuse.
- Exact rollback of historical Homebrew versions is not generally guaranteed.
- Permission failures in `/Applications` cannot be solved without elevation, which is
  outside scope.
- A crash during an external command can leave ambiguous side effects that require human
  recovery; MacWise must report that truth rather than guess.

## Proceed / Do Not Proceed Decision

**PROCEED** with the revised staged strategy. Do not enable an adapter or claim Phase 5
complete until its revalidation, journal-before-mutation, verification, interrupted-state,
and undo tests pass. No real installed-software action is authorized.

## Required Verification

- Cross-process state-lock and stale-digest race tests.
- Schema-1 apply refusal and schema-2 ordering/migration tests.
- Descriptor-relative same-filesystem rename tests covering inode replacement, symlink
  ancestors, occupied destinations, cross-device refusal, verification, and reverse
  rename.
- Exact Homebrew argv/environment tests plus cask-artifact blockers and interrupted
  verification states.
- LaunchAgent plist-digest, owner/domain, changed-content, disable/verify/undo tests.
- Manifest corruption, future schema, concurrent writer, crash-before/after action, replay,
  partial failure, reverse-order undo, and idempotency tests.
- CLI TTY/non-TTY approval, warning disclosure, recovery guidance, and hostile display
  tests.
- Full Python 3.12/3.13 and packaging gates plus only synthetic manual-app and fake-runner
  action demos.
