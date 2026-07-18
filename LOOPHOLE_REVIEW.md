# LOOPHOLE_REVIEW.md

## Strategy Under Review

Phase 6 native Codex plugin, personal-marketplace setup, and eight strictly read-only
STDIO MCP tools described by D-031 and the approved design/implementation plan.

## Confidence Estimate Before Review

| Area | Confidence | Reason |
|---|---:|---|
| Read-only tool boundary | 82% | The design excludes mutation, but imports, plan access, or generic dispatch could accidentally reopen it. |
| MCP protocol/package | 78% | Official v1 SDK and plugin formats are current, but entry-point/PATH/version details need explicit proof. |
| Setup filesystem safety | 68% | Personal plugin and marketplace writes can collide with user-owned content or fail between replacements. |
| Privacy/prompt safety | 80% | Existing invariants are strong, but tool output creates a new model-facing boundary. |
| UX and distribution | 74% | One command is simple, but desktop process environments may not resolve `macwise`. |

## Loopholes Found

| Loophole | Severity | Why It Matters | Fix |
|---|---|---|---|
| A plain `command: macwise` depends on the Codex desktop process PATH. | High | pipx/Homebrew executables may work in a shell but be invisible to the desktop app. | During setup, personalize the installed `.mcp.json` with the resolved absolute current Python executable and `-m macwise codex serve`; validate the executable and test paths containing spaces. |
| `~/plugins/macwise` may already be user-owned or supplied by another marketplace. | Critical | Blind replacement could destroy unrelated work or hijack a same-name plugin. | Require a MacWise ownership marker plus matching manifest/repository for upgrades; refuse any unowned existing directory or foreign same-name marketplace source. |
| Replacing plugin and marketplace files is not one atomic transaction, and `codex plugin add` changes Codex-owned cache/config. | High | A crash could leave mismatched source/entry/cache state. | Stage and fsync both trees, keep bounded backups, replace in a documented order, verify with `codex plugin add --json`, and on failure restore sources then reinstall the prior owned version; fresh failed installs remove only the just-created selector. Persist no silent success claim if compensation fails. |
| PEP 440 `0.1.0a0` is not strict SemVer. | Medium | Plugin validation or cache behavior may reject or misread the Python package version. | Use a deterministic mapping (`0.1.0a0` to `0.1.0-alpha.0`) and test alignment rather than copying the string verbatim. |
| An active-plan preview could open/create or mutate planning state indirectly. | Critical | A read-only Codex tool must not create databases, revisions, approvals, or locks. | Build removal previews only in memory from the current audit and pure planning functions; never instantiate `PlanStore`, `ExecutionStore`, approval, revalidation, or execution services. |
| Re-running a full audit for every tool is slow and can produce internally inconsistent answers. | Medium | A conversation could compare different snapshots and repeatedly invoke expensive collectors. | Keep one process-local, lock-protected audit snapshot; `audit_mac(refresh=true)` refreshes explicitly, and all other tools read that snapshot. Never persist the cache. |
| `audit_mac` or list results can exceed model/tool limits and leak more local detail than needed. | High | Unbounded path-rich output harms privacy, reliability, and protocol framing. | Return bounded summaries, require pagination for lists, omit raw evidence blobs by default, include explicit truncation/continuation facts, and cap serialized tool results before returning. |
| Read-only MCP annotations are hints, not enforcement. | Critical | A client may ignore annotations. | Enforce the boundary in code, imports, schemas, and tests; annotations are defense-in-depth only. Reject generic dispatch and mutation-domain dependencies with AST/import tests. |
| FastMCP exceptions or logging can corrupt STDIO stdout. | High | One stray print can make every tool unusable. | Run protocol output alone on stdout, direct bounded diagnostics to stderr, convert expected domain failures to typed results, and verify a real subprocess session. |
| Prompt-shaped metadata can migrate from structured evidence into server/skill instructions. | High | A hostile app name could influence Codex behavior. | Keep server instructions static, neutralize human-facing controls, label all returned host values as evidence data, and run every hostile fixture through every tool family. |
| Setup tests could accidentally resolve the real home or Codex executable. | Critical | Tests might alter the operator's live installation. | Require explicit isolated home/payload/runner injection in every setup test, add a sentinel test that fails on the actual home, and never execute the default setup assembler in acceptance. |
| Official MCP v2 is approaching stable and may break v1 APIs. | Medium | An unconstrained install could change behavior after release. | Pin `mcp>=1.27,<2`, lock it, and treat v2 migration as a separate reviewed decision. |

## Revised Strategy

Keep D-031, with five mandatory refinements: an owned personal-plugin directory,
personalized absolute Python MCP launch command, in-memory lock-protected audit snapshot,
pure nonpersistent removal previews, and compensating setup rollback with truthful partial
failure. Tool annotations remain descriptive; code/import tests enforce read-only behavior.

## Confidence Estimate After Fixes

| Area | Confidence | Reason |
|---|---:|---|
| Read-only tool boundary | 93% | Pure projections, forbidden dependency tests, no state stores, and real protocol tests directly cover authority. |
| MCP protocol/package | 90% | Stable v1 pin, absolute runtime command, official validators, wheel and STDIO client proof cover the main drift points. |
| Setup filesystem safety | 88% | Ownership refusal, descriptor and ancestor checks, atomic staging, backups, and compensation reduce destructive failure modes. |
| Privacy/prompt safety | 91% | Bounded projections plus existing hostile fixtures and static instructions cover the new boundary. |
| UX and distribution | 88% | Personal marketplace discovery and an absolute runtime path avoid bespoke config and PATH assumptions. |

## Remaining Uncertainty

- A fake-Codex clean-home test cannot prove every internal cache/config behavior of future
  Codex builds.
- Crash consistency across multiple filesystem replacements cannot be perfectly atomic;
  setup must detect and repair owned interrupted state on rerun.
- Live installation into the operator's personal Codex host remains prohibited during
  local implementation and must not be claimed as verified.
- Hosted Codex/web plugin behavior is out of scope; Phase 6 proves the local Codex host.

## Proceed / Do Not Proceed Decision

Proceed with the revised strategy. Confidence is high enough for test-first local
implementation, provided every critical mitigation becomes a failing test before code.

## Required Verification

- AST/import and runtime sentinels prove no integration tool reaches mutation services or
  state stores.
- All eight tools pass schema, pagination, result-size, partial-evidence, and hostile-data
  tests.
- Official SDK client completes initialize/list/call against installed-wheel STDIO.
- Setup refuses unowned/conflicting paths and proves fresh/idempotent/upgrade/rollback/
  interrupted-repair flows in isolated homes.
- Plugin and both skill copies pass official validators.
- Python 3.12/3.13, Ruff, format, Pyright, build, privacy, and independent review gates pass.
