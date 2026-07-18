# Phase 6 Codex Integration Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship an optional one-command `$macwise` Codex plugin with eight strictly read-only typed local tools and no model-accessible mutation authority.

**Architecture:** Add strict integration schemas and a read-only application facade over existing MacWise services, then expose that facade with the official MCP Python SDK over STDIO. Package the skill and MCP configuration as a native Codex plugin; an idempotent setup service installs only MacWise-owned personal-plugin files and marketplace metadata before asking Codex to install the plugin.

**Tech Stack:** Python 3.12+, Pydantic v2, `mcp>=1.27,<2` FastMCP, Typer, pytest, uv, Hatchling, native Codex plugin manifests and personal marketplace.

---

## Governing constraints

- Follow `GOAL.md`, `STANDARDS.md`, D-004, D-005, D-018, D-019, D-024 through D-031, and `docs/plans/2026-07-18-phase-6-codex-integration-design.md`.
- Use @test-driven-development for every behavior change and @verification-before-completion before any completion claim.
- Use @plugin-creator for the initial manifest scaffold and validation. Do not hand-invent unsupported manifest fields.
- No tool may import execution adapters/services, mutate a plan, write state, invoke a shell, accept arbitrary paths/commands, or expose apply/undo/approval.
- Never run setup against the developer's actual home or install the development plugin into the active Codex host. All setup tests use isolated homes and fake runners.
- Keep MCP protocol stdout clean; diagnostics belong on stderr and must be bounded/sanitized.
- Commit after each coherent green task. Do not stage unrelated user changes.

### Task 1: Pin the stable MCP SDK and define strict integration contracts

**Files:**
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Create: `src/macwise/integration/__init__.py`
- Create: `src/macwise/integration/models.py`
- Create: `tests/integration/test_models.py`

**Step 1: Write failing schema tests**

Test all request models with `extra="forbid"`, bounded strings/page sizes, qualified
identity syntax, stable defaults, and all response envelopes with schema version 1.
Include rejection of extra fields, empty names, control-only names, traversal-shaped
scope values, and over-limit page sizes.

```python
def test_inspect_request_is_strict_and_bounded() -> None:
    request = InspectSoftwareRequest(identity="cask:visual-studio-code")
    assert request.schema_version == 1
    with pytest.raises(ValidationError):
        InspectSoftwareRequest.model_validate({"identity": "x", "command": "rm"})


def test_tool_result_keeps_facts_and_limitations_separate() -> None:
    result = ToolResult(operation="inspect_software", limitations=("Usage unavailable.",))
    assert result.facts == ()
    assert result.limitations == ("Usage unavailable.",)
```

Define strict models for `AuditMacRequest`, `ListSoftwareRequest`,
`InspectSoftwareRequest`, `FindOverlapsRequest`, `InspectStartupRequest`,
`InspectStorageRequest`, `InspectBackupsRequest`, and `RemovalPreviewRequest`, plus
bounded `Fact`, `Unknown`, `ToolError`, `SoftwareSummary`, and `ToolResult` response
records. Use enums for operation/scope/status rather than free-form dispatch strings.

**Step 2: Run the tests and observe the intended failure**

Run: `uv run pytest tests/integration/test_models.py -q`

Expected: FAIL because `macwise.integration.models` does not exist.

**Step 3: Add the stable SDK dependency and minimal contracts**

Add `mcp>=1.27,<2` to project dependencies and run `uv lock`. The upper bound is
mandatory because the official SDK documents v1 as current stable and v2 as a breaking
line. Implement frozen strict Pydantic models, field length/page bounds, and a shared
`schema_version: Literal[1] = 1`.

```python
class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class InspectSoftwareRequest(StrictModel):
    schema_version: Literal[1] = 1
    identity: str = Field(min_length=1, max_length=256)
```

**Step 4: Run focused quality gates**

Run:

```bash
uv run pytest tests/integration/test_models.py -q
uv run ruff check src/macwise/integration tests/integration/test_models.py
uv run pyright src/macwise/integration tests/integration/test_models.py
```

Expected: PASS.

**Step 5: Commit**

```bash
git add pyproject.toml uv.lock src/macwise/integration tests/integration/test_models.py
git commit -m "feat: define read-only Codex tool contracts"
```

### Task 2: Build the read-only audit, list, and inspect facade

**Files:**
- Create: `src/macwise/integration/service.py`
- Create: `tests/integration/test_read_service.py`
- Modify: `src/macwise/integration/__init__.py`

