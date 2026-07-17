# IMPLEMENT.md

## Recommended Agent Workflow

- **Orchestrator:** Reads project truth, selects the next coherent vertical slice, protects scope, and updates durable state.
- **Implementer:** Uses test-first changes within the slice and avoids unrelated edits.
- **Reviewer:** Challenges correctness, privacy, shell safety, help quality, and drift from `GOAL.md`.
- **Tester:** Runs the narrow red/green test, then the full local gate, packaging checks, and relevant macOS smoke tests.

One agent may hold all roles. Claude Code may provide a bounded second opinion under `AGENTS.md`; Codex adjudicates every recommendation.

## Upfront Repository Reconnaissance

The initial checkout contained only `GOAL.md`, `GOAL_old.md`, and `docpre2.md`, and was not a Git repository. There was no code, packaging, CI, test harness, or pre-existing implementation to preserve. `GOAL.md` is the controlling specification; the older documents are provenance, not active requirements.

## Clarification Questions That Would Have Been Ideal

- Whether the public package name `macwise` and Homebrew tap `deesatzed/tap` are already reserved.
- Whether the initial release should support Intel Macs in addition to Apple Silicon.
- Whether `uv` is mandatory for contributors or only the preferred development tool.

These do not block Phase 1. Defaults are recorded in `DECISIONS.md` and can be revised with evidence.

## Architecture Decisions Needed

- Stable schema and evidence provenance representation.
- Collector command wrapper and degradation policy.
- SQLite schema/migration strategy and default state directory.
- Terminal/guided interaction behavior for TTY and non-TTY sessions.
- Safe action plan format, approval token, allowlisted executors, and rollback manifest.
- Codex skill installation targets and read-only typed integration protocol.

## Implementation Phases

### Phase 0 — Public Repository Foundation

Create Git history, packaging, license, contributing/security/privacy docs, CI, sanitized fixtures, architecture records, and development commands.

### Phase 1 — Public Read-Only CLI

Deliver the no-argument guided menu, command hierarchy/help contract, versioned evidence models, application/Homebrew/drive collectors, JSON/Markdown reports, failure degradation, and tests.

### Phase 2 — Explain and Review

Add stable item matching, direct/indirect usage evidence, startup ownership, related data, backup limitations, and verified/inferred/user/unknown report sections.

### Phase 3 — Overlap Intelligence

Add role-aware catalog entries, required overlap categories, active-use comparison, learning value, and guarded recommendations.

### Phase 4 — Cleanup Planning

Add persistent decisions and an immutable preview plan with dependency, ambiguity, protection, data, and backup preflight. No action execution in this phase.

### Phase 5 — Reversible Cleanup

Add allowlisted, confirmation-gated executors for Trash-first application removal, exact Homebrew uninstall, reversible startup disable, post-action verification, and undo.

### Phase 6 — Codex Integration

Bundle the `$macwise` skill, implement one-command setup, expose typed read-only local operations, and prove natural-language review against sanitized audits.

### Phase 7 — Public Release

Prove `pipx` and Homebrew installations from clean environments, add release automation/demo/security review, audit public content for privacy, and cut a 1.0 release candidate after all acceptance evidence exists.

## Atomic Task Format

Each task records:

1. user-visible behavior or invariant,
2. exact files,
3. failing test and expected failure,
4. minimal implementation,
5. narrow and full verification commands,
6. documentation/progress delta,
7. rollback instructions,
8. logical commit boundary.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| macOS metadata is incomplete or version-dependent | Preserve unknowns and limitations; fixture-test every parser; isolate command adapters. |
| Inventory commands are slow or absent | Add timeouts, per-collector status, cached snapshots, and partial-audit reporting. |
| Names or metadata trigger command injection | Never use a shell; validate types and paths; add malicious fixture regression tests. |
| Dependency libraries look removable | Model explicit/leaf status and reverse dependencies before recommendations. |
| Backups are overstated | Require path-specific evidence and label uncertainty. |
| Cleanup causes data loss | Separate planning from execution, preserve data, use Trash, require approval, write rollback manifests, verify and support undo. |
| Interactive UX breaks automation | Detect TTY; keep every guided choice available as a deterministic subcommand and structured output. |
| Public release leaks local details | Use only synthetic fixtures and run privacy/secret scans before publishing. |

## Open Decisions

- Exact SQLite migration library or minimal built-in migrations.
- Which read-only local typed protocol package best fits Phase 6 at implementation time.
- Homebrew tap ownership, signing, and release credentials; these become blockers only when publication is attempted.
