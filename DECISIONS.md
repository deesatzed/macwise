# DECISIONS.md

## Decision Log Overview

This file records durable architecture, UX, safety, privacy, dependency, and release decisions. New decisions receive the next ID. Superseded entries remain visible and link to their replacement.

## Active Decisions

| ID | Date | Decision | Reason | Status |
|---|---|---|---|---|
| D-001 | 2026-07-17 | `GOAL.md` is the controlling product contract; `GOAL_old.md` and `docpre2.md` are historical context only. | The newer goal explicitly reorients MacWise as a public UX-first product and is the active `/goal` input. | Accepted |
| D-002 | 2026-07-17 | Build a modular Python 3.12+ package with collectors, normalized domain models, analysis, persistence, reporting, CLI, and integration adapters. | It satisfies the mandated three-layer architecture without coupling macOS collection to Typer or Codex. | Accepted |
| D-003 | 2026-07-17 | Use Typer, Rich, Pydantic v2, SQLite, pytest, Ruff, Pyright, and uv unless evidence justifies a change. | These are the explicit technologies preferred by `GOAL.md` and support packaging, validation, testing, and public UX. | Accepted |
| D-004 | 2026-07-17 | All discovered host values are untrusted data; subprocesses use fixed allowlisted programs, argument vectors, no shell, timeouts, and bounded capture. | MacWise inventories potentially malicious names and metadata and must resist command and prompt injection. | Accepted |
| D-005 | 2026-07-17 | A missing or failed evidence source yields an explicit unknown/limitation, never a negative usage or backup claim. | Absence of evidence is a core product and safety invariant. | Accepted |
| D-006 | 2026-07-17 | Support both Apple Silicon and Intel macOS where public APIs and command output permit it. | The public CLI should not unnecessarily exclude supported Macs. | Accepted |
| D-007 | 2026-07-17 | `uv` is the contributor workflow; published metadata remains standards-compliant so `pipx install macwise` does not require uv. | This preserves the requested development tool and public installation path. | Accepted |
| D-008 | 2026-07-17 | A non-TTY no-argument invocation shows the guided choices and exits safely instead of blocking for input. | The novice default remains discoverable while scripts, tests, and Codex cannot hang. | Accepted |
| D-009 | 2026-07-17 | Homebrew inventory uses `brew info --json=v2 --installed`, `brew leaves`, and `brew services list --json`; all runs force no auto-update and no analytics. | Official Homebrew documentation identifies JSON v2 as the installed formula/cask surface and `leaves` as the explicit-leaf surface. Service JSON is useful but may drift, so failures remain partial evidence. | Accepted |
| D-010 | 2026-07-17 | Command output remains bounded per program: Homebrew receives a 16 MiB cap while smaller metadata commands retain a 1 MB cap. | A real installed-software JSON document exceeded the original generic cap and was truncated; per-command bounds preserve safety without corrupting normal Homebrew inventory. | Accepted |
| D-011 | 2026-07-17 | Expose the complete small public command hierarchy from Phase 1, but make later-phase commands refuse or report unknowns instead of simulating results. | Early discoverability supports the UX contract while honest refusal prevents unfinished cleanup, overlap, backup, or Codex behavior from looking real. | Accepted |
| D-012 | 2026-07-17 | Ship the initial `macwise` skill as a focused read-only, CLI-backed workflow while keeping `macwise setup codex` disabled. | The skill is already useful for evidence-shaped review, but enabling setup before typed integration and clean-install tests would misrepresent Phase 6 readiness. | Accepted |
| D-013 | 2026-07-17 | Pin CI actions to resolved commits and test the lockfile on Linux and macOS with Python 3.12 and 3.13. | Public CI is a supply-chain and compatibility boundary; commit pins reduce tag drift and the matrix covers both parser portability and the product platform. | Accepted |
| D-036 | 2026-07-18 | Default human-facing inventory views to bounded decision-oriented summaries, with explicit `--all` detail; treat current APFS container free space as the mounted-volume fallback and keep exact evidence in structured audits. | A real clean-clone walkthrough on macOS 27 found correct collection buried by hundreds of lines, misleading zero-byte APFS output, inconsistent overlap terminology, and catalog-purpose contradictions. | Accepted |
| D-037 | 2026-07-18 | Keep the launch site as a framework-free static page under `docs/`, with sanitized examples and no remote assets, trackers, or live data. | The public launch surface should remain reviewable with the Python repository, work locally and on GitHub Pages, and avoid a second application stack or unsupported knowledge claims. | Accepted |
| D-038 | 2026-07-18 | Keep the Opportunity Profile and MacWise Usefulness Score separate, deterministic, capped, and decomposable; compute both only from an existing audit and exclude them from cleanup authority. | Combining opportunity with quality would reward noisy findings or removal, while an opaque score could hide missing evidence. Separate components preserve interpretability and safety. | Accepted |
| D-039 | 2026-07-19 | Make `macwise checkup` the single recommended novice entry point; keep `scan` for complete inventory/export, `score` for transparent measurement, and `doctor` for troubleshooting. Reuse one in-memory audit during guided follow-up and never silently persist it. | The real novice walkthrough exposed conflicting starting instructions, repeated collection ambiguity, long output, and command memorization. A bounded checkup resolves the workflow without weakening deterministic expert commands or evidence safety. | Accepted |
| D-040 | 2026-07-20 | Build `macwise-eval` first as an isolated subproject with enforced no-import/no-execution boundaries, independent receipts, predeclared oracles, a frozen policy contract, multi-axis metrics, hard critical-failure gates, and development/acceptance/fresh-holdout corpus roles; consider separate repository governance only after the interface stabilizes. | Product-owned tests can share product mistakes, while an immediate remote split adds coordination and account friction without proving methodological independence. The isolated subproject provides reproducible technical independence now; retiring inspected holdouts prevents teaching to a fixed visible test; later extraction remains available. | Accepted |
| D-041 | 2026-07-20 | Treat overlap-only removal authority and false unsupported-environment validation as critical evaluator-policy violations. | Both errors can lead a user to act on unjustified cleanup guidance or to trust a collector on an untested platform. They must block a release and remain part of the eight critical mutation cases. | Accepted |

