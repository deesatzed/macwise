# Phase 6 Independent Review Adjudication

Date: 2026-07-18

Verdict: **Accepted after fixes.** The independent review initially returned Needs Fixes
with four Important findings and one Minor disclosure finding. Each was accepted and
resolved test-first; none was rejected.

| Finding | Classification | Resolution |
|---|---|---|
| No compatibility preflight before writes | Accepted / Resolved | Setup verifies CLI identity and add/remove JSON capabilities before creating managed directories. |
| Interrupted stage/backup state was not recovered | Accepted / Resolved | Reruns validate complete marker-owned transaction trees, restore the prior backup, remove owned staging state, and refuse ambiguous state. |
| Any nonempty JSON was treated as success | Accepted / Resolved | Add/remove require exact positive booleans; a separate plugin-list query must match selector, version, and installed state. |
| Missing software size was encoded as fact | Accepted / Resolved | Missing size is an explicit `Unknown`, the false fact is omitted, and status is `PARTIAL`. |
| Setup disclosure omitted Codex registration | Accepted / Resolved | Help describes registration add/update and rollback restoration/removal. |

Self-review also added matching-manifest ownership and fresh compensation-order
regressions. The installed-wheel test now calls `audit_mac` over real STDIO JSON-RPC.

Remaining boundaries: no live personal plugin installation or model-driven Codex
session was run, and concurrent third-party marketplace modification is not simulated.

## Phase 7 release-readiness adjudication

The release-readiness and adversarial self-review found four Important candidate gaps;
all were accepted and resolved before the final matrix:

| Finding | Resolution |
|---|---|
| The default sdist included tests, planning controls, and the formula itself, making the formula hash drift and exposing non-runtime files. | The sdist now has an explicit minimal public include set; artifact-content and formula-hash tests rebuild it. |
| The first Homebrew dependency-closure check ignored optional extras, omitting the MCP JWT crypto chain. | The checker traverses requested extras and the formula now includes cryptography, cffi, and pycparser with locked URLs/hashes. |
| Release workflow used an unpinned ephemeral Twine tool. | Twine is a constrained locked development dependency and the workflow invokes it through `uv --frozen`. |
| Python 3.13 coverage exposed unclosed SQLite inspection connections in tests. | Test connections now combine transaction and explicit closing contexts; the focused suite passes with ResourceWarnings fatal. |

No Critical/Important local candidate finding remains open. External Homebrew build
behavior, hosted workflows, publisher/tap configuration, and public install commands
remain blocking evidence gaps rather than accepted passes.