**Step 1: Write failing facade tests**

Use synthetic `AuditDocument` fixtures and injected `AuditProvider`/`PlanPreviewProvider`
protocols. Prove `audit_mac`, `list_software`, and `inspect_software` return stable,
bounded structured results; ambiguous identities return typed errors; missing evidence
returns unknowns/limitations rather than negative claims.

```python
def test_inspect_refuses_ambiguous_unqualified_identity(audit: AuditDocument) -> None:
    service = CodexReadService(audit_provider=lambda: audit_with_duplicate_name(audit))
    result = service.inspect_software(InspectSoftwareRequest(identity="Code"))
    assert result.status is ToolStatus.REFUSED
    assert result.errors[0].code == "ambiguous_identity"
```

Also monkeypatch mutation service constructors to raise if imported/called. Inspect the
module dependency surface so a future accidental import of `macwise.execution`,
`ExecutionService`, or approval helpers fails a security test.

**Step 2: Verify red**

Run: `uv run pytest tests/integration/test_read_service.py -q`

Expected: FAIL because `CodexReadService` does not exist.

**Step 3: Implement the minimal pure facade**

Create a `CodexReadService` with an injected audit callable and a lock-protected,
process-local snapshot. `audit_mac(refresh=true)` is the only refresh path; every other
operation reads the same snapshot. Use existing normalized audit records and analysis,
never rendered terminal text. Centralize exact identity resolution, stable sorting,
pagination, fact/unknown conversion, decisive collector limitations, and serialized
result-size enforcement.

```python
class AuditProvider(Protocol):
    def __call__(self) -> AuditDocument: ...


@dataclass(frozen=True, slots=True)
class CodexReadService:
    audit_provider: AuditProvider

    def inspect_software(self, request: InspectSoftwareRequest) -> ToolResult:
        audit = self.audit_provider()
        match = resolve_exact_identity(audit.software, request.identity)
        if isinstance(match, ToolError):
            return refused_result(Operation.INSPECT_SOFTWARE, match)
        return software_detail_result(match, audit)
```

Do not persist the audit from this service. Default host assembly may run `AuditService`
with the same standard roots used by the CLI; tests inject a provider.

**Step 4: Verify focused and regression behavior**

Run:

```bash
uv run pytest tests/integration/test_read_service.py tests/services/test_audit_service.py -q
uv run ruff check src/macwise/integration tests/integration
uv run pyright src/macwise/integration tests/integration
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/macwise/integration tests/integration/test_read_service.py
git commit -m "feat: add read-only Codex audit facade"
```

### Task 3: Complete overlap, startup, storage, backup, and removal-preview tools

**Files:**
- Modify: `src/macwise/integration/models.py`
- Modify: `src/macwise/integration/service.py`
- Modify: `tests/integration/test_read_service.py`
- Create: `tests/security/test_codex_read_boundary.py`

**Step 1: Write failing tests for the remaining five operations**

Cover exact role-aware overlap relations, startup evidence/ownership ambiguity, storage
mount facts without unsafe free-form paths, backup limitations without coverage claims,
and an in-memory removal preview from pure planning functions. Prove no call opens or
writes `macwise.db`, changes the active plan, creates an execution
journal, or touches synthetic host targets.

```python
def test_removal_preview_never_persists_or_approves(tmp_path: Path) -> None:
    service = CodexReadService(audit_provider=fixed_audit)
    result = service.get_removal_preview(RemovalPreviewRequest(identity="app:com.example.App"))
    assert result.status is ToolStatus.OK
    assert not list(tmp_path.iterdir())
    assert "apply" not in result.model_dump_json().casefold()
```

Add an AST/import boundary test that rejects imports from `macwise.execution`,
`macwise.services.execution`, `macwise.services.approval`, and write methods on
`PlanStore`/`ExecutionStore` anywhere under `src/macwise/integration`.

**Step 2: Verify red**

Run:

```bash
uv run pytest tests/integration/test_read_service.py tests/security/test_codex_read_boundary.py -q
```

Expected: FAIL on unimplemented operations/boundary.

**Step 3: Implement the remaining projections**

Reuse `AuditDocument.overlaps`, startup, volumes, backup, evidence-basis findings, and
the pure planning service. Return only bounded summaries and identifiers. A preview must
say that it is not approval and must route state changes to the standalone CLI, but it
must never emit an approval fingerprint or phrase.

