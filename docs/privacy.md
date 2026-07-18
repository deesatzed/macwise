# Privacy

## Local-first behavior

MacWise inventories software and volumes locally. The current CLI does not send audit records to MacWise maintainers, an AI provider, or a hosted service. It does not require an account or API key.

Homebrew collection explicitly disables Homebrew auto-update and analytics for the bounded commands MacWise starts. MacWise does not web-search installed items during a normal scan.

## Data collected

A Phase 1 audit may contain:

- application names, bundle identifiers, versions, paths, and bundle sizes,
- Homebrew formula/cask names, versions, dependency relationships, service status, descriptions, and homepages,
- disk identifiers, volume names, mount points, capacity/free-space values, filesystem, encryption, and internal/external classification,
- collector timestamps, provenance, reliability, and limitations.

This information can reveal how a Mac is configured. Treat saved reports as private.

## Storage and retention

Terminal output is not persisted by MacWise. A report is written only when the user supplies `--output`; an existing file is not replaced without `--force`. Phase 1 has no background daemon, telemetry database, or cloud synchronization.

The shell, terminal, operating system, backup tools, or third-party logging software may retain command output independently of MacWise.

## Codex integration

`macwise setup codex` installs an optional local MacWise plugin and skill for the current
user. The plugin exposes eight typed read-only operations for audit health, software,
overlap, startup, storage, backups, and pure removal previews. It does not expose apply,
undo, approval, plan persistence, a generic shell, arbitrary filesystem access, or a
remote service.

The local server keeps one audit snapshot in process memory for conversational
consistency. It does not save that snapshot. Tool results contain bounded normalized
facts and may include software names, identifiers, versions, storage classification,
startup relationships, usage findings, backup configuration, and collector limitations.
Those results are provided to the active Codex session, whose own retention and privacy
terms remain separate from MacWise. Users should not invoke the integration for an audit
they do not want present in that session.

Setup writes only the owned personal plugin directory and MacWise's personal-marketplace
entry. It does not edit `~/.codex/config.toml`, require an API key, or contact a MacWise
service. Tests use isolated homes and fake Codex runners; local acceptance does not alter
the developer's live plugin installation.

Future optional research or other AI providers must be opt-in, selective,
source-attributed, and documented. Local metadata is untrusted evidence and must never be
treated as AI instructions.

## Sharing reports

Review and redact reports before attaching them to issues or conversations. Prefer synthetic fixtures. Remove usernames, hostnames, paths, volume names, project references, and software that could identify a person or organization.
