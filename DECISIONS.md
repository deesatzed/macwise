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
