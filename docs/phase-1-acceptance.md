# Phase 1 Acceptance Audit

Date: 2026-07-17

Verdict: **PARTIAL**. The Phase 1 user experience, schema, reports, help contract, safety boundary, local package build, and MW-009 collector fields have direct evidence. Cross-parser hostile-metadata coverage, clean hosted platforms, public installation, and several later evidence fields remain open, so Phase 1 and the overall MacWise goal are not complete.

## Evidence scale

- **PASS**: current direct evidence covers the named requirement.
- **PARTIAL**: useful implementation exists, but required scope or proof is missing.
- **MISSING**: required behavior or evidence does not exist.

## Phase 1 deliverables

| Requirement | Status | Current evidence | Remaining gap |
|---|---|---|---|
| `macwise` guided menu | PASS | CLI tests cover all nine choices, interactive routing, and non-interactive no-block behavior; isolated wheel smoke ran the command. | None for Phase 1. |
| `macwise scan` | PASS | JSON, Markdown, and terminal formats are CLI-tested; real read-only JSON/Markdown smokes parsed successfully. | Terminal presentation can be polished further, but the command is functional. |
| Application inventory | PASS for Phase 1 deterministic fields | Synthetic tests and real smoke prove recursive default/approved-root scanning, plist identity/version, bundle size/location, signing publisher/team, architecture, point-in-time running state, App Store/system/Homebrew source signals, nested helpers/extensions, protected system context, partial limitations, no launch, and no symlink following. | Direct-download source remains unknown when no reliable receipt/cask/system signal exists; related user data and historical usage remain Phase 2. |
| Homebrew formula/cask inventory | PASS for MW-009 fields; PARTIAL for full product evidence | Fixtures and real smoke prove formulae/casks, versions, explicit leaves, dependencies/reverse dependencies, services, descriptions/homepages, install paths/storage location/sizes, executables, linked/pinned state, caveats, approved project references, app artifacts, and guarded cask/app identity correlation. | Configuration locations, install dates, and broader project/shell/config references remain incomplete; no unapproved home scan is performed. |
| Explicit versus dependency distinction | PASS | Model and collector tests classify `openssl@3`-style libraries as dependencies and retain reverse dependencies. | Recommendation use will be re-audited before planning. |
| Drive inventory | PASS for Phase 1 deterministic fields | Plist/text fixtures and real smoke prove capacity/free space, filesystem, internal/external, mount state, read-only, encryption, removable, protocol, health, parent/whole-disk/APFS physical-store hierarchy, ownership, Time Machine role/destination/exclusion facts, unavailable sources, and guarded path resolution. | These volume facts do not prove path-level backup coverage; richer backup history remains later work. |
| Versioned JSON audit | PASS | Schema version 2 model round-trip, schema-version-1 migration, future-version rejection, deterministic renderer/CLI tests, and real parse smoke. | Add a migration for every future schema change. |
| Markdown audit | PASS | Stable renderer tests and real smoke prove verified inventory, separate limitations/unknowns, read-only statement, and absence of “never used.” | Richer evidence sections arrive in Phase 2. |
| Excellent `--help` | PASS | A parameterized matrix covers 24 root/nested command surfaces for useful-when, safety, examples, and next steps. Manual wheel help smoke covers root, scan, review, and nested review. | Re-audit when later-phase behavior replaces refusals. |
| Tests | PASS for current behavior | Fresh local gate: 94 tests, Ruff format/lint, Pyright, sdist/wheel build, skill validation, workflow parse, isolated Python 3.12 wheel install, and real read-only scan smokes. | CI has not run on GitHub yet; MW-010 hostile-metadata coverage is still open. |

## Cross-cutting safety and release evidence

| Requirement | Status | Evidence and limitation |
|---|---|---|
| Audit mode performs no software mutations | PASS for implemented paths | Collectors expose read operations only; subprocess tests prove fixed programs, argument vectors, `shell=False`, bounded environment/time/output, and inert hostile arguments. Real smokes saved no audit. |
| Missing use data is not “never used” | PASS | Model, report, CLI, and real-smoke assertions prohibit that phrase and label usage unknown. |
| Homebrew dependencies are not ordinary selected apps | PASS | Explicit/dependency and reverse-dependency regression tests. |
| Malicious metadata cannot inject shell commands | PARTIAL | Command-boundary hostile-argument test passes and Markdown metacharacters are escaped. Malicious plist/Homebrew/disk fixture coverage and future AI prompt-injection integration tests remain. |
| Public repository foundation | PASS locally | README, MIT license, security/contribution/changelog/privacy/threat-model docs, valid initial skill, and CI workflow exist; repository privacy contract passes. | No public GitHub remote or hosted CI result exists yet. |
| `pipx install macwise` | MISSING publicly | Wheel installs in a fresh Python 3.12 environment. The package is not published and `pipx` is unavailable on the development host. |
| `brew install deesatzed/tap/macwise` | MISSING | No tap formula or public release artifact exists. |
| `macwise setup codex` and `$macwise` | PARTIAL | Initial read-only skill validates; CLI setup safely refuses. Installation, typed tools, and integration tests remain Phase 6. |

## Fresh verification commands

```bash
uv run pytest -q
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv build
python3 /path/to/skill-creator/scripts/quick_validate.py skills/macwise
```

Additional evidence used an isolated Python 3.12 virtual environment to install the built wheel and smoke `--version`, root help, no-argument guidance, scan help, nested help, and safe Codex-setup refusal. Real JSON and Markdown scans were captured in memory, structurally checked, summarized without names or paths, and discarded.

## Required next work

1. Add malicious metadata fixtures across every parser and renderer under MW-010.
2. Close the remaining full-product evidence fields in the owning later phase without broad unapproved scans.
3. Re-run this audit and clean-platform acceptance before declaring Phase 1 complete.
4. Continue Phase 2 explain/review evidence only after the deterministic substrate is complete enough to support it honestly.
