# UV-First Release Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `uv tool install macwise` the primary first-release installation path, retain pipx as an alternative, and defer Homebrew distribution without removing Homebrew product features.

**Architecture:** PyPI remains the sole first-release package authority and GitHub Releases remains the matching artifact/checksum surface. Repository contracts drive documentation, workflow, verifier, and truth-file changes; the final proof uses a new clone and isolated UV tool directories.

**Tech Stack:** Python 3.12+, pytest, YAML GitHub Actions, uv, Git, GitHub CLI

---

### Task 1: Encode the UV-first release contract

**Files:**
- Modify: `tests/repository/test_public_foundation.py`
- Modify: `tests/repository/test_release_workflow.py`
- Modify: `tests/repository/test_public_release_verifier.py`

**Step 1: Write failing assertions**

Require the README to present `uv tool install macwise` before the pipx alternative and not advertise `brew install deesatzed/tap/macwise`. Require the manual public smoke to use an isolated UV tool installation and contain no Homebrew job. Require the public verifier to validate PyPI and GitHub release identity without requiring a tap.

**Step 2: Run the focused repository tests**

Run: `uv run pytest -q tests/repository/test_public_foundation.py tests/repository/test_release_workflow.py tests/repository/test_public_release_verifier.py`

Expected: FAIL on the existing pipx/Homebrew-first contract.

**Step 3: Commit the red contract**

```zsh
git add tests/repository
git commit -m "test: define UV-first release contract"
```

### Task 2: Implement UV-first documentation and release automation

**Files:**
- Modify: `README.md`
- Modify: `docs/getting-started.md`
- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/public-install-smoke.yml`
- Modify: `scripts/verify_public_release.py`

**Step 1: Update beginner installation**

Show `uv tool install macwise` followed by `macwise`; explain `pipx install macwise` as an alternative. Remove the unavailable Homebrew installation command from current instructions and label Homebrew distribution as deferred.

**Step 2: Remove Homebrew from the first-release gates**

Delete the Homebrew candidate CI job. Replace the public smoke's pipx/Homebrew jobs with a clean UV-tool job on macOS 26 and make cross-channel verification depend on that job. Remove tap retrieval and formula-version validation from `verify_public_release.py` while preserving PyPI, GitHub release, artifact, and checksum checks.

**Step 3: Run the focused repository tests**

Run: `uv run pytest -q tests/repository/test_public_foundation.py tests/repository/test_release_workflow.py tests/repository/test_public_release_verifier.py`

Expected: PASS.

**Step 4: Commit implementation**

```zsh
git add README.md docs/getting-started.md .github/workflows scripts/verify_public_release.py
git commit -m "feat: make UV the primary install path"
```

### Task 3: Reconcile project truth and release checklists

**Files:**
- Modify: `GOAL.md`
- Modify: `DECISIONS.md`
- Modify: `PROGRESS.md`
- Modify: `TASK_QUEUE.md`
- Modify: `RELEASE_CHECKLIST.md`
- Modify: `docs/release-checklist.md`
- Modify: `docs/phase-1-acceptance.md`
- Modify: `docs/phase-3-acceptance.md`
- Modify: `docs/phase-5-acceptance.md`
- Modify: `docs/phase-7-acceptance.md`

**Step 1: Record the scope change**

State that UV/PyPI is the first-release requirement, pipx is an alternative, and Homebrew distribution is a future milestone. Preserve all Homebrew inventory, analysis, planning, execution, and safety requirements.

**Step 2: Reconcile acceptance language**

Remove the Homebrew tap from current public-release blockers and checklists. Preserve historical evidence as dated history rather than rewriting past outcomes.

**Step 3: Run truth and privacy contracts**

Run: `uv run pytest -q tests/repository`

Expected: PASS.

**Step 4: Commit truth updates**

```zsh
git add GOAL.md DECISIONS.md PROGRESS.md TASK_QUEUE.md RELEASE_CHECKLIST.md docs
git commit -m "docs: defer Homebrew distribution"
```

### Task 4: Full verification and publication to GitHub

**Files:**
- Verify: entire repository

**Step 1: Run the complete local gate**

Run: `uv run pytest -q`

Expected: all tests pass.

Run: `uv run ruff format --check .`

Expected: no files need formatting.

Run: `uv run ruff check .`

Expected: all checks pass.

Run: `uv run pyright`

Expected: zero errors.

Run: `uv build`

Expected: wheel and source distribution build successfully.

Run: `git diff --check`

Expected: no output.

**Step 2: Push main and watch hosted CI**

Run: `git push origin main`

Run: `gh run watch <new-run-id> --exit-status`

Expected: current Linux/macOS and Python matrix passes without a Homebrew distribution job.

### Task 5: Fresh-clone novice run-through

**Files:**
- Verify: a new temporary clone outside the working repository

**Step 1: Clone from GitHub**

Create a new temporary directory and clone `https://github.com/deesatzed/macwise.git`. Verify the clone's HEAD matches `origin/main` and its worktree is clean.

**Step 2: Build from the clone**

Run `uv build` inside the clone and identify the exact `macwise-1.0.0rc1` wheel.

**Step 3: Install with isolated UV tool state**

Set temporary `UV_TOOL_DIR` and `UV_TOOL_BIN_DIR`, then run `uv tool install <wheel-path>`. Do not reuse or modify the developer's global UV tool installation.

**Step 4: Exercise the novice path**

Run the isolated `macwise --version`, `macwise --help`, no-argument guided entry in noninteractive mode, `macwise scan --help`, and `macwise setup codex --help`. Confirm expected exit codes and beginner-facing output.

**Step 5: Record evidence**

Append the clone path, commit SHA, exact commands, versions, and results to `PROGRESS.md`; do not persist machine inventory. Commit and push the evidence update, then confirm the final documentation-only CI run.
