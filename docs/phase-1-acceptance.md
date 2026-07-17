# Phase 1 Acceptance Audit

Date: 2026-07-17

Verdict: **PARTIAL**. The Phase 1 user experience, schema, reports, help contract, safety boundary, local package build, and core collectors have direct evidence. Several inventory fields explicitly required by `GOAL.md` are not implemented, so Phase 1 and the overall MacWise goal remain open.

## Evidence scale

- **PASS**: current direct evidence covers the named requirement.
- **PARTIAL**: useful implementation exists, but required scope or proof is missing.
- **MISSING**: required behavior or evidence does not exist.

## Phase 1 deliverables

| Requirement | Status | Current evidence | Remaining gap |
|---|---|---|---|
| `macwise` guided menu | PASS | CLI tests cover all nine choices, interactive routing, and non-interactive no-block behavior; isolated wheel smoke ran the command. | None for Phase 1. |
| `macwise scan` | PASS | JSON, Markdown, and terminal formats are CLI-tested; real read-only JSON/Markdown smokes parsed successfully. | Terminal presentation can be polished further, but the command is functional. |
| Application inventory | PARTIAL | Synthetic tests prove recursive approved-root scanning, plist identity/version, bundle size, storage location, partial limitations, no launch, and no symlink following. | Publisher/signing identity, architecture, running state, installation source, helpers/extensions, protected/system context, and configurable user-approved external roots are missing. |
| Homebrew formula/cask inventory | PARTIAL | Fixtures and a real smoke prove formulae/casks, versions, explicit leaves, dependencies/reverse dependencies, services, descriptions/homepages, and cask app artifacts. | Installed sizes, executables, project references, linked/pinned state, caveats, and app/cask duplication are missing. |
| Explicit versus dependency distinction | PASS | Model and collector tests classify `openssl@3`-style libraries as dependencies and retain reverse dependencies. | Recommendation use will be re-audited before planning. |
| Drive inventory | PARTIAL | Plist tests and real smoke prove capacity/free space, filesystem, internal/external, mount state, read-only, encryption, removable, protocol, health, unavailable disks, and guarded path resolution. | Physical-disk/APFS-container hierarchy, ownership, Time Machine roles/exclusions, and richer mount/backup relationships are missing. |
| Versioned JSON audit | PASS | Schema version 1 model round-trip, deterministic renderer tests, CLI format test, and real parse smoke. | Migration strategy is needed before schema version 2. |
| Markdown audit | PASS | Stable renderer tests and real smoke prove verified inventory, separate limitations/unknowns, read-only statement, and absence of “never used.” | Richer evidence sections arrive in Phase 2. |
| Excellent `--help` | PASS | A parameterized matrix covers 24 root/nested command surfaces for useful-when, safety, examples, and next steps. Manual wheel help smoke covers root, scan, review, and nested review. | Re-audit when later-phase behavior replaces refusals. |
| Tests | PASS for current behavior | Fresh local gate: 76 tests, Ruff format/lint, Pyright, sdist/wheel build. | CI has not run on GitHub yet; missing collector fields need their own tests. |

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

1. Close the application, Homebrew, and drive inventory field gaps above with fixture-backed tests.
2. Add malicious metadata fixtures across every parser and renderer.
3. Re-run this audit before declaring Phase 1 complete.
4. Continue Phase 2 explain/review evidence only after the deterministic substrate is complete enough to support it honestly.
