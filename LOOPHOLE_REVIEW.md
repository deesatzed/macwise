# Phase 7 Loophole Review

## Findings and mandatory mitigations

| Loophole | Severity | Mitigation |
|---|---|---|
| A workflow could publish from an arbitrary branch or mismatched tag. | Critical | Exact `v1.0.0rcN` tag gate, tag/package version comparison, environment protection, pinned actions. |
| A long-lived PyPI or tap token could leak. | Critical | PyPI OIDC only; no tap publication step until a separately scoped secret and repository are authorized. |
| A formula could depend on network access during install or placeholder hashes. | High | Lock every source/resource URL and SHA-256; tests reject placeholders and dynamic pip resolution. |
| A local wheel test could accidentally use the source checkout. | High | Isolated pipx/venv, unset `PYTHONPATH`, run outside the repo, inspect installed distribution path. |
| README could claim unpublished install commands work. | High | Separate RC candidate instructions from verified-current public availability. |
| Demo output could expose host inventory or imply mutation. | High | Synthetic fixture names only; public privacy scan includes demo assets. |
| RC version could diverge across package, plugin, changelog, workflow, and formula. | High | One metadata authority plus cross-surface repository tests. |
| GitHub release creation could be mistaken for tested hosted behavior. | Medium | Local structural validation only; acceptance labels hosted execution unverified. |
| Homebrew tests could alter the user's normal prefix. | Critical | Prefer isolated prefix/test-bot controls; never uninstall or overwrite an existing user formula. |
| A 1.0 RC label could be read as production-safety certification. | High | Repeat limitations in README, security policy, changelog, and acceptance audit. |

## Revised strategy

Build immutable Python artifacts first, derive every distribution surface from the exact
RC identity, exercise them only in disposable local environments, and leave external
publication as a deliberate handoff. No placeholder formula or simulated hosted result
may satisfy a gate.

## Proceed decision

Proceed locally. Publication remains blocked pending explicit authority and real external
infrastructure.
