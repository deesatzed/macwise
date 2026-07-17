# MacWise

## What MacWise does

MacWise helps ordinary Mac users understand installed applications, Homebrew software, and storage before deciding what deserves attention. It gathers deterministic local evidence first, distinguishes user-selected Homebrew tools from dependencies, and labels missing evidence instead of turning it into a confident claim.

MacWise is currently a pre-alpha read-only inventory and explain/review tool. It now reports cautious usage findings, startup ownership, bounded related-data measurements, and Time Machine facts without claiming complete history or backup coverage. Overlap recommendations, cleanup planning, reversible apply/undo, and one-command Codex setup are still under development.

## Terminal example

```text
$ macwise
MacWise

What would you like to do?

1. Scan this Mac
2. Review installed apps
3. Review Homebrew software
4. See what starts automatically
5. Find overlapping apps
6. See what uses the most space
7. Ask what an app does
8. Create a safe cleanup plan
9. Help
```

Every guided choice also has a direct command for repeatable use.

## Installation

The intended public commands are:

```bash
brew install deesatzed/tap/macwise
```

or:

```bash
pipx install macwise
```

The package and Homebrew tap are **not yet published**. Until the release phase is complete, contributors can run the verified source checkout with:

```bash
uv sync --locked --all-groups
uv run macwise
```

To remove a future public installation:

```bash
brew uninstall macwise
# or
pipx uninstall macwise
```

Removing the CLI will not remove audit files that you explicitly saved.

## Guided usage

Run `macwise` with no arguments. In an interactive terminal it asks for a choice; in scripts and non-interactive environments it prints the choices and exits without blocking.

Create a fresh terminal report:

```bash
macwise scan
```

Save structured output only when you explicitly choose a destination:

```bash
macwise scan --format json --output audit.json
macwise scan --format markdown --output audit.md
```

MacWise refuses to replace an existing report unless you review the path and add `--force`.

## Safety promises

- Scan and review commands do not uninstall, disable, unload, launch, or otherwise change installed software.
- Discovered names, paths, and metadata are treated as untrusted data and are never executed as shell commands.
- Homebrew libraries are identified as dependencies rather than presented as ordinary selected applications.
- Missing last-use information means “no reliable evidence,” never “never used.”
- Backup configuration is not described as verified path coverage.
- Current `plan`, `apply`, `undo`, and `setup codex` surfaces refuse safely rather than simulate unfinished capabilities.
- A future cleanup action must have an exact reviewed plan, action-time approval, verification, a rollback manifest, and an undo path where technically possible.

See [Privacy](docs/privacy.md), [Threat model](docs/threat-model.md), and [Security policy](SECURITY.md).

## Codex setup

The target setup command is:

```bash
macwise setup codex
```

It is not enabled in the current pre-alpha build. The repository includes an initial read-only `skills/macwise/` workflow for development, but setup will continue to refuse until the bundled skill, local typed interface, clean installation, and integration tests pass.

Once Phase 6 is complete, Codex users will be able to type:

```text
$macwise Explain which installed AI tools overlap and which ones appear active.
```

The standalone CLI does not require Codex or an AI key.

## Common examples

```bash
# Review installed application bundles
macwise review apps

# Keep Homebrew dependencies distinct from selected tools
macwise review brew

# Inspect internal and external volumes
macwise storage

# Produce machine-readable evidence
macwise scan --format json

# Show cautious identity facts for one item
macwise explain "Example App"

# Review only evidence-supported possibly-unused items
macwise review unused

# Inspect startup ownership and backup limitations
macwise startup
macwise backups

# Diagnose collector availability
macwise doctor
```

Every command supports `--help`, including nested commands such as `macwise review apps --help`.

## Current scope and roadmap

Phases 1 and 2 cover guided use, the complete public command hierarchy, application/Homebrew/storage inventory, evidence provenance, partial-failure reporting, schema-3 JSON/Markdown output, cautious usage findings, startup ownership, bounded related data, backup limitations, and read-only explain/review views. `GOAL.md` remains the full product contract for overlap intelligence, planning, reversible cleanup, Codex integration, and public release. See the [Phase 2 acceptance audit](docs/phase-2-acceptance.md) for current proof and limitations.

## Development

Requires Python 3.12 or newer and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --locked --all-groups
uv run pytest
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv build
```

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a change.