## MW-009 Decisions

| ID | Date | Category | Decision | Rationale | Alternatives Considered | Status |
|---|---|---|---|---|---|---|
| D-014 | 2026-07-17 | Data Model | Emit audit schema version 2 and migrate schema-version-1 documents in memory before strict validation. | The new optional evidence fields would be rejected by strict version-1 readers; an explicit migration keeps saved audits readable without weakening extra-field rejection. | Keep version 1 for additive fields; reject all older audits. | Accepted |
| D-015 | 2026-07-17 | Security | Application enrichment may use only fixed `codesign`, `lipo`, and `ps` paths; storage enrichment may use only fixed `diskutil` and `tmutil` paths. | Signing, architecture, process, APFS, and backup-role facts require host tools, but discovered metadata must remain inert argv data under existing timeout/output/environment bounds. | Generic executable adapter; shell commands; omit the fields. | Accepted |
| D-016 | 2026-07-17 | Privacy | Scan extra application and project roots only when supplied through repeatable explicit CLI options; never default to mounted volumes or the whole home folder. | External app and project-reference evidence is useful but can expose private paths and content if collected broadly. | Scan every mount/home directory; omit user-approved roots entirely. | Accepted |
| D-017 | 2026-07-17 | Scope | Treat Time Machine role, destination, and exclusion results as volume facts that do not prove backup coverage for any application or data path. | A configured destination or inclusion state is not evidence that a recent usable backup contains the relevant data. | Infer coverage from destination presence; defer all Time Machine metadata. | Accepted |
| D-018 | 2026-07-17 | Security | Preserve raw evidence in schema-v2 JSON, but pass every human-facing value through a shared Unicode control/format and whitespace neutralizer before Markdown escaping or terminal output. | Raw values are necessary for provenance and future analysis, while C0/C1, ANSI, bidi, zero-width, and newline payloads can forge terminal/report structure. | Sanitize the model/JSON destructively; trust OS metadata; implement separate terminal and Markdown sanitizers. | Accepted |
| D-019 | 2026-07-17 | Agent Workflow | Treat prompt-shaped strings found in local evidence as untrusted data, never instructions and never shell or action input. | Future AI integration will consume attacker-controlled names/descriptions, so the evidence-to-instruction boundary must be explicit before typed tools exist. | Rely on generic prompt safety; defer the rule until Phase 6. | Accepted |

