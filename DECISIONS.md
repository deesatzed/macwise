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

## Initial Default Decisions

- MIT license unless a later legal decision selects Apache-2.0.
- Store user state under the platform-appropriate user data directory with an override for tests.
- Keep audit schema versions independent from package versions.
- Prefer partial truthful audits over all-or-nothing collection failures.
- Treat Phase 1 as strictly read-only and do not add hidden mutation hooks early.

## Superseded Decisions

None.

## Decision Rules for Future Agents

- Record a decision before introducing a production dependency, mutating capability, persisted public schema, credential requirement, or compatibility break.
- Do not rewrite accepted decisions silently. Add a replacement with evidence and mark the prior decision superseded.
- Favor the choice that improves novice safety and explainability while preserving structured automation.
- Tests arbitrate implementation claims; `GOAL.md` arbitrates scope claims.

## Pending Decision Questions

- D-P01: Select the SQLite migration mechanism before persistent audit history lands.
- D-P02: Select and pin the Phase 6 local typed protocol after evaluating current official support.
- D-P03: Confirm tap/repository ownership and release credentials before external publication.
