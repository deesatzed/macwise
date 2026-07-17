# Phase 1 Public Read-Only CLI Design

## Context and Authority

`GOAL.md` is the user-approved product design. The active first milestone is a public, installable, read-only MacWise CLI whose no-argument experience is useful to a novice and whose collectors produce versioned, provenance-bearing audit data. The design intentionally leaves cleanup execution and Codex plumbing out of Phase 1 while preserving seams required by later phases.

## Considered Approaches

### 1. Single Typer module with direct system calls

This is the fastest path to a demo. It also couples parsing, host access, analysis, and presentation, making read-only guarantees difficult to test and later MCP exposure unsafe. Rejected.

### 2. Modular library with ports and adapters — selected

Typer and Rich form a thin interface over an application service. Collectors call a small safe command adapter and emit normalized Pydantic records. Reporters consume an audit document without host access. This adds modest initial structure but directly supports deterministic tests, partial failure, JSON/Markdown output, Codex reuse, and future allowlisted actions.

### 3. SQLite-first inventory daemon

A background scanner and database-centric API could make repeated audits fast, but it adds lifecycle, staleness, privacy, and installation complexity before the basic CLI is proven. Deferred; Phase 1 may persist completed audit documents without a daemon.

## Architecture

The package is divided into six directional layers:

1. `models`: versioned software, drive, evidence, collector status, and audit document types.
2. `system`: the fixed-program, argument-vector command runner and filesystem abstractions.
3. `collectors`: application, Homebrew, and drive adapters that transform macOS/Homebrew output into models.
4. `services`: audit orchestration, stable matching, and partial-failure aggregation.
5. `reporting`: terminal summaries, Markdown, and deterministic JSON serialization.
6. `cli`: guided menu, simple public commands, output selection, and actionable errors.

Dependencies point inward: the CLI may depend on services and reporting; collectors depend on models and system ports; models never depend on Typer, Rich, subprocess, or the host.

## Components and Data Flow

`macwise scan` builds an `AuditRequest`, selects enabled read-only collectors, and calls `AuditService`. Each collector returns records plus a `CollectorStatus`; a missing tool, timeout, permission failure, or malformed item becomes a bounded status/evidence limitation rather than aborting unrelated collection. `AuditService` stamps schema and collection metadata, joins safe identities where deterministic, and returns one `AuditDocument`. A reporter then emits terminal, Markdown, or JSON output. Only an explicit save option writes an audit file.

The no-argument `macwise` command does not scan immediately. In a TTY it renders the nine choices from `GOAL.md` and prompts for one selection. In a non-TTY it prints the same choices plus an instruction to run a direct command, then exits successfully without blocking. Every guided choice routes to the same function as its public command.

## Evidence and Unknowns

Evidence carries kind, typed/JSON-safe value, source, collection time, reliability, and limitations. Records distinguish observed facts from later inferences. Phase 1 collectors do not infer use, backup coverage, or removal safety. Failed or absent sources yield explicit unknowns. They never emit “never used.”

The audit document has its own schema version, independent of package version. JSON uses stable ordering for reviewable fixtures. Paths are preserved in local audit output when necessary but public fixtures use synthetic roots and public logs redact the user home.

## Host and Shell Safety

Collectors may invoke only fixed executable paths or validated allowlisted program names owned by the adapter. Arguments are separate strings; `shell=True`, interpolated command strings, arbitrary environment inheritance, and execution of discovered metadata are prohibited. Runs have timeouts and output caps. Phase 1 contains no action executor. Filesystem collectors use read/stat/plist operations only.

## Error Handling

Expected host variability is represented in data and summarized plainly. A completely unusable command invocation exits nonzero with a recovery suggestion; partial audits exit successfully but prominently list limitations. Ambiguous item names are never silently selected. Typer usage errors are augmented only where a concrete recovery command can be given.

## CLI and Help Contract

The root and all commands use plain-English summaries. Long help states why/when, read-only or mutating status, realistic examples, and next action. `review` and `setup` are Typer sub-apps; direct convenience commands such as `startup` and `storage` coexist with corresponding review views without exposing collector internals. Commands that are not implemented in the current vertical slice remain absent until their help and behavior are real; Phase 1 completion requires the full required public hierarchy to exist with honest behavior.

## Testing Strategy

- CLI tests exercise no-argument TTY/non-TTY behavior, menu routing, help contract, errors, and structured output.
- Model tests exercise schema versions, serialization stability, provenance, validation, and unknown-language invariants.
- Collector tests use sanitized synthetic directories and captured plist/JSON fixtures; no test launches software or mutates the host.
- System adapter tests spy on process creation and prove argument-vector/no-shell/timeouts/output bounds.
- Integration smoke tests run only read operations on macOS and assert no mutation adapter exists in Phase 1.
- Packaging tests build wheel/sdist and run `macwise --help` from an isolated installation.

## Phase Boundary

Phase 1 is accepted only when the guided experience, application/Homebrew/drive inventory, explicit-versus-dependency distinction, JSON/Markdown audits, full command help contract, tests, and packaging evidence exist. Startup, usage, backup, and recommendation fields may be explicit unknowns until Phase 2; they must not be simulated.
