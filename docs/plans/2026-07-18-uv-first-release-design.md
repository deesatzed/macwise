# UV-First Release Design

## Decision

Make `uv tool install macwise` the primary beginner-facing installation path for the
first public release. Retain `pipx install macwise` as a documented alternative. Defer
Homebrew tap publication to a later milestone rather than blocking the first release.

## User experience

The shortest supported path is:

```zsh
uv tool install macwise
macwise
```

Documentation explains how to install `uv` when it is unavailable, labels `pipx` as an
alternative, and does not present the unavailable Homebrew command as usable today.
`uv pip install` is not the default because it requires the user to understand and
manage a Python environment; `uv tool install` provides an isolated command-line tool.

## Release architecture

PyPI remains the artifact authority. The GitHub release workflow publishes the Python
wheel and source distribution to PyPI and creates the matching GitHub prerelease. The
public installation smoke workflow verifies a clean `uv tool install` from PyPI and
cross-checks the installed version against the GitHub release artifacts.

The resource-locked Homebrew formula remains in the repository as deferred work and
prior technical evidence, but it is removed from the first-release workflow, public
completion gate, and beginner installation instructions. A future milestone may update,
publish, and verify the separate tap without changing the first-release claim.

## Truth and testing

- Update `GOAL.md`, `DECISIONS.md`, `PROGRESS.md`, and `TASK_QUEUE.md` so the scope change
  is explicit and durable.
- Add repository tests that require UV-first documentation and a UV-only public install
  smoke, while rejecting an advertised public Homebrew command.
- Preserve tests for Homebrew inventory and cleanup behavior; deferring distribution
  does not remove MacWise's ability to understand or manage existing Homebrew software.
- Run the full local quality gate, commit, push, and require hosted CI.
- Clone the repository into a new temporary directory, build from that clone, install
  the resulting wheel using a clean UV tool directory, and exercise the novice path.

## Boundaries

- Do not create a Homebrew tap or claim Homebrew installation is available.
- Do not create a release tag or publish to PyPI during implementation verification.
- Do not remove Homebrew auditing and cleanup product features.
- Do not use the developer's existing global UV tool state for the clean-clone proof.
