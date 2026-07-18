# Phase 6 Acceptance Audit

Date: 2026-07-18

Verdict: **PASS for MW-500 local Codex-integration scope.** MacWise ships a native
`macwise` plugin containing a novice-facing skill and exactly eight typed read-only
tools over STDIO MCP. `macwise setup codex` has compatibility preflight, ownership
checks, atomic replacement, semantic verification, compensation, and owned-state
recovery.

This does not prove a live personal install or model-quality outcome. Acceptance did
not modify the operator's Codex plugin state and did not run a hosted model session.

## Acceptance evidence

| Requirement | Verdict | Direct evidence | Honest limitation |
|---|---|---|---|
| Bundled `$macwise` experience | PASS | Canonical and packaged skills plus plugin manifest validate and ship in the wheel. | Workflow policy is scripted, not a live model evaluation. |
| One-command setup | PASS | Clean-home, update, idempotence, ownership, preservation, rollback, compatibility, semantic-result, and recovery tests pass. | No real personal Codex state was changed. |
| Typed local protocol | PASS | Strict contracts cover all eight closed operations; extra fields and hostile identities are refused. | Protocol schema is version 1. |
| Read-only boundary | PASS | No apply, undo, state-store, command-execution, or mutation tool is registered. | The separate CLI retains Phase 5 mutation paths. |
| Evidence honesty | PASS | Facts and unknowns remain distinct; missing size/startup/backup evidence forces `PARTIAL`. | Collector limitations can reduce completeness. |
| Installed artifact | PASS | Clean Python 3.12 wheel install launches STDIO, lists every tool, and calls `audit_mac`. | This proves transport/engine behavior, not model behavior. |
| Independent review | PASS | `REVIEW.md` resolves all four Important and one Minor findings. | Concurrent external marketplace writes are not simulated. |

## Fresh verification

- Python 3.12.11: 361 tests passed.
- Python 3.13.13: 361 tests passed.
- Ruff lint/format passed; Pyright reported 0 errors.
- `uv build` produced wheel and source distributions for `0.1.0a0`.
- Plugin validation and both skill validations passed.
- The clean-wheel proof made a real `audit_mac` JSON-RPC call.
- The repository privacy contract passed.

## Claim validation

**PASS** for “MW-500 Phase 6 local Codex integration is complete.” Hosted model
behavior, live personal setup, publication, hosted CI, and Phase 7 remain open.
