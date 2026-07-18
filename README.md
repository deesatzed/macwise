# MacWise

## What MacWise does

MacWise helps you understand the software on your Mac before you decide whether to keep,
learn, disable, or remove anything. It reviews applications, Homebrew software, startup items,
storage, backups, and overlapping tools while clearly separating facts from guesses.

`1.0.0rc1` is a release candidate. Local quality gates, clean-clone installation, a real
read-only macOS 27 walkthrough, and hosted CI pass. MacWise is not yet published to PyPI and no
GitHub Release has been created, so the public one-command installation shown below is the
after-publication path—not a claim that it works from the registry today.

See the [MacWise launch page](docs/index.html) for a visual overview or go directly to
[Getting started](docs/getting-started.md).

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

Every menu choice has a deterministic command. Inventories are concise by default and tell you
when `--all` is available. See the [sanitized walkthrough](docs/demo.md).

## Installation

After publication, the primary installation command will be:

```bash
uv tool install macwise
macwise
```

If you already use pipx, this will remain a supported alternative after publication:

```bash
pipx install macwise
```

The package is **not yet published to PyPI**. To evaluate this exact candidate today, use a
trusted checkout:

```bash
git clone https://github.com/deesatzed/macwise.git
cd macwise
uv sync --locked --all-groups
uv run macwise doctor
uv run macwise
```

Homebrew distribution is deferred to a later milestone so it cannot drift from the first
release. Removing the CLI does not remove reports or local plan/recovery state you explicitly
created.

## Guided usage

Start with a read-only health check and scan:

```bash
macwise doctor
macwise scan
```

Then ask focused questions instead of reading hundreds of lines:

```bash
macwise review largest
macwise startup
macwise overlap
macwise explain Docker
macwise compare Docker podman
macwise backups
```

A typical useful result tells you what MacWise observed, how strong that evidence is, what it
could not establish, and a guarded next step. For example:

```text
Actual-use comparison: Harbor has stronger observed use evidence than Dockyard.

Relationship: strong substitute
Shared capabilities: containers, images
Harbor unique: integrated desktop controls
Dockyard unique: daemonless container workflow
```

The names above are fictional. MacWise does not remove either item because two tools overlap.

Save a report only when you explicitly choose a path:

```bash
macwise scan --format json --output audit.json
macwise scan --format markdown --output audit.md
```

Existing reports are not replaced unless you add `--force`. Reports can contain private paths
and software inventories, so review them before sharing.

### How MacWise knows

MacWise reads local macOS metadata and approved system-command output. It can examine application
bundles, Homebrew's installed-package data, launch items, mounted volumes, Spotlight usage
metadata, and Time Machine facts. It does not search the web during an ordinary scan.

Results are labeled:

- **Verified:** directly observed local evidence.
- **Inferred:** a cautious conclusion supported by multiple facts.
- **User-confirmed:** context you explicitly supplied.
- **Unknown:** evidence is absent or ambiguous—not proof of non-use or safety.

The built-in catalog supplies general roles and overlap knowledge for recognized software. It is
versioned with the app rather than silently updated online. A shared updateable knowledge database
is planned for a later phase and is not part of this release candidate.

## Safety promises

- Scan, explain, review, compare, storage, startup, backups, and doctor are read-only.
- Discovered metadata is untrusted data, never a shell command or AI instruction.
- Missing last-use evidence never means “never used”; a configured backup never proves coverage.
- Homebrew dependencies are not ordinary delete candidates; unknown and protected targets block.
- Planning creates an immutable preview and changes no installed software.
- Apply supports a closed set of manual-app, Homebrew, and current-user startup actions—no
  arbitrary commands, elevation, force, zap, related-data deletion, or system-daemon actions.
- Apply and undo require separate exact approvals, fresh revalidation, and observed verification.
- Codex exposes bounded read-only tools and cannot approve, apply, undo, or persist cleanup state.

Read [Privacy](docs/privacy.md), the [Threat model](docs/threat-model.md), and the
[Security policy](SECURITY.md) before using cleanup features.

## Codex setup

Install the optional local integration for the current user:

```bash
macwise setup codex
```

Start a new Codex session and type:

```text
$macwise Explain which installed AI tools overlap and which ones appear active.
```

Setup installs the bundled local plugin and read-only server. It needs no MacWise account or
AI-provider key. The standalone CLI remains fully usable without Codex.

## Common examples

```bash
macwise review apps
macwise review brew
macwise review unknown
macwise review largest
macwise storage
macwise scan --format json
macwise explain Docker
macwise compare Docker podman
macwise startup
macwise backups
macwise plan add SketchNote
macwise plan show
macwise apply
macwise undo
macwise doctor
```

Use `--help` on every root or nested command. Add `--all` only when you need every Homebrew item,
startup item, unknown-purpose item, measured application, backup-path observation, or mounted
macOS support volume.

## Release status

Phases 1–6 are complete against their recorded local acceptance evidence. Phase 7 has a locally
and hosted-CI-verified `1.0.0rc1` candidate. Hosted CI passes across the repository's supported
matrix; PyPI trusted-publisher configuration, the authorized release tag/workflow, the GitHub
prerelease, and a clean public UV installation remain external release gates.

No release tag has been created. Homebrew publishing and the shared online knowledge database are
later milestones, not hidden launch dependencies. See the [Phase 7 acceptance audit](docs/phase-7-acceptance.md)
and [release checklist](docs/release-checklist.md).

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
