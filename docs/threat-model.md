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
- Cleanup execution is an approval-gated write boundary kept separate from collectors,
  inert plan models, and read-only review commands.

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

### Persisted planning-state tampering

Phase 4 stores complete immutable plan revisions in a local SQLite database only after an
explicit `macwise plan add`. Documents use a versioned strict schema, canonical JSON,
an integrity digest, append-only revision keys, and an atomic active pointer. The state
path refuses symbolic-link database targets, SQL values use bound parameters, and
corrupt, malformed, or future-schema state fails closed.

A persisted plan is **not execution authority**. It contains typed preview intent rather
than an arbitrary command, shell string, or executable. Phase 5 revalidates exact
identity, protection, dependencies, usage, related data, backup limitations, rollback,
and current host state before it constructs any allowlisted action. Hostile or stale
persisted values remain untrusted data.

### Approval, execution journals, and replay

Approval is an exact `APPLY` or `UNDO` phrase containing a 16-character display
fingerprint. The full plan or manifest digest remains the internal identity check, so a
matching short prefix cannot authorize a changed active document. Apply and undo share a
symlink-safe advisory state lock with plan and execution stores. Complete immutable
manifest revisions are appended before mutation and after each observed transition. An
unresolved partial, verification-failed, interrupted, or undo-partial run blocks ordinary
continuation.

### Allowlisted Phase 5 mutation boundary

Manual applications can only move through an exclusive no-replace, descriptor-relative,
same-filesystem rename from standard application roots to the current user's Trash. The
exact device, inode, and descriptor-read `Contents/Info.plist` identity are verified before
and after movement; undo refuses an occupied or changed restore path.

Homebrew and launchctl actions use fixed executable paths, structured token/label
validators, `shell=False`, a reduced environment, timeouts, and bounded captured output.
The production runner drains stdout and stderr while retaining at most 64 KiB plus one
overflow byte per stream, so rejection does not depend on first buffering unbounded output.
No force, zap, cleanup, autoremove, discovered executable, LaunchDaemon, system domain, or
privilege elevation operation is available. Current-user LaunchAgent actions require the
exact direct plist path and unchanged SHA-256 content immediately before dispatch. Fresh
read-only audit and launchctl observations, not exit status, determine verified
after-state.

Related support data is never part of an action. Homebrew reinstall undo is explicitly
best-effort because a captured version may no longer be available. A failure after an
action enters `in_progress` is conservatively recorded as partial even when the adapter
reports failure, because mutation may already have occurred.

On command failure MacWise takes a fresh observation and records any safely observed
partial state, including the first half of a LaunchAgent disable/bootout sequence. After a
process interruption, separately approved undo classifies fresh state as unchanged,
applied, or ambiguous. It reverses only unchanged/applied states; ambiguous state remains
durably interrupted. Recovery history can reach an older still-applied run after a newer
run has already been fully undone.

## Remaining write-boundary requirements

Before public release, MacWise must continue to prove:

- exact unambiguous targets and protected-system rejection,
- dependency and path-specific backup preflight,
- immutable reviewed plans and exact previews,
- resilience to malicious names, symlinks, races, and changed state,
- clean installed-wheel synthetic execution and fake-runner recovery smokes,
- independent review closure and privacy-safe public artifacts,
- hosted CI and release-platform behavior without relabeling local evidence.

## Out of scope through Phase 5

MacWise does not claim malware detection, vulnerability scanning, complete backup
verification, complete usage history, arbitrary application uninstallation, privileged
cleanup, deletion of related data, exact-version Homebrew restoration, or production
safety. Local acceptance uses synthetic bundles and fake Homebrew/launchctl mutators; it
does not prove permissions or behavior for every real installed tool. macOS, Homebrew,
Codex, terminal history, backups, and third-party security products retain their own trust
and privacy boundaries.