**Step 4: Run focused gates**

Run:

```bash
uv run pytest tests/integration/test_read_service.py tests/security/test_codex_read_boundary.py -q
uv run pytest tests/services/test_overlap_analysis.py tests/services/test_planning.py -q
uv run ruff check src/macwise/integration tests/integration tests/security/test_codex_read_boundary.py
uv run pyright src/macwise/integration tests/integration tests/security/test_codex_read_boundary.py
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/macwise/integration tests/integration/test_read_service.py tests/security/test_codex_read_boundary.py
git commit -m "feat: complete read-only Codex review operations"
```

### Task 4: Expose the facade through a read-only FastMCP STDIO server

**Files:**
- Create: `src/macwise/integration/server.py`
- Create: `tests/integration/test_mcp_server.py`
- Modify: `src/macwise/integration/__init__.py`

**Step 1: Write failing in-process and subprocess protocol tests**

Assert the exact eight names, strict JSON schemas, structured output, and annotations:
`readOnlyHint=True`, `destructiveHint=False`, `idempotentHint=True`, and
`openWorldHint=False`. Check that server instructions begin with the untrusted-evidence
and no-mutation boundary. Use the official SDK client over a real STDIO child process to
initialize, list tools, and call a deterministic injected/test-mode tool.

```python
READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


async def test_stdio_lists_only_read_only_tools(server_command: list[str]) -> None:
    async with stdio_client(StdioServerParameters(command=server_command[0], args=server_command[1:])) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            listed = await session.list_tools()
    assert {tool.name for tool in listed.tools} == EXPECTED_TOOL_NAMES
    assert all(tool.annotations and tool.annotations.readOnlyHint for tool in listed.tools)
```

**Step 2: Verify red**

Run: `uv run pytest tests/integration/test_mcp_server.py -q`

Expected: FAIL because the server factory does not exist.

**Step 3: Implement server factory and runner**

Create `create_server(service: CodexReadService) -> FastMCP` and register explicit
decorated functions, not a dynamic arbitrary dispatcher. Use Pydantic returns and
`structured_output=True`.

```python
def create_server(service: CodexReadService) -> FastMCP:
    server = FastMCP("MacWise", instructions=SERVER_INSTRUCTIONS, log_level="ERROR")

    @server.tool(annotations=READ_ONLY, structured_output=True)
    def inspect_software(request: InspectSoftwareRequest) -> ToolResult:
        return service.inspect_software(request)

    # Register the other seven explicit functions.
    return server


def run_stdio() -> None:
    create_server(build_default_read_service()).run(transport="stdio")
```

No stdout logging or exception traceback may corrupt framing. Convert expected domain
failures to typed `ToolResult`; reserve transport errors for protocol failures.

**Step 4: Verify protocol and quality**

Run:

```bash
uv run pytest tests/integration/test_mcp_server.py -q
uv run ruff check src/macwise/integration tests/integration
uv run pyright src/macwise/integration tests/integration
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/macwise/integration tests/integration/test_mcp_server.py
git commit -m "feat: serve MacWise read-only tools over MCP"
```

### Task 5: Scaffold and complete the native Codex plugin payload

**Files:**
- Create: `src/macwise/codex_payload/macwise/.codex-plugin/plugin.json`
- Create: `src/macwise/codex_payload/macwise/.mcp.json`
- Create: `src/macwise/codex_payload/macwise/skills/macwise/SKILL.md`
- Create: `src/macwise/codex_payload/macwise/skills/macwise/agents/openai.yaml`
- Create: `src/macwise/codex_payload/macwise/skills/macwise/references/evidence-boundary.md`
- Modify: `skills/macwise/SKILL.md`
- Modify: `skills/macwise/agents/openai.yaml`
- Modify: `pyproject.toml`
- Create: `tests/repository/test_codex_plugin.py`

**Step 1: Write failing artifact tests**

Assert outer folder/manifest name equality, deterministic PEP-440-to-strict-SemVer
mapping (`0.1.0a0` to `0.1.0-alpha.0`), MIT metadata, `skills` and
`mcpServers` paths, read-only capability wording, actual companion files, exact STDIO
command/args, no hooks/apps/remote URLs, no TODOs, and byte-identical canonical skill
content between the authoring and packaged copies.

**Step 2: Verify red**

Run: `uv run pytest tests/repository/test_codex_plugin.py -q`

