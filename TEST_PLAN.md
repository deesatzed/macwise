# Phase 5 Execution Test Plan

## Behavior Changed

Phase 5 adds schema-2 ordered cleanup actions, exact approval phrases, fresh revalidation,
append-only execution manifests, allowlisted Trash/Homebrew/current-user startup actions,
post-action verification, reverse-order undo, and `apply` / `undo` CLI recovery UX.

## Existing Test Coverage

The final 292-test suite covers model and store integrity, exact approval parsing, shared
locking, stale-policy revalidation, exclusive synthetic Trash moves, fake command argv and
environment boundaries, formula/cask/service/LaunchAgent coordination, prepared-token
substitution, action verification failure, undo failure, CLI approval, and help/recovery views.

## Review Gaps Closed

| Test Type | Scenario | Resolution | Priority |
|---|---|---|---|
| Security regression | A command or filesystem adapter fails after invocation and the run remains unresolved, never safely `failed` | Fresh failed-state observation plus partial/verification-failed recovery tests pass. | Critical |
| Security regression | LaunchAgent plist content changes between preparation and command dispatch | Exact descriptor-read plist digest is rechecked before dispatch. | Critical |
| Integration | Multi-action failure stops later actions and preserves earlier verified actions as partial | Stop-first-failure and reverse recovery tests pass. | Critical |
| Integration | Reverse undo order remains exact when three action classes coexist | Trash/startup and service/package ordering regressions pass. | High |
| Security regression | Same approval fingerprint cannot authorize a changed full plan digest | Full active digest binding and prepared-action substitution tests pass. | Critical |
| Security regression | Plan and execution DB tampering, future schema, and symlink ancestors refuse through CLI without raw errors | Store/security/public-boundary regressions pass. | High |
| Security regression | External/manual application roots outside the live adapter allowlist refuse before approval | CLI preparation rejects external roots before journaling. | High |
| Crash semantics | Classify interrupted apply/undo from fresh command and Trash evidence | Unchanged/applied paths recover; ambiguity remains interrupted. | High |
| CLI regression | Partial, verification-failed, interrupted, and undo-partial states give bounded recovery guidance | Undo and doctor recovery views are covered. | High |
| Boundary regression | Global subprocess mutation spy proves tests only use synthetic rename or injected runners | Security test enumerates synthetic/fake mutation only. | Critical |

## Edge Cases

- Control, newline, bidi, SQL-shaped, flag-shaped, and null-containing identities.
- Destination replacement, source inode replacement, symlink ancestors, cross-device Trash.
- LaunchAgent disabled-but-running prior state and unchanged-hash undo.
- Homebrew output overflow, timeout, missing executable, nonzero exit, and verification mismatch.
- Approval whitespace, case, prefix, suffix, replay, and full-digest mismatch.

## Regression Tests

- Preserve every existing Phase 1-4 read-only and planning assertion.
- Keep synthetic filesystem mutations under pytest temporary roots only.
- Keep every Homebrew and launchctl mutation behind recording fake runners.
- Keep plan display read-only and state-store reads non-initializing.

## Manual Smoke Tests

- Render root, plan, apply, and undo help from the built wheel.
- Install the wheel into a fresh Python 3.12 environment.
- Run schema-2 planning and synthetic bundle apply/verify/undo under `/private/tmp`.
- Run fake Homebrew and startup commands only; do not touch live package or launch state.

## Commands To Run

| Purpose | Command | Expected Result |
|---|---|---|
| Security focus | `uv run pytest -q tests/security/test_execution_safety.py tests/execution tests/services/test_execution_commands.py` | All adversarial tests pass without live mutation |
| Python 3.12 | `uv run --python 3.12 --frozen pytest -q` | Full suite passes |
| Python 3.13 | `uv run --python 3.13 --frozen pytest -q` | Full suite passes |
| Static quality | `uv run --frozen ruff check . && uv run --frozen ruff format --check . && uv run --frozen pyright` | No findings |
| Packaging | `uv build` | Wheel and sdist build |
| Repository | `uv run --frozen pytest -q tests/repository && git diff --check` | Contracts and whitespace pass |

## Coverage Gaps Accepted For Now

- No real installed application, real user Trash, live Homebrew mutation, or live launchctl
  mutation will be exercised locally without explicit authority.
- Hosted CI and public artifact/tap behavior remain external acceptance gates.
- Homebrew undo cannot prove restoration of an unavailable captured version and remains
  explicitly best-effort.
- A 16-character approval fingerprint is a consent UX identifier rather than a secret;
  full active digests are checked internally, but the displayed 64-bit prefix has a
  theoretical collision limit.

## Done Criteria

All critical and high-priority local tests above pass on Python 3.12 and 3.13; independent
review findings are adjudicated; help/build/clean-wheel smokes pass; `PROGRESS.md`, the threat
model, and Phase 5 acceptance record only verified local evidence and explicit limitations.
