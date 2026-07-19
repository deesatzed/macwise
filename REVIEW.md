# REVIEW.md

## Review Scope

Adversarial review of the `GOAL_SIMPLE_UX.md` implementation diff: checkup models,
prioritization, terminal rendering, guided unknown-item and planning flows, score language,
tests, public documentation, and durable project state.

## Summary Judgment

Proceed. The post-review full gate, isolated final wheel, real-Mac checkup, all nine hosted CI
jobs, and user-supplied current desktop PDF inspection pass. The user explicitly waived the
separate mobile export after accepting the desktop page visually.

## Findings

| Severity | Category | Finding | Why It Matters | Required Fix |
|---|---|---|---|---|
| Important | UX | The first implementation ended after one priority. | A user would need another slow collection to review a second result. | Resolved: loop over priorities, reuse one audit, and finish only when the user enters `0`. |
| Important | Verification | The in-app browser was unavailable for three retries. | Longer first-run text could clip even when HTML contracts pass. | Resolved: the user opened the current page and supplied a desktop PDF; Poppler rendering and visual inspection found no clipping or overlap. The user explicitly waived a separate mobile export. |
| Minor | UX | Real aggregate output initially exceeded an ordinary terminal width. | Wrapped lines are easier to scan and avoid horizontal scrolling. | Resolved: renderer and regression test cap lines at 96 characters. |

## Correctness

The prioritizer is pure and deterministic, caps the summary at five supported domains, preserves
the audit collection timestamp, and reuses the same in-memory audit for guided follow-up. Plan
creation calls the existing typed planning service and never invokes apply.

## Security and Privacy

No network provider, telemetry, upload, shell execution, or new mutation adapter was added.
Unknown software remains unknown. The direct checkup is aggregate-only; item names appear only
after an interactive local choice. Existing planning, apply, and undo boundaries remain intact.

## Tests

New tests cover immutable models, allowed next commands, deterministic prioritization, bounded
output, fresh-evidence language, one-audit reuse, safe stop, unknown facts, session-only context,
plan preview, and score wording. The final full gate must be rerun after the review-loop fix.

## Maintainability

Collection, prioritization, and rendering remain separated. The command allowlist in the checkup
model prevents future priority cards from becoming arbitrary command suggestions.

## Performance

The guided loop reuses one audit and avoids repeated 18–20 second host collection. No additional
collectors or network calls were introduced.

## UI/UX Impact

The menu has one visibly recommended first step. Each card contains reason, evidence, possible
benefit, non-claim, and safest next action. Users can inspect multiple priorities, stop with `0`,
or create a non-applied plan preview from the unknown-item path.

## Regression Risk

Moderate CLI presentation risk; low collector/execution risk. Structured scan and score JSON
schemas are unchanged. Existing command names remain available.

## Scope Creep Check

No PyPI publication, GitHub Release, GitHub Pages deployment, Homebrew distribution, online
knowledge database, telemetry, GUI, or real cleanup action was added.

## Required Fixes Before Done

None. The full local gate, exact-wheel check, interactive safe-stop journey, push, hosted CI,
desktop PDF inspection, and explicit mobile-export waiver are recorded.

## Optional Improvements

- Revisit domain ranking with user research after release; the deterministic current ordering is
  safe but not yet validated as personalized priority.
- Add the deferred shared knowledge source in its separately approved later phase.
