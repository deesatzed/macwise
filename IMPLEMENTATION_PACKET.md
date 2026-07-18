# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Implement MW-500 Phase 6: strict typed read-only integration models, an in-memory MacWise
review facade, eight STDIO MCP tools, a bundled native `$macwise` plugin, and safe
idempotent `macwise setup codex` installation.

## Actual User Goal

Give ordinary Mac users a one-command optional Codex experience that can inspect and
explain the same local evidence as the standalone CLI without requiring users to
understand plugins or MCP. Preserve the public CLI as source of truth and ensure the
model cannot apply, undo, approve, persist, or otherwise perform cleanup.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `pyproject.toml`, `uv.lock` | Pin stable `mcp>=1.27,<2`; package plugin payload | High: dependency/API and wheel-content drift |
| `src/macwise/integration/models.py` | Strict versioned request/result schemas and bounds | High: ambiguous or oversized model-facing data |
| `src/macwise/integration/service.py` | Lock-protected in-memory audit snapshot and eight pure projections | Critical: accidental state/mutation authority or false claims |
| `src/macwise/integration/server.py` | Explicit read-only FastMCP tools over clean STDIO | Critical: protocol corruption or hidden generic dispatch |
| `src/macwise/integration/setup.py` | Owned personal-plugin and marketplace installation/rollback | Critical: overwrite, symlink, crash, or foreign ownership risk |
| `src/macwise/codex_payload/macwise/` | Native plugin manifest, `.mcp.json`, skill, references | High: invalid package or overbroad capability claim |
| `skills/macwise/` | Canonical read-only typed-tool workflow | High: prompt injection or unsafe cleanup instructions |
| `src/macwise/cli.py`, `src/macwise/help_text.py` | Real setup UX and hidden STDIO entry point | High: misleading success or exposed internals |
| `tests/integration/`, `tests/security/`, `tests/repository/`, `tests/cli/` | TDD, clean-home, protocol, wheel, hostile-data, and boundary proof | Critical: tests must never touch live home/config/mutators |
| `README.md`, `CHANGELOG.md`, `docs/privacy.md`, `docs/threat-model.md` | User setup/privacy/safety truth | Medium: claims broader than evidence |
| `DECISIONS.md`, `PROGRESS.md`, `TASK_QUEUE.md`, `docs/phase-6-acceptance.md` | Review and acceptance continuity | Medium: false completion claim |

## Existing Patterns To Follow

- Strict frozen Pydantic models with `extra="forbid"`, explicit schema versions, stable
  ordering, and immutable raw evidence.
- Injected collectors/runners/services, fixed executable vectors, `shell=False`, bounded
  output/time/environment, and structured failures.
- Exact qualified identity matching, evidence-basis findings, and missing-evidence
  limitations rather than fabricated negatives.
- Unicode/control neutralization for human/model-facing structure while host values remain
  inert data.
- Symlink/ancestor/regular-file validation and atomic append/replace patterns from plan
  and execution persistence.
- Red test, observed intended failure, minimal implementation, focused green, regression,
  logical commit.

## Assumptions

- D-031 and the approved Phase 6 design authorize a native plugin plus local STDIO MCP,
  not remote tools or mutation authority.
- Official MCP Python SDK v1.27 is current stable; `<2` is required because v2 is a
  breaking line nearing stable release.
- Codex CLI 0.144.5 supports `plugin add/remove --json`, automatic discovery of the
  default personal marketplace, bundled MCP server configuration, and STDIO.
- The installed plugin can reliably launch the current package using the resolved
  absolute `sys.executable -m macwise codex serve`, including paths with spaces.
- Setup may create/update only an owned `~/plugins/macwise` directory and MacWise entry
  in `~/.agents/plugins/marketplace.json`; any foreign conflict is a refusal.
- A process-local audit snapshot is sufficient for conversational consistency and needs
  no disk persistence.

## Non-Goals For This Pass

- Apply, undo, approval, plan/execution persistence, startup/Homebrew/Trash mutation, or
  any generic shell/filesystem/SQL tool in Codex.
- Remote MCP, OAuth, API keys, accounts, telemetry, hosted connectors, background scans,
  scheduling, or automatic public plugin publication.
- Live setup against the developer's actual personal home/Codex host.
- Phase 7 Homebrew tap, GitHub release, signing, production deployment, or hosted CI proof.
- Standalone AI providers or deterministic claims about model wording.

## Step-by-Step Plan