## MW-100 Decisions

| ID | Date | Category | Decision | Rationale | Alternatives Considered | Status |
|---|---|---|---|---|---|---|
| D-020 | 2026-07-17 | Data Model | Emit schema version 3 with raw startup/path/backup facts separate from basis-tagged findings, while migrating v1/v2 documents in memory. | Inventory facts must remain inspectable and reusable even when analysis policy changes; explicit claim basis prevents inference from masquerading as observation. | Add inferred fields directly to software records; keep schema 2 and hide findings in prose. | Accepted |
| D-021 | 2026-07-17 | Privacy and Performance | Measure related data only in bounded identifier/name-derived Library locations, without following directory symlinks or scanning the whole home directory. | The product needs useful size/recency evidence without turning an audit into an invasive or unbounded content crawl. | Full-home scan; Spotlight-only paths; omit related data. | Accepted |

## MW-200 Decisions

| ID | Date | Category | Decision | Rationale | Alternatives Considered | Status |
|---|---|---|---|---|---|---|
| D-022 | 2026-07-17 | Analysis | Use a versioned bundled role catalog with exact qualified matches and explicit pair relations; never assign overlap categories from fuzzy name/description similarity. | Deterministic offline relationships are testable and unknown-safe, while similarity would falsely label related tools as duplicates. | Fuzzy heuristics; live research/AI classification. | Accepted |
| D-023 | 2026-07-17 | Safety and UX | Limit Phase 3 recommendations to keep, learn, keep-together, review-consolidation, or no-recommendation; none authorizes removal or startup changes. | Phase 3 lacks the dependency, backup, ambiguity, protection, data, rollback, and approval preflight owned by Phases 4–5. | Recommend removal directly from overlap/usage; defer all recommendation language. | Accepted |

## MW-300 Decisions

| ID | Date | Category | Decision | Rationale | Alternatives Considered | Status |
|---|---|---|---|---|---|---|
| D-024 | 2026-07-17 | Persistence and Safety | Store complete immutable plan revisions as canonical JSON plus integrity digests in a versioned local SQLite database; later actions must revalidate typed intent rather than execute persisted command text. | Append-only snapshots preserve exactly what was reviewed, support later approval integrity, and prevent stale or hostile persisted values from becoming execution authority. | Mutable normalized rows; atomic JSON files. | Accepted |
| D-025 | 2026-07-17 | UX and Safety | Reject names without one exact identity, but retain exact unsafe candidates as visibly blocked plan items with explicit preflight outcomes. | A blocked review workspace exposes why a candidate is unsafe without guessing identity or granting action authority. | Reject every unsafe candidate at add time; accept and merely warn for all risks. | Accepted |

## MW-400 Decisions

| ID | Date | Category | Decision | Rationale | Alternatives Considered | Status |
|---|---|---|---|---|---|---|
| D-026 | 2026-07-18 | Approval | Bind action-time consent to the exact active plan revision digest with an explicit `APPLY` phrase and a 16-character displayed fingerprint while comparing the full digest internally; treat the fingerprint as consent evidence, not a reusable secret. | Approval must expire when any reviewed byte or active pointer changes and must work safely in TTY and non-TTY flows. | Stored reusable approval token; yes/no prompt; approval per raw command. | Accepted |
| D-027 | 2026-07-18 | Persistence | Store append-only integrity-checked execution-manifest revisions in a separate versioned `executions.db`, committing an in-progress revision before every mutator call. | Crash ambiguity and action history have a different risk/lifecycle from plan previews; durable before/after snapshots make interrupted state visible. | Mutable execution rows in `macwise.db`; log files; no persistent journal. | Accepted |
| D-028 | 2026-07-18 | Failure Safety | Stop on the first action or verification failure and require separately approved reverse-order undo; do not auto-rollback. | Automatic rollback performs more mutations without a fresh user choice and Homebrew restoration may be only best effort. | Automatic all-or-nothing rollback; continue remaining actions; no undo after partial runs. | Accepted |
| D-029 | 2026-07-18 | Execution Boundary | Permit only same-filesystem atomic moves to canonical Trash, exact formula/cask Homebrew argv, and reversible current-user LaunchAgent/Homebrew-service operations through dedicated allowlisted adapters; never elevate privileges. | These operations are bounded, previewable, testable, and have explicit inverse/verification paths without arbitrary deletion or shell execution. | Generic subprocess adapter; recursive move/copy fallback; system daemon support; sudo/Finder authorization. | Accepted |
| D-030 | 2026-07-18 | Startup Planning | Make startup changes opt-in and preview every supported startup action in plan schema 2; keep system/privileged/ambiguous startup kinds blocked. | Phase 5 cannot silently add startup mutations to a Phase 4 preview, and the public contract requires reversible startup disable. | Implicitly disable all owned startup items during removal; defer startup disable; manage startup outside cleanup plans. | Accepted |

