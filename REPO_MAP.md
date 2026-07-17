# REPO_MAP.md

## Project Type

Greenfield public Python CLI and reusable library for read-only macOS software auditing, later extended with reversible cleanup and optional Codex integration.

## Tech Stack

- Required: Python 3.12+, Typer, Rich, Pydantic, SQLite, pytest, Ruff, Pyright, uv.
- Current at intake: planning Markdown only; no package, environment, or tool configuration exists.

## Package Manager

`uv` is the contributor tool. Standards-compliant `pyproject.toml` metadata must support `pipx install macwise` independently of uv.

## Commands

| Purpose | Command | Verified |
|---|---|---|
| Inspect files | `rg --files` | Yes, 2026-07-17 |
| Inspect repository state | `git status --short --branch` | Yes; failed because no Git repository existed |
| Test | `uv run pytest` | No; not configured yet |
| Lint/format | `uv run ruff check .` and `uv run ruff format --check .` | No; not configured yet |
| Type check | `uv run pyright` | No; not configured yet |
| Build | `uv build` | No; not configured yet |

## Entry Points

Planned console entry point: `macwise = macwise.cli:main`. No runtime entry point exists yet.

## Major Folders

- Repository root: active and historical planning artifacts.
- `docs/plans/`: design and implementation plans created before code.
- Planned `src/macwise/`: product library and CLI.
- Planned `tests/`: sanitized unit, CLI, collector, safety, and integration tests.
- Planned `skills/macwise/`: optional Codex integration.

## Existing Patterns To Preserve

- The public CLI is the product; Codex is optional.
- Deterministic evidence precedes inference or recommendation.
- Guided no-argument use and simple nested commands are primary UX.
- Audit/review operations are read-only; mutations require reviewed plans, action-time confirmation, rollback manifests, verification, and undo.

## Tests and Verification

No tests existed at intake. The first implementation must establish CLI behavior tests before production code, then add fixtures for all host-command parsers and regression tests for shell/prompt injection.

## Likely Files For Current Task

- `pyproject.toml`
- `src/macwise/cli.py`
- `src/macwise/models.py`
- `src/macwise/collectors/`
- `src/macwise/reporting/`
- `tests/cli/`
- `tests/collectors/`
- public repository documentation and CI files required by `GOAL.md`

## Unknowns

- Availability and exact versions of Python 3.12 and uv on this host.
- Current output variations of macOS and Homebrew commands across supported versions and architectures.
- Public GitHub repository/tap ownership and release credentials.
- Final Phase 6 typed local integration package.
