# GOAL.md — Build MacWise as a Public, UX-First macOS Software Auditor

## Goal

Build a polished, open-source GitHub repository named **MacWise** that helps ordinary Mac users understand installed software and safely decide what to keep, learn, disable, or remove.

MacWise must work as:

1. A simple standalone CLI anyone can install and use.
2. An optional Codex integration that gives users a conversational `$macwise` experience.
3. A reusable open-source project with tests, documentation, and releases; Homebrew distribution is a later milestone.

The public product is the CLI. The Codex skill is an optional intelligence and conversational layer. Users must not need to understand MCP, skills, agents, or internal architecture.

---

# 1. User experience comes first

## 1.1 Installation

Target public installation:

```bash
uv tool install macwise
```

Also support as an alternative:

```bash
pipx install macwise
```

Provide a one-command Codex integration:

```bash
macwise setup codex
```

That command installs or configures the bundled MacWise Codex skill and any required local read-only integration.

## 1.2 The simplest command

Running this with no arguments:

```bash
macwise
```

must open a friendly guided experience:

```text
MacWise

What would you like to do?

1. Check up this Mac (Recommended)
2. Review installed apps
3. Review Homebrew software
4. See what starts automatically
5. Find overlapping apps
6. See what uses the most space
7. Ask what an app does
8. Create a safe cleanup plan
9. Assess findings and usefulness
10. Review undo recovery
11. Help
```

Do not require users to memorize commands.

## 1.3 Simple command structure

Use a small, understandable hierarchy:

```bash
macwise checkup
macwise scan
macwise score
macwise review
macwise explain <name>
macwise compare <name> [<name>...]
macwise startup
macwise storage
macwise backups
macwise plan
macwise apply
macwise undo
macwise doctor
macwise setup codex
macwise help
```

Nested review commands:

```bash
macwise review apps
macwise review brew
macwise review startup
macwise review duplicates
macwise review largest
macwise review unused
macwise review unknown
```

A user should never need to use internal commands such as `brew list`, `launchctl`, `diskutil`, `mdls`, or `sfltool` directly.

## 1.4 Help quality

Every command must support:

```bash
macwise <command> --help
```

Help text must:

- Start with a plain-English sentence.
- Explain when the command is useful.
- Show two or three realistic examples.
- Avoid internal jargon.
- Explain whether the command changes anything.
- State when an operation is read-only.
- Suggest the next likely command.

Example:

```text
macwise explain NAME

Explains what an installed app or command-line tool does, whether MacWise found
evidence that you use it, what may depend on it, and what overlaps with it.

This command does not remove or change anything.

Examples:
  macwise explain Raycast
  macwise explain ollama
  macwise explain "Docker Desktop"

Next:
  macwise compare Raycast Hammerspoon
  macwise plan
```

Error messages must be actionable:

```text
MacWise found two possible matches:

1. Docker.app
2. Homebrew formula: docker

Run:
  macwise explain "Docker.app"
or:
  macwise explain "formula:docker"
```

---

# 2. Questions MacWise must answer

For every important app, Homebrew cask, Homebrew formula, service, helper, or startup item, answer:

1. What is it?
2. What does it do?
3. How was it installed?
4. Do I appear to use it directly?
5. Might I use it indirectly without realizing it?
6. What depends on it?
7. Does it start automatically or run in the background?
8. How much space does it and its related data use?
9. Is its data on the internal drive or an external drive?
10. Is the relevant data backed up?
11. Would learning to use it provide meaningful value?
12. Which installed apps overlap with it?
13. Which overlapping app do I actually appear to use?
14. What unique functions or data might be lost?
15. Should I keep it, learn it, disable startup, consolidate, or remove it?
16. How confident is that recommendation?

Clearly distinguish:

- Verified facts
- Reasonable inferences
- User-confirmed information
- Unknowns

Never say “never used” when the actual result is “no reliable use evidence found.”

---

# 3. Example user-facing assessment

