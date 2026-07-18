# Real-Mac UX Correction Design

## Context

A clean clone and isolated `uv tool install .` succeeded on macOS 27, but the live walkthrough exposed correctness and usability defects that unit tests had not represented.

## Design

MacWise will keep the existing collector/model/CLI architecture and add a consistent novice-facing summary layer. Default terminal views will prioritize decisions and bounded results; `--all` will expose complete inventories when needed. Existing deterministic subcommands remain available, and `macwise overlap` becomes a discoverable alias for the existing role-aware overlap review.

The storage collector will interpret current APFS metadata correctly: when `FreeSpace` is zero or unavailable for a mounted APFS volume, `APFSContainerFree` is the authoritative fallback. The default storage view will show only mounted volumes, use human-readable capacity/free-space values, and never turn missing evidence into zero. Unmounted devices remain in structured audit evidence rather than crowding the default view.

Homebrew, startup, backup-path, unknown-purpose, and largest-application views will show bounded summaries and explain how to request full detail. Largest sizes will use IEC units. Backup output will foreground destination and last-verifiable date, including an age warning when stale, while relegating path exclusions to `--all`.

Overlap analysis will not label parallel versioned formulae such as `python@3.12` and `python@3.13` as exact duplicate installations. Explain output will use catalog roles as a purpose fallback when a prose description is absent, preventing contradictory “unknown purpose” plus known-role output. Common-app catalog coverage may be expanded only through explicit stable identifiers or exact normalized names; no fuzzy purpose guessing is introduced.

## Verification

Each observed defect receives a failing behavioral regression test before production changes. After narrow red/green cycles, run the full unit suite, formatting, lint, type checking, privacy checks, and package build. Then clone the pushed commit into a new temporary directory, install it into isolated `uv` tool directories, and autonomously rerun version, doctor, scan, Homebrew, startup, overlaps, largest, unused, unknown, explain, compare, storage, and backups. Compare storage figures with `df` and delete all temporary private audit data afterward.

