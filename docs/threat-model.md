# Threat Model

## Security goals

MacWise should let a user inspect software without executing discovered content, changing installed software during audit, leaking local inventory by default, or turning incomplete evidence into an unsafe cleanup recommendation.

## Assets

- Installed applications, command-line tools, services, and their configuration.
- User documents, application support data, models, databases, and containers.
- Audit reports containing paths and software inventory.
- Cleanup plans, approvals, rollback manifests, and future Codex configuration.

## Trust boundaries

- Application names, paths, plists, signatures, Homebrew JSON, service metadata, and disk metadata are untrusted input.
- macOS and Homebrew command output crosses into normalized models through bounded parsers.
- Terminal, Markdown, JSON, Codex prompts, and future typed tools are separate presentation/integration boundaries.
- Cleanup execution is a future write boundary and must remain separate from collectors.

## Threats and current mitigations

### Command injection

A malicious name or metadata value could contain shell syntax. MacWise selects programs from an enum-to-fixed-path allowlist, passes arguments as a sequence with `shell=False`, strips unrelated environment variables, applies time/output bounds, and never executes an app to identify it.

### Prompt injection through metadata

An app name, description, file, or web result could contain instructions aimed at an AI layer. The normalized value remains evidence data, not an instruction. The Codex skill requires deterministic CLI evidence first and forbids inventing or executing removal actions.

### Accidental host mutation during audit

Collectors expose read operations only. Homebrew auto-update and analytics are disabled for child commands. Tests inject command boundaries and use synthetic files; real smoke checks print summaries without saving local inventories.

### Unsafe dependency removal

Formulae are classified as explicit leaves or dependencies, with dependencies and reverse dependencies retained. Dependency libraries are not presented as independently selected applications.

### False claims from missing evidence

Collector errors become partial/unavailable status and limitations. Missing usage or backup data remains unknown. Reports explicitly state that usage, backup coverage, and removal safety are not established in Phase 1.

### Report disclosure

Reports are printed by default and saved only to an explicit path. Existing files require `--force`. Public fixtures and repository checks reject current machine identity and secret-shaped assignments.

## Future write-boundary requirements

Before cleanup is enabled, MacWise must prove:

- exact unambiguous targets and protected-system rejection,
- dependency and path-specific backup preflight,
- immutable reviewed plans and exact previews,
- action-time confirmation,
- allowlisted Trash/Homebrew/startup executors without arbitrary shell,
- rollback manifests, post-action verification, and tested undo,
- resilience to malicious names, symlinks, races, and changed state.

## Out of scope for Phase 1

Phase 1 does not claim malware detection, vulnerability scanning, complete backup verification, complete usage history, or safe software removal. macOS, Homebrew, Codex, terminal history, backups, and third-party security products retain their own trust and privacy boundaries.