```text
Raycast

What it is
An app launcher and automation tool that can extend or replace parts of
Spotlight.

Do you appear to use it?
MacWise found no reliable recent launch evidence.

Could you use it indirectly?
Probably not. No installed app or service was found to require Raycast.

Does it start automatically?
Yes. A background/login entry is enabled.

Would learning it help?
Possibly. Its launcher, snippets, clipboard, and automation features may be
useful. However, this Mac also has Hammerspoon and AltTab.

Overlap
- Spotlight: launching and search
- Hammerspoon: programmable automation
- AltTab: window switching

Which overlap appears active?
Hammerspoon has recent configuration activity.
AltTab has startup activity.
Raycast has no reliable recent-use evidence.

Potentially unique data
Snippets, extensions, aliases, preferences, and history.

Recommendation
Review or export unique data, then consider removal.

Confidence
Identification: High
Usage assessment: Medium
Removal safety: High
Learning value: Moderate
```

---

# 4. Inventory and evidence

## 4.1 Applications

Scan:

```text
/Applications
~/Applications
```

Optionally scan user-approved app locations on mounted external drives.

Collect:

- Name
- Bundle identifier
- Version
- Publisher and signing identity
- Install path
- Installation source
- Application size
- Related-data estimate
- Architecture
- Running status
- Startup/background relationship
- Last-use evidence
- Helpers and extensions
- External-drive location
- Protected/system status

Never launch unknown apps to identify them.

## 4.2 Homebrew

Use machine-readable Homebrew output rather than parsing formatted terminal tables.

Collect:

- Installed formulae
- Installed casks
- Explicitly installed formulae (`brew leaves`)
- Dependencies and reverse dependencies
- Services
- Descriptions and homepages
- Installed sizes
- Executables provided
- Project references
- App/cask duplication

Do not treat dependency libraries such as `freetype`, `openssl`, or `libpng` as independently selected apps.

## 4.3 Startup software

Identify and connect startup components to their owner:

- Login items
- Background items
- LaunchAgents
- LaunchDaemons
- Homebrew services
- Privileged helpers
- System/network extensions
- Finder and Quick Look extensions

Explain what user-visible function may stop if a startup component is disabled.

## 4.4 Storage and drives

Assess:

- Internal drive space
- External drive space
- Read/write status
- Filesystem
- App locations
- Related data
- Local AI models
- Container images and volumes
- Database data
- Homebrew caches
- Backup destinations

Clearly say which drive would regain space.

## 4.5 Backups

Check Time Machine when available:

- Whether it is configured
- Last verifiable backup
- Destination availability
- Whether external volumes are included or excluded
- Whether data in a proposed cleanup appears covered

Do not claim something is safely backed up merely because Time Machine is enabled.

## 4.6 Usage evidence

Use multiple signals:

- Currently running
- Spotlight last-used metadata
- Recent app-support activity
- Active startup/background component
- Homebrew service activity
- Project manifest references
- Shell configuration references
- Other software invoking the tool
- User confirmation

Usage labels:

```text
Actively used
Recently used
Probably used
Indirectly required
Configured but idle
Possibly unused
No reliable evidence
User confirmed unused
```

---

# 5. Smart overlap analysis

Do not label related tools as duplicates without understanding their roles.

Required categories:

```text
Exact duplicate
Same product installed twice
Strong substitute
Partial overlap
Complementary tools
Runtime and frontend
Dependency and user-facing app
Legacy and successor
Not actually related
```

Required comparison examples:

- Docker Desktop, Docker CLI, Compose, and Podman
- Ollama, LM Studio, oMLX, llama.cpp, MLX, and local model files
- Obsidian, Zettlr, Mark Text, Markdown Preview, and QLMarkdown
- Raycast, Spotlight, Hammerspoon, AltTab, and Magnet
- Homebrew Python, pyenv, Anaconda, and virtual environments

For each group, explain:

- What overlaps
- What is unique
- Which items appear used
- Which items are indirectly required
- What could be consolidated
- What should not be removed together

---

# 6. AI design

## 6.1 Deterministic evidence first

The local engine must gather facts and create a structured audit before AI reasons about anything.

AI must not invent:

- Use history
- Dependencies
- Backup coverage
- Disk size
- Startup status
- Installed software
- Removal commands

