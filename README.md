# MacWise

## What MacWise does

MacWise helps ordinary Mac users understand installed applications, Homebrew software,
startup items, storage, backups, and overlapping tools before changing anything. It
separates verified facts, cautious inferences, user-confirmed context, and unknowns.

`1.0.0rc1` is a locally verified release candidate. Audit and review are read-only.
Cleanup requires an immutable reviewed plan, fresh revalidation, an exact approval
fingerprint, a crash-visible journal, verification, and separately approved undo. This
is not a promise that every Mac, permission configuration, or package manager edge case
has been proven.

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

Every choice also has a deterministic command. See the [synthetic walkthrough](docs/demo.md).

## Installation

The intended primary public command is:

```bash
uv tool install macwise
```

Then open MacWise:

```bash
macwise
```

If you already use pipx, it remains a supported alternative:

```bash
pipx install macwise
```

The package is **not yet published**. Homebrew distribution is deferred to a later
milestone so it cannot drift from the first release. To evaluate this exact candidate from a
trusted checkout:

```bash
uv sync --locked --all-groups
uv run macwise
```

See [Getting started](docs/getting-started.md). Removing the CLI does not remove audit
files or local plan/recovery state you explicitly created.

## Guided usage

Run `macwise` with no arguments. It prompts in an interactive terminal and prints the
same menu without blocking in automation. A first read-only review can be:

```bash
macwise scan
macwise explain "Example App"
macwise review unused
macwise overlap
```

Save a report only when you choose a path:

```bash
macwise scan --format json --output audit.json
macwise scan --format markdown --output audit.md
```

Existing reports are not replaced unless you add `--force`.

## Safety promises

- Scan, explain, review, compare, storage, startup, backups, and doctor do not mutate host state.
- Discovered metadata is untrusted data, never shell or AI instructions.
- Missing last-use evidence never means “never used”; configured backup never means verified coverage.
- Homebrew dependencies are not ordinary delete candidates; unknown/protected targets remain blocked.
- Planning changes only immutable local preview state, not installed software.
- Apply supports only closed manual-app, Homebrew, and current-user startup actions; no arbitrary command, elevation, force, zap, related-data deletion, or system daemon action exists.
- Apply and undo require separate exact consent and verify observed state; Homebrew reinstall is explicitly best-effort.
- Codex exposes only eight bounded read-only tools and cannot approve, apply, undo, or persist cleanup state.

Read [Privacy](docs/privacy.md), the [Threat model](docs/threat-model.md), and the
[Security policy](SECURITY.md) before using cleanup features.

## Codex setup

Install the optional local experience for the current user:

```bash
macwise setup codex
```

Start a new Codex session and type:

```text
$macwise Explain which installed AI tools overlap and which ones appear active.
```

Setup validates Codex compatibility and installs a bundled native plugin backed by a
local read-only server. It needs no MacWise account or AI-provider key. The standalone
CLI remains fully usable without Codex.

## Common examples

```bash
macwise review apps
macwise review brew
macwise storage
macwise scan --format json
macwise explain "Example App"
macwise compare "Docker Desktop" "Podman"
macwise startup
macwise backups
macwise plan add "Example App"
macwise plan show
macwise apply
macwise undo
macwise doctor
```

Use `--help` on every root or nested command.

Long inventories show a concise default view. Add `--all` only when you want every
Homebrew item, startup item, unknown item, measured application, backup-path observation,
or mounted macOS support volume—for example, `macwise review brew --all`.

## Release status

Phases 1–6 have local acceptance audits under `docs/`. Phase 7 is preparing public
artifacts and install paths. Hosted CI, PyPI, and GitHub Release are not claimed
until those systems run successfully. See the [release checklist](docs/release-checklist.md).

## Development

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/):

```bash
uv sync --locked --all-groups
uv run pytest
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv build
```

Read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a change.