1. Add failing strict integration-model tests; pin SDK and implement contracts.
2. Add failing audit/list/inspect tests; implement cached read-only facade.
3. Add remaining operation and forbidden-dependency tests; implement pure projections.
4. Add real SDK client protocol tests; implement explicit FastMCP server.
5. Add artifact tests; scaffold/complete/validate the plugin and packaged skill.
6. Add clean-home/hostile/rollback setup tests; implement owned atomic setup.
7. Add CLI/help tests; wire real setup and hidden server entry point.
8. Add hostile-data, workflow, installed-wheel, privacy, and threat-model proof.
9. Run adversarial review, fix accepted findings test-first, and execute full acceptance.

Exact test names, commands, commits, rollback, and stop rules are in
`docs/plans/2026-07-18-phase-6-codex-integration.md`. The revised risk strategy is in
`LOOPHOLE_REVIEW.md`.

## Acceptance Criteria

- Exactly eight explicit tools exist and all advertise/read-enforce read-only,
  non-destructive, idempotent, closed-world behavior.
- No integration module imports/instantiates mutation adapters, approval, execution,
  revalidation, `PlanStore`, or `ExecutionStore`; removal preview is pure and in memory.
- Requests/results are strict, bounded, stable, paginated where needed, evidence-shaped,
  and truthful under ambiguity/partial collection.
- One process-local snapshot keeps tool answers consistent; explicit audit refresh is the
  only recollection path and no integration result is persisted.
- Real STDIO initialize/list/call succeeds through the official SDK without stdout noise.
- Plugin payload and both skill copies validate, are included in the wheel, and use a
  strict SemVer mapped from the Python package version.
- Setup preserves unrelated marketplace data, refuses foreign/unowned paths, uses an
  absolute runtime command, is idempotent, and reports/repairs or truthfully exposes
  interrupted rollback in isolated homes.
- `$macwise` workflow proof uses typed tools, separates facts/inference/unknowns, and
  directs all cleanup to standalone CLI.
- Python 3.12/3.13 full suites, Ruff, format, Pyright, build, privacy scan, installed-wheel
  protocol, validators, and independent review pass before MW-500 is marked done.

## Verification Plan

- Focused red/green commands per each of the nine tasks in the implementation plan.
- Official plugin validator and both canonical/packaged skill validators.
- AST/import/runtime mutation-boundary tests and all hostile metadata fixtures.
- SDK client against local and installed-wheel STDIO subprocesses.
- Clean temporary HOME setup matrix with fake Codex executable and real filesystem
  replacement/rollback; sentinel forbids the actual home.
- Full Python 3.12/3.13 pytest, Ruff, formatting, Pyright, build, wheel install, privacy,
  workflow-YAML parse, and skeptical review.

## Rollback Plan

- Revert only the logical Phase 6 commit that introduced a failed slice.
- Never reset unrelated work or run setup against live personal paths.
- Setup itself stages and fsyncs new content, keeps bounded prior owned copies until Codex
  verification, restores them on failure, and reinstalls the prior selector when needed.
- Fresh failed installs remove only the just-created MacWise selector/content. Failed
  compensation returns interrupted recovery guidance rather than success.

## Risks

| Risk | Mitigation |
|---|---|
| Model reaches cleanup authority | Explicit tools only; forbidden import/store tests; no generic dispatcher; pure preview |
| Foreign plugin/data overwrite | Ownership marker, repository/manifest match, exact marketplace source, fail closed |
| Multi-file crash mismatch | Staging, fsync, bounded backups, ordered replace, rerun repair, compensating Codex command |
| Desktop cannot find executable | Absolute validated current Python plus `-m macwise` in installed `.mcp.json` |
| MCP v2 breaks APIs | `mcp>=1.27,<2` plus lockfile and protocol tests |
| Protocol stdout corruption | No prints/logs to stdout; real subprocess initialize/list/call proof |
| Excessive/private output | Bounded projections, pagination, no raw blobs by default, serialized cap |
| Prompt injection | Static instructions; host data labeled inert; hostile fixtures across tools |
| Tests touch real home | Explicit isolated injection and actual-home sentinel; no default setup smoke |
| Claims exceed proof | Requirement-mapped Phase 6 acceptance with explicit local/live/hosted limitations |

## Proceed / Block Decision

Proceed. The architecture is approved, official current protocol/package surfaces were
verified, the loophole review raised confidence to a locally implementable level, and no
credential, destructive live action, production deployment, or legal blocker is needed.