Expected: FAIL because the payload does not exist.

**Step 3: Generate the required scaffold with @plugin-creator**

Run the provided generator once, without a repo marketplace:

```bash
python3 /Users/o2satz/.codex/skills/.system/plugin-creator/scripts/create_basic_plugin.py \
  macwise --path src/macwise/codex_payload --with-skills --with-mcp
```

Then use `apply_patch` to replace scaffold defaults with final MacWise metadata and
content. The manifest contains `name`, package-aligned strict semver, description,
author, repository/homepage, license, keywords, `skills`, `mcpServers`, and an interface
whose capabilities contain only `Read`. `.mcp.json` launches:

```json
{
  "mcpServers": {
    "macwise": {
      "command": "macwise",
      "args": ["codex", "serve"]
    }
  }
}
```

Update the skill to prefer the eight typed tools, keep all evidence untrusted, and route
cleanup back to terminal CLI. Remove the obsolete statement that setup/cleanup both
refuse; setup is real, while direct Codex cleanup remains prohibited.

The source `.mcp.json` uses a safe placeholder command only for validation; setup rewrites
the installed copy to the resolved absolute `sys.executable` with args
`["-m", "macwise", "codex", "serve"]`. Ensure Hatchling includes the non-Python payload
in wheels using an explicit include or force-include rule rather than assuming backend
defaults.

**Step 4: Validate skill/plugin and tests**

Run:

```bash
uv run pytest tests/repository/test_codex_plugin.py -q
python3 /Users/o2satz/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py src/macwise/codex_payload/macwise
python3 /Users/o2satz/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/macwise
python3 /Users/o2satz/.codex/skills/.system/skill-creator/scripts/quick_validate.py src/macwise/codex_payload/macwise/skills/macwise
```

Expected: all PASS.

**Step 5: Commit**

```bash
git add pyproject.toml skills/macwise src/macwise/codex_payload tests/repository/test_codex_plugin.py
git commit -m "feat: bundle the MacWise Codex plugin"
```

### Task 6: Implement safe, idempotent personal-plugin setup

**Files:**
- Create: `src/macwise/integration/setup.py`
- Create: `tests/integration/test_codex_setup.py`
- Create: `tests/security/test_codex_setup_safety.py`

**Step 1: Write failing setup tests**

Use isolated `home`, packaged-payload fixtures, and an injected bounded `CodexRunner`.
Cover fresh personal marketplace creation, preservation of existing name/display/order,
append/update only the MacWise entry, same-version idempotency, atomic plugin replacement,
upgrade, failed Codex install rollback, corrupt JSON, symlinked ancestors/files, nonregular
files, same-name foreign source conflict, wrong payload name, missing/incompatible Codex,
bounded output/timeout, absolute Python launch command (including spaces), ownership
marker, interrupted-owned-install repair, compensation failure truth, and exact
`codex plugin add macwise@NAME --json` argv with no shell.

```python
def test_setup_preserves_unrelated_marketplace_entries(tmp_path: Path) -> None:
    home = isolated_personal_marketplace(tmp_path, entries=[OTHER_PLUGIN])
    result = CodexSetupService(home=home, runner=SuccessfulFakeCodex()).install()
    document = json.loads((home / ".agents/plugins/marketplace.json").read_text())
    assert document["plugins"][0] == OTHER_PLUGIN
    assert document["plugins"][1]["name"] == "macwise"
    assert result.status is SetupStatus.INSTALLED
```

**Step 2: Verify red**

Run:

```bash
uv run pytest tests/integration/test_codex_setup.py tests/security/test_codex_setup_safety.py -q
```

Expected: FAIL because setup service does not exist.

**Step 3: Implement setup with narrow ownership**

Define strict `MarketplaceDocument`, `MarketplaceEntry`, `OwnershipMarker`, `SetupResult`, and runner
protocols. Resolve the home once; reject any symlink/non-directory ancestor; read JSON
through a regular-file descriptor with bounds; validate before preserving; write plugin
and marketplace siblings to exclusive temporary paths, fsync, then atomically replace.
Keep a bounded backup until Codex install verification succeeds, then remove it. Restore
the previous plugin/marketplace and reinstall the prior owned selector on later failure;
for a fresh failed install, remove only the just-created selector. If compensation fails,
return an explicit interrupted status and recovery instruction rather than success.

The generated entry is exactly:

