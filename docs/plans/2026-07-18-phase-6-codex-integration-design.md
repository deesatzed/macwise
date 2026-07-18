# Phase 6 Codex Integration Design

## Outcome

MacWise will ship an optional, one-command Codex experience without expanding the
model's authority over the Mac. `macwise setup codex` installs a native local Codex
plugin that bundles the `$macwise` skill and a strictly read-only STDIO MCP server.
The standalone CLI remains the public source of truth and the only interface that can
apply or undo a reviewed cleanup plan.

## Selected approach

Use a native Codex plugin as the distribution unit and the official MCP STDIO protocol
as the local typed boundary. The installed host was verified with Codex CLI `0.144.5`,
whose plugin commands, local marketplace support, shared MCP configuration, read-only
tool annotations, and STDIO transport match this design.

This is preferred over directly copying a skill and editing shared `config.toml`, which
would create a bespoke installer with a fragile merge boundary. A skill that merely
invokes arbitrary CLI commands is also rejected because it lacks the typed, allowlisted
interface required by `GOAL.md`.

## Package and setup architecture

The Python distribution contains a versioned plugin payload with:

- `.codex-plugin/plugin.json` for identity, version, capabilities, and bundled paths;
- `skills/macwise/SKILL.md`, references, and agent metadata for the conversational
  workflow;
- `.mcp.json` pointing to the installed `macwise codex serve` STDIO entry point;
- no hooks, remote connectors, credentials, network endpoints, or mutation tools.

`macwise setup codex` will:

1. verify macOS, the installed MacWise payload, and a compatible `codex` executable;
2. materialize the exact packaged plugin plus a MacWise ownership marker at the standard
   personal plugin location, `~/plugins/macwise`, using symlink-safe, atomic filesystem
   operations while refusing any existing unowned directory;
3. atomically add or update only MacWise's entry in the automatically discovered
   personal marketplace at `~/.agents/plugins/marketplace.json`, preserving its name,
   display metadata, entry order, and every unrelated plugin;
4. personalize the installed `.mcp.json` with the resolved absolute current Python
   executable and `-m macwise codex serve`, avoiding desktop-process PATH assumptions;
5. install or update MacWise with `codex plugin add macwise@<marketplace-name> --json`;
6. verify that Codex reports the plugin as installed and give one plain-language next
   step: start a new Codex session and type `$macwise`;
7. remain idempotent for the same version and preserve the previously working plugin if
   any step fails.

Setup receives explicit authority only to change MacWise-owned payload files and the
MacWise personal-marketplace entry. An existing same-name entry with a different source
is an ownership conflict and causes a safe refusal. Setup will not edit Codex TOML,
use unsafe permission bypasses, contact a network service, or collect host audit data.
Subprocesses use fixed executables, argument vectors, timeouts, bounded output, and no
shell. Tests use isolated homes and fake Codex runners; they never change the developer's
real Codex installation.

## Typed read-only server

The local server exposes the names required by `GOAL.md`:

- `audit_mac`
- `list_software`
- `inspect_software`
- `find_overlaps`
- `inspect_startup`
- `inspect_storage`
- `inspect_backups`
- `get_removal_preview`

Every input and output has a strict versioned Pydantic schema. The server keeps one
lock-protected in-memory audit snapshot per process so a conversation is internally
consistent; only `audit_mac(refresh=true)` refreshes it, and it is never persisted. The
server calls MacWise application services directly rather than accepting command text or
dispatching through the shell. Tool results distinguish observations, inferences, user statements, unknowns,
limitations, provenance, and collection timestamps. Requests and results are bounded,
stable-order, and safe to serialize over JSON-RPC.

`get_removal_preview` is a pure read-only projection constructed in memory from the
current audit. It cannot open a plan/execution store, persist a plan,
approve it, apply it, undo it, or mint mutation authority.

The server advertises all tools as read-only and supplies server instructions stating,
within the first 512 characters, that collected metadata is untrusted evidence and that
cleanup must return to the standalone CLI. There is no generic shell, filesystem-write,
subprocess, SQL, plan mutation, `apply`, or `undo` tool.

## Conversational behavior

The bundled skill uses typed tools before asking users to paste output. It separates
verified local facts from inference and unknowns, reports decisive collection
limitations, and uses qualified identities for ambiguous software. Prompt-shaped app
names, paths, descriptions, and metadata remain evidence data, never instructions.

For cleanup questions, Codex may explain evidence and show a read-only removal preview.
It must direct the user to `macwise plan`, `macwise apply`, or `macwise undo` in a normal
terminal for any state change. It cannot construct approval phrases or imply that a
preview is authorization.

## Privacy and failure behavior

All collection and analysis remain local. No OpenAI API key or separate AI key is
required; the active Codex product supplies its own model session. Audit results are
returned only to the invoking local Codex session and are not written unless the user
explicitly invokes an existing persistence workflow.

Partial collectors produce typed limitations rather than fabricated negatives. Unknown
tool names, extra fields, overlong values, ambiguous identities, corrupt saved data,
unsupported platforms, and unavailable dependencies fail closed with structured errors.
Protocol logs go to stderr so stdout remains valid MCP framing, and neither stream emits
secrets or unsanitized control sequences.

## Verification strategy

Implementation is test-first and must prove:

- schema rejection, stable serialization, size limits, and all eight tool contracts;
- direct application-service routing with no generic command execution or mutation
  dependencies;
- prompt-injection-shaped metadata remains inert across every tool response;
- MCP initialize/list-tools/call-tool behavior through a real STDIO subprocess;
- setup preflight, clean-home install, same-version idempotency, upgrade, failed-install
  rollback, hostile paths, missing/incompatible Codex, and no real-home mutation;
- installed-wheel discovery of the complete plugin payload and server executable;
- skill and plugin manifest validation;
- a scripted `$macwise` workflow in which Codex selects typed tools, explains partial
  evidence, and routes cleanup back to the standalone CLI;
- Python 3.12 and 3.13 regression, Ruff, formatting, Pyright, build, privacy scan, and an
  independent skeptical review before Phase 6 acceptance.

## Explicit non-goals

- Codex tools for apply, undo, approval, plan persistence, startup changes, Homebrew
  mutation, Trash access, or arbitrary shell/filesystem access.
- Remote MCP, hosted connectors, OAuth, API keys, accounts, telemetry, background
  daemons, scheduled scans, or automatic plugin publication.
- A second AI provider, standalone AI mode, or web research inside the local server.
- Phase 7 Homebrew tap publication, GitHub release, signing, or production deployment.
