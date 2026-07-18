# RELEASE_CHECKLIST.md

## Release Scope

MacWise `1.0.0rc1`: Python wheel/sdist, optional Codex payload, release workflow,
pipx install path, and Homebrew tap candidate. No external publication is authorized.

## Go / No-Go Decision

**Conditional Go for a local release candidate; No-Go for public publication.** Local
build, test, pipx, artifact, workflow, privacy, and formula-structure gates have direct
evidence. Hosted CI/release, PyPI trusted-publisher configuration, tap ownership, public
install commands, and a clean Homebrew install remain external gates. Local strict
Homebrew audit is also blocked by Xcode 26.4 while Homebrew requires 27.0.

## Checklist

| Area | Status | Evidence | Notes |
|---|---|---|---|
| Build | PASS local | Reproducible wheel/sdist build and content/hash tests | Public artifact URLs do not exist yet. |
| Tests | PASS local | 377 tests on Python 3.12 and 3.13 | Hosted matrix has not run. |
| Lint/Typecheck | PASS local | Ruff format/lint and strict Pyright | Re-run on release commit. |
| Security | PASS local / external open | `pip-audit` found no known installed dependency vulnerabilities; read/mutation boundary tests pass | RC is not production certification. |
| Privacy | PASS local | Public candidate scan rejects current home, hostname, and secret-shaped assignments | Re-scan downloaded public artifacts. |
| Environment Variables | PASS structural | Release uses PyPI OIDC and no package token; runtime child environments are reduced | Protected `pypi` environment must be configured remotely. |
| Documentation | PASS candidate | README, getting-started, demo, privacy, threat model, security policy, changelog | Install commands remain labeled unpublished. |
| Error Handling | PASS local | Refusal/recovery/help contracts and hostile/error suites pass | Real platform combinations remain broader. |
| Logging | PASS local | STDIO MCP protocol test rejects traceback/stdout corruption; no telemetry | Terminal/shell/Codex may retain output independently. |
| Rollback | PASS scoped | Cleanup journal/undo and setup compensation/recovery suites pass | Homebrew reinstall remains best-effort. |
| pipx | PASS local | Real isolated pipx installs the built wheel under Python 3.12 | Public index install unverified. |
| Homebrew | PARTIAL | Exact RC/source/resource hashes including optional extras, formula test stanza, `brew style`, and an ephemeral hosted audit/install/test job are defined | Hosted job has not run; local strict audit is Xcode-blocked. |
| Release workflow | PASS structural | Exact RC tag/version gate, build once, pinned actions, OIDC, checksums, prerelease ordering, manual public pipx/brew smoke, and cross-channel verifier tests | Workflows have not run on GitHub. |

## Known Blockers

1. No explicit authority to tag, push, publish to PyPI/GitHub, or create/update a tap.
2. Hosted Linux/macOS CI and release workflow have no run evidence.
3. PyPI trusted-publishing environment and tap ownership are not confirmed.
4. Public artifacts do not exist, so public pipx/Homebrew commands cannot be tested.
5. Local strict Homebrew audit requires Xcode 27.0; this host has 26.4.

## Accepted Risks

- `1.0.0rc1` communicates pre-release status and does not claim universal permission or
  production behavior.
- Homebrew resource sdists may expose build-system issues only a clean hosted install can
  arbitrate; the formula is a candidate, not an accepted tap release.
- A live model session was not used to score Codex language/tool selection.

## Required Fixes Before Release

1. Obtain publication authority and configure protected external environments.
2. Run hosted CI, including its ephemeral local-artifact formula audit/install/test, and the release workflow.
3. Trigger the manual public-install workflow to verify pipx, Homebrew, checksums, PyPI, GitHub, and tap identity.
4. Update acceptance/checklist with those external results before calling the RC public.

## Rollback Plan

Do not publish if any gate fails. Before publication, rollback is a normal commit revert.
After an authorized prerelease, yank the PyPI file only for a material defect, mark the
GitHub prerelease withdrawn, revert the tap formula, publish an advisory, and prepare a
new RC version rather than replacing immutable artifacts.