```python
MarketplaceEntry(
    name="macwise",
    source={"source": "local", "path": "./plugins/macwise"},
    policy={"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
    category="Productivity",
)
```

Never edit `~/.codex/config.toml`. If the existing marketplace is absent, create the
document with name `personal` and display name `Personal`. If it exists, preserve its
top-level name and display metadata. Do not register the default personal marketplace
with `codex plugin marketplace add`; it is automatically discovered.

**Step 4: Run focused security/quality tests**

Run:

```bash
uv run pytest tests/integration/test_codex_setup.py tests/security/test_codex_setup_safety.py -q
uv run ruff check src/macwise/integration tests/integration tests/security/test_codex_setup_safety.py
uv run pyright src/macwise/integration tests/integration tests/security/test_codex_setup_safety.py
```

Expected: PASS and no files outside isolated homes.

**Step 5: Commit**

```bash
git add src/macwise/integration/setup.py tests/integration/test_codex_setup.py tests/security/test_codex_setup_safety.py
git commit -m "feat: install the Codex plugin safely"
```

### Task 7: Wire the setup UX and hidden MCP entry point

**Files:**
- Modify: `src/macwise/cli.py`
- Modify: `src/macwise/help_text.py`
- Create: `tests/cli/test_phase_six_codex.py`
- Modify: `tests/cli/test_help_contract.py`

**Step 1: Write failing CLI tests**

Prove `macwise setup codex` performs injected setup, reports installed/already-current/
updated/refused states in plain language, uses nonzero exits on failure, and suggests a
new Codex session with `$macwise`. Root/setup help must stay novice-facing and must not
lead with MCP. `macwise codex serve` must be callable for the plugin but hidden from root
help and never instantiate mutation services.

**Step 2: Verify red**

Run: `uv run pytest tests/cli/test_phase_six_codex.py tests/cli/test_help_contract.py -q`

Expected: FAIL because setup still refuses and the server entry point is absent.

**Step 3: Implement minimal CLI wiring**

Replace the Phase 6 refusal with an injected/default `CodexSetupService`. Add a hidden
`codex` Typer group or hidden `codex-serve` command matching `.mcp.json`; the handler does
only `run_stdio()`. Keep all errors bounded and actionable. Do not expose internal MCP or
marketplace terminology in ordinary successful output.

**Step 4: Verify CLI and help regressions**

Run:

```bash
uv run pytest tests/cli/test_phase_six_codex.py tests/cli/test_help_contract.py tests/cli/test_root.py -q
uv run ruff check src/macwise/cli.py src/macwise/help_text.py tests/cli
uv run pyright src/macwise/cli.py src/macwise/help_text.py tests/cli
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/macwise/cli.py src/macwise/help_text.py tests/cli
git commit -m "feat: enable one-command Codex setup"
```

### Task 8: Prove hostile-data safety, installed-wheel operation, and `$macwise` workflow

**Files:**
- Modify: `tests/security/test_hostile_metadata.py`
- Modify: `tests/security/test_codex_read_boundary.py`
- Create: `tests/integration/test_codex_workflow.py`
- Create: `tests/integration/test_installed_codex_plugin.py`
- Modify: `docs/privacy.md`
- Modify: `docs/threat-model.md`

**Step 1: Add failing end-to-end tests**

Feed prompt-shaped names/descriptions, ANSI/bidi/control characters, oversized metadata,
ambiguous identities, partial collectors, and hostile saved plans through every tool.
Assert content remains data, response structure cannot be forged, and no tool call becomes
argv/action authority.

Script a `$macwise Explain which AI apps overlap and which ones I actually use` workflow
as deterministic skill/tool-selection fixtures: tool discovery, audit/overlap call,
qualified facts/unknowns, and terminal-CLI routing for cleanup. This is not a claim that a
model is deterministic; it proves the bundled instructions and typed interface support
the required journey.

Build a wheel, install it into a clean Python 3.12 environment, locate/validate the
packaged plugin, launch the installed `macwise codex serve`, and perform MCP initialize,
list-tools, and a safe call. Never run installed setup against the real home.

**Step 2: Verify tests initially expose missing hardening/docs**

Run:

```bash
uv run pytest tests/security/test_hostile_metadata.py tests/security/test_codex_read_boundary.py tests/integration/test_codex_workflow.py tests/integration/test_installed_codex_plugin.py -q
```

Expected: at least one intended failure before final hardening/docs.

