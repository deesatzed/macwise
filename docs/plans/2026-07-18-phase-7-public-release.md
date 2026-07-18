# Phase 7 Public Release Implementation Plan

Date: 2026-07-18

## Task 1 — Release identity and metadata

- Set `1.0.0rc1`, RC classifiers, URLs, and supported-platform metadata.
- Add tests that inspect wheel/sdist metadata and reject development versions.
- Verify: focused repository tests, `uv build`, artifact inspection.

## Task 2 — Public documentation and demo

- Rewrite README install/status/Codex/safety guidance to current behavior.
- Add an end-to-end novice guide, release checklist, and synthetic transcript demo.
- Extend privacy scans to all public candidates and release artifacts.

## Task 3 — GitHub release automation

- Add an exact-tag, pinned-action, least-privilege workflow for build, test, provenance,
  PyPI trusted publishing, checksums, and prerelease creation.
- Add structural tests for tag/version matching, permissions, and forbidden secret/token
  patterns.

## Task 4 — pipx clean-install proof

- Build the RC wheel and install it into an isolated pipx home using only the artifact.
- Smoke version, guided UX, scan help, setup help, and installed STDIO tool call.
- Save only aggregate evidence.

## Task 5 — Homebrew tap candidate

- Generate a tap-shaped formula with exact source/resource hashes.
- Add formula structure, version, checksum, dependency, and CLI test assertions.
- Run `brew audit`, `brew install`, and formula test in isolated/local mode if the current
  Homebrew supports it without external publication; otherwise record the exact blocker.

## Task 6 — Security and release readiness

- Update security/privacy/threat-model scope for RC behavior and release supply chain.
- Run dependency/artifact/privacy/stub/skip checks and independent adversarial review.
- Resolve every Critical/Important finding test-first.

## Task 7 — Final acceptance and handoff

- Produce `docs/phase-7-acceptance.md` mapping all 15 novice tests and Definition of Done.
- Mark local proof separately from hosted/public proof.
- Do not tag, push, publish, or create the tap until the user authorizes external actions.

Each task uses a failing test first, a minimal implementation, focused/full verification,
truth-file updates, and one logical commit.