## 6.2 Selective research

Do not web-search every formula or dependency.

Research only:

- Unknown or ambiguous software
- User-facing apps needing explanation
- Obsolete or renamed products
- High-impact removal decisions
- Current compatibility or maintenance questions
- Items the user explicitly asks to investigate

Prefer official product documentation, official repositories, Homebrew metadata, and Apple sources.

Cache results with timestamps and source provenance.

## 6.3 Codex mode

The bundled Codex skill should use the active Codex model to interpret the local audit and converse with the user.

After setup, the user can type inside Codex:

```text
$macwise
```

or:

```text
$macwise Explain which AI apps overlap and which ones I actually use.
```

Codex should call the local MacWise engine rather than asking the user to paste long command output.

## 6.4 Standalone mode

The CLI must remain useful without Codex or an AI key.

It should provide deterministic explanations and recommendations from local metadata and the bundled software catalog.

Optional standalone AI providers may be added later, but they are not required for the first public release.

---

# 7. Safety

Default workflow:

```text
Scan → Explain → Recommend → Plan → Preview → Approve → Apply → Verify → Undo
```

Rules:

- Every scan and review command is read-only.
- Never use arbitrary `rm -rf`.
- Preserve related user data by default.
- Prefer official uninstallers.
- Prefer exact Homebrew uninstall commands for Homebrew-managed software.
- Move manual app bundles to Trash rather than permanently deleting them.
- Require an explicit reviewed plan before changes.
- Require confirmation at action time.
- Reject ambiguous targets.
- Protect Apple/system components.
- Detect dependencies before removal.
- Create a rollback manifest.
- Provide `macwise undo` when technically possible.

Example:

```bash
macwise plan add "CodeLLM.app"
macwise plan show
macwise apply
macwise undo
```

The guided interface should make this easier than the raw commands.

---

# 8. Architecture

Build three layers.

## 8.1 Public CLI and Python library

This is the main product and source of truth.

Responsibilities:

- Collect evidence
- Normalize data
- Analyze dependencies and overlap
- Store audit history and decisions
- Produce terminal, Markdown, and JSON reports
- Create safe cleanup plans
- Execute only approved allowlisted actions

Use:

- Python 3.12+
- `src/` package layout
- Typer
- Rich
- Pydantic or typed dataclasses
- SQLite
- pytest
- ruff
- pyright or mypy
- uv

## 8.2 Codex skill named `macwise`

Bundle a skill that:

- Understands requests about installed Mac software
- Calls the MacWise CLI or typed local tools
- Gives concise, evidence-based explanations
- Supports explicit `$macwise` invocation
- Never performs cleanup without a plan and approval

Suggested location:

```text
skills/macwise/
├── SKILL.md
├── references/
├── scripts/
└── agents/openai.yaml
```

The installer command:

```bash
macwise setup codex
```

must install/configure this for the user.

## 8.3 Local read-only integration

Provide a local typed interface for Codex, preferably an STDIO MCP server, but hide this implementation detail from ordinary users.

Expose read-only operations first:

```text
audit_mac
list_software
inspect_software
find_overlaps
inspect_startup
inspect_storage
inspect_backups
get_removal_preview
```

Do not expose a generic shell tool.

Add write operations only after the read-only product is mature and safety-tested.

---

# 9. Repository and public release requirements

Create a clean public GitHub repository with:

```text
README.md
GOAL.md
AGENTS.md
LICENSE
SECURITY.md
CONTRIBUTING.md
CHANGELOG.md
pyproject.toml
src/
tests/
docs/
skills/macwise/
.github/workflows/
```

README must begin with:

1. What MacWise does
2. A screenshot or terminal example
3. Installation
4. `macwise` guided usage
5. Safety promises
6. Codex setup
7. Common examples

Provide:

- MIT or Apache-2.0 license
- GitHub Actions for lint, types, and tests
- Tagged releases
- Semantic versioning
- UV tool installation from PyPI
- pipx installation as an alternative
- A deferred, separately accepted Homebrew distribution milestone
- Uninstall instructions
- Privacy documentation
- Threat model
- Contribution guide
- Sanitized test fixtures

