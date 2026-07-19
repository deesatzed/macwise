# Phase 7 Acceptance Audit

Date: 2026-07-18

Verdict: **PASS for the local and hosted `1.0.0rc1` candidate; BLOCKED for public
release.** D-035 makes `uv tool install macwise` the primary first-release path, retains
pipx as an alternative, and defers Homebrew distribution to a later milestone.

## Novice acceptance map

| # | Outcome | Evidence | Remaining boundary |
|---:|---|---|---|
| 1 | Install with one command | Local artifact installs through isolated UV tool state; prior isolated pipx proof also passes | Public PyPI UV-tool install requires publication. |
| 2 | Run without subcommands | Guided/noninteractive CLI and installed-wheel smokes pass | None local. |
| 3-8 | Understand software, usage, overlap, storage, and backup limits | Phase 1-3 acceptance suites pass | Host evidence may remain explicitly unknown. |
| 9-12 | Plan, preview, apply, and undo safely | Immutable planning, approval, synthetic mutation, verification, and recovery suites pass | Live user software mutation is not claimed. |
| 13-14 | Set up and use Codex | Plugin setup/recovery and eight read-only tool proofs pass | No hosted model-quality claim. |
| 15 | Receive useful help/errors | Root, nested, refusal, and recovery help contracts pass | None local. |
| 16 | Assess whether findings and output are useful | Separate deterministic Opportunity Profile and MacWise Usefulness Score expose component counts, reasons, and limitations | Scores describe evidence and structure, not personalized outcomes. |
| 17 | Give a novice one clear starting journey | `macwise checkup` performs one fresh read-only collection, shows at most five evidence-linked priorities, supports repeated guided review, unknown-item review and plan preview, and ends with an explicit session/no-change summary; the local/full/isolated-wheel/real-Mac/hosted gates and user-supplied desktop PDF inspection pass | The user explicitly waived a separate mobile PDF export; PyPI publication remains a separate external release gate. |

## Release evidence

- The complete local suite, Ruff format/lint, Pyright, build, privacy, artifact, and
  release-workflow contracts pass.
- Hosted run `29641643615` passed Linux, macOS 15, macOS 26, and Python 3.12-3.14.
- That run also passed the historical resource-locked Homebrew candidate proof before
  D-035 deferred Homebrew distribution; this remains technical evidence, not a public
  Homebrew claim or first-release gate.
- The release workflow is exact-RC-tag gated, builds artifacts once, uses PyPI OIDC,
  checks artifacts, publishes checksums, and creates a GitHub prerelease only after PyPI.
- The manual public smoke now installs through isolated `uv tool` state and verifies
  PyPI/GitHub artifact and checksum identity.
- The README and framework-free landing page explain the candidate honestly, use sanitized
  examples, distinguish trusted-checkout evaluation from after-publication installation, and
  expose local-link/privacy contracts. Desktop and 390-pixel mobile Chrome renders were inspected
  locally without remote assets or scripts.
- Hosted run `29646278423` passed all nine jobs after the final real-Mac UX corrections. Launch
  documentation commit `991a608` then passed all nine Linux/macOS 15/macOS 26 and Python
  3.12-3.14 jobs in run `29652271086`, including privacy contracts and package builds.
- A private real-Mac score produced a 70/100 Opportunity Profile and 86/100 Usefulness Score in
  25.94 seconds. Aggregate cross-checks confirmed 28 startup records, 4 comparison-worthy overlap
  relations out of 6, 22 applications at least 500 MiB out of 69 measured, 53 unknown-purpose
  records, zero supported non-use findings, and a stale-backup warning. No name or path entered
  `docs/scorecard-evaluation.md` or the public examples.
- Scorecard commit `3953348` passed all nine hosted matrix jobs in run `29653569296` after a clean
  public-clone locked install and focused score/privacy contract proof.

## Claim validation

**PASS:** “The repository contains a locally and hosted-CI-verified MacWise
`1.0.0rc1` candidate with a UV-first release path.”

**BLOCK:** “MacWise `1.0.0rc1` is publicly released.” That claim still requires the
GitHub `pypi` environment, PyPI pending trusted publisher, authorized RC tag, successful
release workflow, and clean public UV-tool installation.

The public GitHub repository now exists. The PyPI project remains absent until the
trusted publisher first publishes. The absent Homebrew tap is intentional deferred
scope rather than a release blocker.

The shared updateable knowledge database is also deferred to a later phase. `1.0.0rc1` performs
ordinary scans from local evidence and uses only its versioned bundled role catalog.
