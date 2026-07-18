# MacWise Launch Documentation Implementation Plan

**Goal:** Deliver a truthful, polished README and static launch page, close documentation gaps,
and verify the public repository surface without publishing a package or release.

**Architecture:** Keep the Python application unchanged. Add a framework-free page under `docs/`,
reuse the existing documentation hierarchy, and extend repository contract tests only where they
provide durable protection against stale claims, broken local links, or privacy regressions.

---

## Task 1: Audit the public surface

**Files:** `README.md`, `docs/*.md`, `.github/workflows/*`, `tests/*`, `pyproject.toml`

1. Scan for TODOs, placeholders, stale release claims, missing links, skipped tests, and public
   privacy leaks.
2. Compare README claims with acceptance records, package metadata, and current CLI help.
3. Record only launch-relevant gaps; keep deferred Homebrew and shared-knowledge work out of scope.

## Task 2: Add documentation contract tests

**Files:** `tests/test_repository_contracts.py` or the nearest existing contract-test module

1. Add failing checks for the launch page, required README status language, and valid local links.
2. Observe the expected failures against the current public surface.
3. Keep the checks structural and truth-oriented rather than snapshotting prose or styling.

## Task 3: Rewrite the README launch journey

**Files:** `README.md`, `docs/getting-started.md`, `docs/demo.md`

1. Lead with the user outcome and current release-candidate status.
2. Separate future registry installation from trusted-checkout evaluation.
3. Add concise sanitized examples for storage, startup, overlap, explanations, and bounded detail.
4. Explain evidence sources, usefulness boundaries, and what requires user approval.
5. Correct hosted-CI status and link the landing page and focused documentation.

## Task 4: Build the static landing page

**Files:** `docs/index.html`, `docs/assets/macwise.css`

1. Implement the approved page hierarchy with semantic HTML and local CSS.
2. Include no trackers, remote fonts, scripts, machine data, or invented metrics.
3. Make navigation, focus states, contrast, responsive layout, and reduced-motion behavior clear.
4. Use sanitized terminal excerpts aligned with actual MacWise output categories.

## Task 5: Close documentation and truth-file gaps

**Files:** `docs/release-checklist.md`, `docs/phase-7-acceptance.md`, `PROGRESS.md`,
`TASK_QUEUE.md`, and any directly affected public documentation

1. Correct stale hosted-CI and launch-documentation status.
2. Record landing-page verification and remaining external publication blockers.
3. Ensure deferred Homebrew and shared knowledge work remain clearly classified as later work.

## Task 6: Verify and publish the repository changes

1. Run focused documentation-contract tests.
2. Render the page at desktop and mobile widths and inspect screenshots.
3. Run all tests, Ruff formatting/lint, Pyright, build, privacy/secret checks, link checks, workflow
   checks, and `git diff --check`.
4. Review the final diff for unsupported claims and private machine information.
5. Commit coherent changes, push `main`, and inspect the resulting hosted CI run. Do not publish
   PyPI, GitHub Release, GitHub Pages, or Homebrew artifacts in this pass.

