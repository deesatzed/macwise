# Phase 5 Acceptance Audit

Date: 2026-07-18

Verdict: **PASS for MW-400 local reversible-cleanup scope**. Phase 5 now binds one
reviewed schema-2 plan to exact approval, revalidates action-relevant evidence while the
shared state lock is held, journals before mutation, invokes only closed allowlisted
adapters, verifies fresh after-state, and offers separately approved reverse-order undo.
Interrupted actions are classified from fresh evidence as unchanged, applied, or
ambiguous before recovery.

This is not a production-safety or live-host verdict. Local acceptance used only pytest
temporary application bundles, synthetic Trash roots, injected Homebrew/launchctl
runners, and read-only host probes. It does not prove permissions or behavior for a real
installed application, the user's real Trash, live Homebrew, live launchctl, hosted CI,
publication, Codex integration, or every crash timing.

## Acceptance evidence

| Requirement | Verdict | Direct evidence | Honest limitation |
|---|---|---|---|
| Exact reviewed approval | PASS | Exact `APPLY` and `UNDO` parsing, full active plan/manifest digest checks, stale active-pointer refusal, replay exclusion, and prepared-action substitution regressions pass. | The displayed 16-hex fingerprint is a consent identifier with a theoretical 64-bit collision limit, not a secret. |
| Fresh action-time policy | PASS | Action-specific collector-completeness tests, in-lock revalidation, and active full-digest reload before each ordered action pass. | A collector that cannot establish complete relevant evidence blocks execution. |
| Crash-visible journal | PASS | Immutable canonical revisions are appended before every mutator; corruption, future schema, unsafe paths, state transitions, partial state, and interrupted recovery are tested. | SQLite state is local and does not protect against an attacker with full account control. |
| Trash move and restore | PASS | Descriptor-relative exclusive no-replace same-filesystem rename tests verify device, inode, and descriptor-read Info.plist identity before/after move and reverse restore. | Only synthetic bundles under pytest temporary roots were moved; related data is untouched. |
| Homebrew and startup actions | PASS | Fixed executable, safe token/label, reduced environment, no-shell, changed-plist, bounded-output, current-user-domain, ordering, and fake-runner verification tests pass. | No live formula, cask, service, or LaunchAgent was changed; reinstall remains best-effort. |
| Verification and unknown handling | PASS | Complete-collector absence is required for `installed=False`; generic launchctl failure stays unknown; nonzero and unverified after-state stop and journal safely. | Exit status alone never proves the requested host state. |
| Partial and interrupted recovery | PASS | Command failure observations, multi-action recovery, interrupted command apply, interrupted undo, interrupted Trash move, retry from undo-partial, and older-run history selection pass. | State that matches neither recorded before nor expected after remains ambiguous and is not automatically mutated. |
| CLI recovery UX | PASS | Apply/undo approval, partial/verification failure, doctor manifest summaries, interrupted classification guidance, help, and no-plan/stale-plan refusal tests pass. | Recovery still requires explicit separate approval and may require manual escalation when evidence is ambiguous. |

## Independent review disposition