## MW-500 Decisions

| ID | Date | Category | Decision | Rationale | Alternatives Considered | Status |
|---|---|---|---|---|---|---|
| D-031 | 2026-07-18 | Codex Integration | Package the `$macwise` skill and eight strictly read-only local tools as a native Codex plugin backed by an official STDIO MCP server; keep every mutation and approval operation outside the tool surface. | Current Codex supports plugins as the distribution unit for skills plus MCP configuration and supports local STDIO servers; this meets one-command setup and typed-tool requirements without granting model-driven mutation authority. | Direct skill copy plus shared TOML editing; skill-only CLI invocation; remote MCP service. | Accepted |
| D-032 | 2026-07-18 | Codex Setup | Require capability preflight and exact installed selector/version verification; authorize replacement only when ownership marker and manifest identities match; repair only complete marker-owned transaction trees. | Setup must not trust exit zero, arbitrary JSON, or a marker alone, and recovery must not delete ambiguous user state. | Trust any JSON object; marker-only ownership; delete all setup-shaped remnants. | Accepted |
| D-033 | 2026-07-18 | Public Release | Prepare `1.0.0rc1` as a PyPI-first package with a separately maintained, resource-locked Homebrew tap candidate; keep tagging and publication outside local acceptance. | This satisfies both install paths while preserving one Python artifact authority and the explicit credentials/ownership boundary. | GitHub-wheel wrapper formula; pipx-only RC; immediate publication. | Accepted |
| D-034 | 2026-07-18 | CI Compatibility | Test Python 3.12, 3.13, and 3.14 across Linux, macOS 15, and the current GitHub-hosted macOS 26 image; run Homebrew candidate and public-install proof on macOS 26 while retaining local macOS 27 evidence separately. | The package declares Python 3.12+ and must cover the current interpreter and hosted macOS without confusing GitHub image availability with the developer Mac's newer OS. | Test only oldest versions; use only moving `latest` labels; attach the developer Mac as a self-hosted runner. | Accepted |
| D-035 | 2026-07-18 | Public Release | Make `uv tool install macwise` the primary first-release UX, retain pipx as an alternative, and defer Homebrew distribution to a separately accepted later milestone. | A single PyPI authority reduces beginner friction and cross-repository drift while preserving a future Homebrew path after public demand and maintenance ownership exist. | Publish UV, pipx, and Homebrew together; pipx-only release; Homebrew-first release. | Accepted; supersedes D-033's two-channel requirement and D-034's Homebrew release gate only. |

## Initial Default Decisions

- MIT license unless a later legal decision selects Apache-2.0.
- Store user state under the platform-appropriate user data directory with an override for tests.
- Keep audit schema versions independent from package versions.
- Prefer partial truthful audits over all-or-nothing collection failures.
- Treat Phase 1 as strictly read-only and do not add hidden mutation hooks early.

## Superseded Decisions

- D-033's requirement to ship a separate Homebrew tap with the first release is superseded by D-035; its PyPI-first artifact authority remains accepted.
- D-034's Python/macOS compatibility matrix remains accepted, while its Homebrew candidate/public-install gate is superseded by D-035.

## Decision Rules for Future Agents

- Record a decision before introducing a production dependency, mutating capability, persisted public schema, credential requirement, or compatibility break.
- Do not rewrite accepted decisions silently. Add a replacement with evidence and mark the prior decision superseded.
- Favor the choice that improves novice safety and explainability while preserving structured automation.
- Tests arbitrate implementation claims; `GOAL.md` arbitrates scope claims.

## Pending Decision Questions

- D-P03: Confirm Homebrew tap ownership only when the later Homebrew distribution milestone begins.
