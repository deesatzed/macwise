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

## Codex and future AI features

The included skill is an initial local read-only workflow. `macwise setup codex` remains disabled. Before Phase 6 enables integration, documentation and tests must specify which local evidence is exposed to Codex and keep cleanup actions behind the same planning and approval gates.

Future optional research or AI providers must be opt-in, selective, source-attributed, and documented. Local metadata must never be treated as AI instructions.

## Sharing reports

Review and redact reports before attaching them to issues or conversations. Prefer synthetic fixtures. Remove usernames, hostnames, paths, volume names, project references, and software that could identify a person or organization.