| Recommendation | Classification | Resolution |
|---|---|---|
| Add usable recovery for partial, verification-failed, and interrupted runs | Accepted / Resolved | Fresh locked classification records unchanged/applied/ambiguous state and separately approved undo reverses only safely observed actions. |
| Do not interpret missing Homebrew records as absence when collection is incomplete | Accepted / Resolved | Absence becomes `False` only with a complete relevant collector; otherwise it remains unknown. |
| Display the complete digest in approval phrases | Rejected | D-026 intentionally uses a 16-character consent fingerprint; full active plan/manifest digests are independently checked internally. The collision limitation is documented. |
| Require action-relevant collector completeness | Accepted / Resolved | Applications, Homebrew, startup, usage, backup, and overlap completeness are required according to action kind. |
| Revalidate under the lock and reload active plan identity before every action | Accepted / Resolved | The execution service invokes the revalidator while holding the exact shared lock and checks the full active digest before each action. |
| Treat generic `launchctl print` failure as unknown | Accepted / Resolved | Only canonical not-found exit/output evidence maps to not running; other failures remain unknown. |
| Make doctor expose durable recovery state and a usable next step | Accepted / Resolved | Doctor prints run/action states and routes recoverable/interrupted state to approved undo classification. |
| Bound mutation-command output before it is fully buffered | Accepted / Resolved | The production runner drains both pipes while retaining only 64 KiB plus one overflow byte per stream. |
| Strengthen Trash identity beyond path/device/inode | Accepted / Resolved | Identity now includes descriptor-read Info.plist content alongside device and inode and is rechecked at rename time. |
| Reject non-regular lock files | Accepted / Resolved | `fstat()` rejects FIFOs/devices before advisory locking. |
| Preserve the first successful LaunchAgent sub-step when the second fails | Accepted / Resolved | Any command error triggers fresh observation; safely observed partial enablement/running state is journaled for approved inverse recovery. |
| Keep older applied runs reachable after a newer run is undone | Accepted / Resolved | Integrity-checked history selects the latest still-undoable run and permits resuming its append-only revision chain only after the active run is fully undone. |
| Preserve possible mutation when post-action evidence is unavailable | Accepted / Resolved | Missing or typed-unknown decisive evidence preserves the action as in-progress/unknown and the run as interrupted for later fresh classification. |
| Let fully restored partial runs terminate when later actions never ran | Accepted / Resolved | Never-attempted tail actions become explicit, strictly validated `NOT_APPLIED`; only mutated actions require `UNDONE`. |
| Require authoritative startup item state | Accepted / Resolved | LaunchAgent enabled/running and Homebrew-service running state must be concrete booleans before preparation. |
| Reconstruct LaunchAgent inverse from fresh partial state | Accepted / Resolved | Enable/disable and bootstrap/bootout are emitted only for the delta between fresh current state and recorded prior state. |
| Treat absent collector-status tuples as incomplete | Accepted / Resolved | Required collector statuses must be explicitly complete; production no longer has a synthetic-fixture bypass. |
| Bound lock contention and unreadable identity at the CLI boundary | Accepted / Resolved | Lock errors become bounded execution errors; unsafe metadata reads become unknown observations and fail revalidation. |
| Enforce authoritative after-state again at undo time | Accepted / Resolved | Undo refuses any recorded after-state with an unknown kind-specific decisive field before invoking an inverse. |
| Enforce action-level `NOT_APPLIED` truth | Accepted / Resolved | Strict models require pending verification, no after-state, and no error. |

The primary and fast independent reviews initially blocked acceptance. Two subsequent
read-only re-reviews found additional recovery edge cases; those were fixed test-first.
The final review reported no remaining Critical or Important findings and recommended
local Phase 5 acceptance.

## Fresh verification

- Python 3.12.11: 292 tests passed.
- Python 3.13.13: 292 tests passed.
- Full-suite statement coverage measured 89%.
- Ruff lint and format checks passed; Pyright reported 0 errors.
- `uv build` produced the `macwise-0.1.0a0` wheel and source distribution.
- The repository privacy contract reported 5 passing tests.
- The bundled read-only skill validated; the pinned CI workflow parsed as YAML.
- A fresh Python 3.12 wheel environment rendered root/apply/undo help; 43
  installed-wheel tests passed synthetic Trash, fake command, coordinator, and interrupted
  recovery behavior.
- Focused execution/security/repository tests reported 49 passing tests.
- Scoped TODO/FIXME/HACK/XXX/NotImplemented and skipped/xfail scans returned no matches.
- `git diff --check` passed.

## Claim validation

| Completion requirement | Result | Evidence |
|---|---|---|
| Acceptance criteria defined and met | PASS | `GOAL.md`, `IMPLEMENTATION_PACKET.md`, the Phase 5 design/plan, and the evidence table above. |
| Tests exist, run, and pass | PASS | Unit, integration, security, crash-recovery, CLI, persistence, and clean-wheel tests pass on both supported Python versions. |
| Coverage measured | PASS | The full suite reports 89% statement coverage; no threshold is claimed beyond the measured result. |
| No blocking scoped stubs or skipped tests | PASS | Scoped marker and skip scans returned no matches. |
| Independent review adjudicated | PASS | Every recommendation is classified above; accepted findings have regressions and pass. |
| Mutation boundary preserved | PASS | Only temporary synthetic renames and injected fake command runners were used. |
| Dirty-state truth preserved | PASS | Phase 5 feature commits are recorded; the review-hardening and acceptance commits remain pending at audit time. |

**Claim verdict: PASS** for “MW-400 Phase 5 local reversible-cleanup scope is complete.”

## Still open

1. Live installed-application permissions, real user Trash behavior, and live
   Homebrew/launchctl mutations are unproven and were intentionally not attempted.
2. MW-011 was later closed by hosted run `29641643615`; this Phase 5 audit's original
   local-only verdict remains historical evidence.
3. Public UV-tool/pipx installation, signing, and release artifacts remain Phase 7 work;
   Homebrew distribution is deferred by D-035.
4. One-command Codex setup, typed read-only local tools, and conversational integration
   remain Phase 6 work.
5. This audit does not claim malware detection, vulnerability absence, complete backup
   recoverability, exact-version Homebrew restoration, or production readiness.
