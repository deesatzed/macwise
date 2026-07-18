# Phase 7 Public Release Design

Date: 2026-07-18
Status: Approved by the autonomous `GOAL.md` continuation contract

## Outcome

Produce a locally verified `1.0.0rc1` release candidate with truthful pipx, Homebrew-tap,
GitHub release, documentation, demo, privacy, and security surfaces. Do not publish,
create remote repositories, tags, releases, or credentials without explicit authority.

## Options considered

1. **PyPI-first release plus a separately maintained Homebrew tap (selected).** Build and
   attest Python artifacts once; test pipx directly; maintain a resource-locked formula
   in a tap-shaped local fixture. This matches normal user commands and separates package
   publication from tap ownership.
2. GitHub-wheel wrapper formula. Simpler formula, but bypasses normal Python dependency
   packaging and is less conventional to maintain.
3. pipx-only release candidate. Fastest, but fails the explicit Homebrew deliverable.

## Architecture

- `pyproject.toml` is the single version and package-metadata authority.
- `.github/workflows/release.yml` builds once, verifies artifacts, publishes to PyPI via
  trusted publishing, creates a GitHub prerelease, and emits checksums only on an exact
  `v1.0.0rcN` tag.
- `packaging/homebrew/` is a tap-shaped, testable publication candidate. Its formula is
  generated from locked release inputs; placeholder hashes are forbidden.
- Clean pipx and Homebrew tests use isolated state and a locally served release artifact.
- Public docs state available versus pending install paths from evidence, not aspiration.
- A deterministic transcript demo uses synthetic names and contains no host inventory.
- Publication is a separate manual authority boundary after local acceptance.

## Safety and truth boundaries

- Release automation has least privilege and pinned actions.
- PyPI uses OIDC trusted publishing; no long-lived token is stored in workflow text.
- Tap publication requires a separately scoped secret and is not attempted locally.
- No release artifact may contain current home paths, hostnames, secrets, audit reports,
  state databases, caches, or transaction remnants.
- `1.0.0rc1` is a release candidate, not a production-safety claim.
- Hosted CI, PyPI, GitHub release, and public tap results remain unverified until their
  external systems actually run.

## Acceptance gates

1. Exact version/metadata and artifact-content tests.
2. Clean Python 3.12 and 3.13 suites plus build.
3. Clean pipx install from the built wheel and core CLI/Codex-server smoke.
4. Formula audit plus isolated Homebrew install/test from a local artifact where Homebrew
   is available; otherwise an explicit external blocker remains.
5. Release workflow structural/security tests and local build/checksum simulation.
6. Synthetic demo and public privacy/secret scans.
7. Independent release-readiness review and final requirement audit.