**Step 3: Implement only the evidence-backed hardening**

Add shared result-size enforcement, safe display normalization where responses are
human-facing, typed protocol errors, and privacy/threat-model documentation. Do not
weaken schemas or add generic escape hatches to make fixtures pass.

**Step 4: Run the Phase 6 focused gate**

Run:

```bash
uv run pytest tests/integration tests/security/test_codex_read_boundary.py tests/security/test_codex_setup_safety.py tests/security/test_hostile_metadata.py tests/repository/test_codex_plugin.py tests/cli/test_phase_six_codex.py -q
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/macwise/integration tests docs/privacy.md docs/threat-model.md
git commit -m "test: prove the read-only Codex boundary"
```

### Task 9: Adversarial review, full acceptance, and durable truth

**Files:**
- Replace: `IMPLEMENTATION_PACKET.md`
- Modify: `PROGRESS.md`
- Modify: `TASK_QUEUE.md`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Create: `docs/phase-6-acceptance.md`
- Optionally modify only files required by accepted review findings

**Step 1: Create the current implementation packet before review**

Use @implementation_packet to record exact Phase 6 files, safety boundary, assumptions,
non-goals, verification commands, and rollback. Mark real personal-home setup and public
plugin distribution as unproven until separately tested/authorized.

**Step 2: Run skeptical review**

Use @requesting-code-review and @code_review_adversary. Under the repository's delegation
rules, a bounded read-only Claude second opinion is allowed if the local CLI is available.
Classify every recommendation as Accepted, Rejected, or Needs Investigation. Fix accepted
findings test-first; record meaningful decisions in `DECISIONS.md`.

Review specifically for:

- any hidden mutation/import path in the MCP surface;
- stdout corruption or unbounded response/diagnostic data;
- marketplace/plugin path traversal, symlink, replacement, rollback, or ownership bugs;
- manifest/package/cache/version mismatch;
- ambiguous identity or absent-evidence claims;
- prompt injection becoming instructions;
- setup tests accidentally touching the actual home/Codex configuration.

**Step 3: Run full verification on both supported Pythons**

Run:

```bash
.venv-phase5-py312/bin/python -m pytest -q
.venv-phase5-py313/bin/python -m pytest -q
uv run ruff check .
uv run ruff format --check .
uv run pyright
rm -rf dist && uv build
python3 /Users/o2satz/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py src/macwise/codex_payload/macwise
python3 /Users/o2satz/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/macwise
```

Re-sync the existing Python 3.12/3.13 environments after the lockfile change before
their test runs. Run the repository privacy scan and workflow YAML parse used in prior
acceptance phases. Create a brand-new Python 3.12 wheel environment for installed-wheel
MCP and help smokes; use an isolated temporary HOME for any setup smoke and a fake Codex
binary, never the active personal configuration.

Expected: all local gates pass. Any unavailable hosted runner or live personal-plugin
proof remains an explicit limitation rather than being relabeled PASS.

**Step 4: Write evidence-bounded acceptance and update truth files**

`docs/phase-6-acceptance.md` maps every Phase 6 deliverable to direct evidence and states
a PASS/PARTIAL/FAIL verdict no broader than the proof. Update README setup/usage/privacy,
CHANGELOG, PROGRESS, and TASK_QUEUE. Mark MW-500 done only if clean-home setup,
installed-wheel server, tool boundary, skill validation, conversational workflow, and
independent review all pass. Then make MW-600 the sole ready task.

**Step 5: Commit**

```bash
git add IMPLEMENTATION_PACKET.md DECISIONS.md PROGRESS.md TASK_QUEUE.md README.md CHANGELOG.md docs tests src pyproject.toml uv.lock skills
git commit -m "docs: accept local Phase 6 Codex integration"
```

## Rollback and stop rules

- Revert only the logical Phase 6 commit that introduced a failed slice; never reset or
  discard unrelated work.
- Stop before any command would modify the developer's real `~/plugins`,
  `~/.agents/plugins/marketplace.json`, or `~/.codex/config.toml`.
- Stop for a same-name foreign marketplace entry, incompatible live Codex behavior,
  dependency vulnerability without a safe pin, missing publication credentials, or any
  discovery that read-only tools can reach mutation authority.
- Do not mark Phase 6 complete from unit tests alone. Installed-wheel STDIO protocol,
  clean-home setup, package artifact validation, hostile-data safety, review closure, and
  truthful documentation are mandatory.
