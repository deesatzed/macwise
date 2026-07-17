# RANKED_OPTIONS.md

## Decision Needed

How should MacWise implement the full Phase 5 apply/verify/undo contract without turning
persisted preview data into a generic mutation mechanism?

## Goal Being Optimized

Deliver the complete local Phase 5 scope with the highest probability of preserving
exact approval, user data, crash truth, reversibility, testability, and the existing
public CLI contract.

## Options

| Rank | Option | Estimated Chance of Achieving Goal | Why | Main Risk | When To Choose |
|---:|---|---:|---|---|---|
| 1 | Staged typed coordinator with separate Trash, Homebrew, and startup adapters plus append-only manifests | 84% | Reuses current strict models/persistence patterns, keeps every mutator narrow, and supports test-first vertical slices while still completing all Phase 5 deliverables. | Cross-adapter state, crash recovery, and plan-schema evolution remain complex. | Choose for this repository and implement one verified adapter slice at a time. |
| 2 | Trash-only execution engine now; defer Homebrew and startup | 58% | Smallest and safest useful mutation slice and directly proves the required manual-app journey. | Does not fulfill the explicit Phase 5 Homebrew/startup contract and would make a partial slice look complete. | Choose only if the full goal is explicitly narrowed. |
| 3 | One generic command/action engine driven by persisted argv | 34% | Less code and superficially extensible across all action kinds. | Persisted hostile/stale values become execution authority; allowlists and recovery semantics become easy to bypass. | Choose only for a trusted internal automation system, not MacWise. |
| 4 | Shell/Finder/Homebrew scripts with log-file rollback | 18% | Quick to prototype and easy to demo manually. | Shell injection, weak typing, incomplete crash truth, untestable privilege prompts, and unreliable undo violate core standards. | Do not choose. |

## Recommended Option

Choose option 1, but enforce staged acceptance inside Phase 5: models and journal first,
then Trash, Homebrew, supported startup, CLI, adversarial review, and only then a bounded
Phase 5 verdict. Each adapter remains unusable until its exact revalidation, manifest,
verification, and undo tests pass.

## Why Not The Others

Option 2 is a useful internal checkpoint but cannot be the Phase 5 completion claim.
Option 3 conflicts with the accepted invariant that persisted intent is inert and must be
reconstructed. Option 4 violates the no-shell, explicit recovery, and tests-arbitrate
contracts.

## Confidence Level

Moderate-high (84%). The repository already proves strict models, append-only SQLite,
exact resolution, safe argv construction, and adversarial review. Confidence is below
90% because real mutation introduces TOCTOU, partial-action, Homebrew behavior, and
startup-state uncertainty that must be addressed in isolated tests and review.

## Evidence Used

- `GOAL.md` Phase 5 and end-to-end user journey.
- Accepted Phase 4 plan models, persistence, preflight, and review findings.
- `STANDARDS.md` mutation, user-data, shell, testing, and approval boundaries.
- Existing read-command adapter and collector injection patterns.
- `docs/phase-4-acceptance.md` verified local state and open action gates.

## Assumptions

- Synthetic same-filesystem bundle moves inside a canonical temporary root are allowed
  during tests; installed applications and the real Trash are not.
- Homebrew and launchctl mutators can be fully tested with injected runners and exact
  argv assertions without changing live state.
- Phase 5 may add plan schema 2 while preserving read-only access to schema-1 history.
- No privilege elevation or production deployment is authorized.

## Decision To Record

D-029 records dedicated allowlisted adapters; D-027 records append-only execution
manifests; the Phase 5 design records the staged implementation order.
