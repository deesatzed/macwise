# MacWise

## What MacWise does

MacWise helps ordinary Mac users understand installed applications, Homebrew software, and storage before deciding what deserves attention. It gathers deterministic local evidence first, distinguishes user-selected Homebrew tools from dependencies, and labels missing evidence instead of turning it into a confident claim.

MacWise is currently a pre-alpha inventory, explain/review, cleanup-planning, and locally verified reversible-cleanup tool. It reports cautious usage findings, startup ownership, bounded related-data measurements, Time Machine facts, and exact-catalog role-aware overlaps without claiming complete history, backup coverage, or interchangeability. Cleanup previews can be saved as immutable local state and applied only after fresh revalidation plus an exact approval fingerprint; one-command Codex setup and public release are still under development.

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
9. Review undo recovery
10. Help
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
- Overlap categories come from exact qualified catalog identities and explicit relations, never fuzzy name similarity.
- Phase 3 guidance can recommend keep, learn, keep-together, cautious consolidation review, or no recommendation; it does not authorize removal.
- `plan add` and `plan show` write or read only local immutable preview state; they do not change installed software or user data.
- `apply` requires a schema-2 reviewed plan, fresh evidence, an exact fingerprint phrase, a pre-mutation journal, and verified after-state; it never elevates privileges or deletes related user data.
- `undo` requires separate exact approval and verifies reverse-order restoration. Trash restoration is exact; Homebrew reinstall is best-effort and may not restore the captured version.
- Only standard application roots, exact safe Homebrew formulae/casks, running Homebrew services, and current-user LaunchAgents are supported. System/privileged targets and arbitrary commands remain blocked.
- `setup codex` still refuses safely rather than simulating unfinished integration.

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

# Compare exact catalog roles, observed-use evidence, and unique value
macwise compare "Docker Desktop" "Podman"

# Review role-aware overlap groups without calling every pair a duplicate
macwise review duplicates

# Inspect startup ownership and backup limitations
macwise startup
macwise backups

# Save and review an exact non-executing cleanup preview
macwise plan add "Example App"
macwise plan show

# Revalidate, review the exact phrase, then explicitly approve
macwise apply
macwise apply --approve 'APPLY FINGERPRINT'

# Review reverse actions and use a separate approval phrase
macwise undo

# Diagnose collector availability
macwise doctor
```

Every command supports `--help`, including nested commands such as `macwise review apps --help`.

## Current scope and roadmap

Phases 1–5 cover guided use, the public command hierarchy, evidence-rich inventory, cautious usage and backup findings, exact-match role intelligence, immutable cleanup previews, approval-gated allowlisted execution, append-only recovery manifests, fresh verification, and undo. Phase 5 local acceptance is synthetic/fake-mutator evidence, not permission to test real installed software without explicit authority. `GOAL.md` remains the full contract for Codex integration and public release. See the phase acceptance audits under `docs/` for proof and limitations.

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
