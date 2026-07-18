# RELEASE_CHECKLIST.md

## Release Scope

MacWise `1.0.0rc1`: Python wheel/sdist on PyPI, `uv tool install macwise` as the
primary UX, pipx as an alternative, optional Codex payload, and a matching GitHub
prerelease. Homebrew distribution is deferred to a later milestone.

## Current Decision

**Conditional Go.** Local build/tests and hosted compatibility CI have direct evidence.
Public publication still requires PyPI trusted-publisher configuration, an authorized RC
tag, a successful release workflow, and a clean public UV-tool install.

## Checklist

| Area | Status | Evidence | Remaining gate |
|---|---|---|---|
| Build | PASS local | Reproducible wheel/sdist and content tests | Compare published artifacts. |
| Tests | PASS local/hosted | 378 local tests; Linux/macOS 15/macOS 26 with Python 3.12-3.14 passed | Re-run on final release commit. |
| Quality | PASS local/hosted | Ruff format/lint and Pyright | Re-run on final release commit. |
| Security/privacy | PASS candidate | Boundary, hostile-input, privacy, and secret-shape tests | Re-scan published artifacts. |
| UV tool | PASS from local artifact | Isolated clean-clone proof required after this transition | Public PyPI install unverified. |
| pipx alternative | PASS from local artifact | Prior isolated pipx proof | Public PyPI install unverified. |
| Release workflow | PASS structural | Exact RC tag, OIDC, build-once, checksums, prerelease ordering | Hosted release run unverified. |
| Homebrew distribution | DEFERRED | Formula candidate and prior hosted technical evidence retained | Not a first-release gate or claim. |

## Remaining Blockers

1. Configure the GitHub `pypi` environment and PyPI pending trusted publisher.
2. Push the authorized exact RC tag and require the release workflow to pass.
3. Run the manual public-install smoke and verify PyPI/GitHub artifact identity.
4. Record the public evidence before calling the RC released.

## Rollback

Do not publish if any gate fails. After an authorized prerelease, yank a materially
defective PyPI release, mark the GitHub prerelease withdrawn, publish an advisory, and
prepare a new RC rather than replacing immutable artifacts.