No personal machine names, usernames, paths, institution names, or private software lists may appear in the public repository.

---

# 10. Build phases

## Phase 1 — Public read-only CLI

Deliver:

- `macwise` guided menu
- `macwise scan`
- Application inventory
- Homebrew formula/cask inventory
- Explicit versus dependency distinction
- Drive inventory
- JSON and Markdown audit
- Excellent `--help`
- Tests

## Phase 2 — Explain and review

Deliver:

- `macwise explain`
- `macwise review`
- Usage evidence
- Startup mapping
- Related-data estimates
- Backup checks
- Clear verified/inferred/unknown sections

## Phase 3 — Overlap intelligence

Deliver:

- `macwise compare`
- `macwise review duplicates`
- Required overlap categories
- Actual-use comparison
- Learning-value recommendation

## Phase 4 — Cleanup planning

Deliver:

- `macwise plan`
- Exact change previews
- Dependency and backup preflight
- Rollback manifests
- No actions yet

## Phase 5 — Reversible cleanup

Deliver:

- `macwise apply`
- Trash-first manual app removal
- Exact Homebrew uninstall
- Reversible startup disable
- Verification
- `macwise undo`

## Phase 6 — Codex integration

Deliver:

- `$macwise` skill
- `macwise setup codex`
- Read-only local typed tools
- Natural conversational review
- Integration tests

## Phase 7 — Public release

Deliver:

- UV tool installation from PyPI
- pipx installation as an alternative
- Documentation
- GitHub release workflow
- Demo
- Security review
- Version 1.0 release candidate

## Later milestone — Homebrew distribution

Deliver only after separate acceptance:

- A maintained Homebrew tap
- Formula/release identity automation
- Clean public Homebrew install, upgrade, and uninstall proof

---

# 11. Acceptance tests

MacWise is ready only when a novice user can:

1. Install it with one command.
2. Run `macwise` without knowing any subcommands.
3. Understand what an unfamiliar app does.
4. Learn whether they use it directly or indirectly.
5. See whether another installed app overlaps.
6. Learn which overlapping app appears active.
7. See internal versus external storage usage.
8. Understand backup limitations.
9. Create a cleanup plan without changing anything.
10. Preview every change.
11. Remove one approved manual app by moving it to Trash.
12. Undo that action.
13. Set up Codex with `macwise setup codex`.
14. Type `$macwise` and review software conversationally.
15. Obtain useful help from every command and error state.

Also verify:

- Homebrew dependencies are not presented as ordinary delete candidates.
- Missing last-use data is not interpreted as “never used.”
- Unknown software is not disabled or removed.
- Docker/Podman, Python environments, and local AI tools are analyzed by role.
- Audit mode performs no mutations.
- Malicious names or metadata cannot inject shell commands or AI instructions.

---

# 12. Definition of done

The repository is complete when it contains:

- A polished public CLI
- A no-argument guided user experience
- Simple nested commands
- Excellent help and error messages
- Evidence-based app explanations
- Direct and indirect usage analysis
- Overlap and learning-value analysis
- Internal/external storage and backup awareness
- Safe plan/preview/apply/undo workflow
- A bundled `$macwise` Codex skill
- One-command Codex setup
- Tests, documentation, CI, releases, and install paths
- No dependency on users understanding the internal skill or MCP architecture

---

# 13. Instructions to Codex

Before coding:

1. Inspect the existing repository and preserve useful work.
2. Identify what can be reused.
3. Create a concise architecture and task plan.
4. Build in the phases above.
5. Prioritize the user-facing workflow before advanced integrations.
6. Test each phase.
7. Commit coherent milestones.
8. Continue until the Definition of Done is met or a genuine blocker requires user input.
9. Never perform destructive testing on the host Mac.
10. Use fixtures and temporary directories for cleanup tests.

The first working milestone must be:

```bash
macwise
```

opening the guided interface, and:

```bash
macwise scan
```

creating a useful read-only report.

Do not begin with MCP or the Codex skill. Build the public product first, then add Codex as the optional intelligent interface.
