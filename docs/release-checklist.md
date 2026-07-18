# Release checklist

## Local candidate gates

- [ ] Exact `1.0.0rc1` identity matches package, plugin, changelog, and workflow.
- [ ] Python 3.12, 3.13, and 3.14 tests pass.
- [ ] Ruff, formatting, Pyright, build, artifact, privacy, and secret checks pass.
- [ ] Clean isolated `uv tool install` from the built wheel succeeds.
- [ ] pipx alternative remains installable from the built wheel.
- [ ] Independent security/release reviews have no open Critical or Important finding.

## External authority gates

- [ ] User confirms release authority for `deesatzed/macwise`.
- [ ] GitHub `pypi` environment and PyPI trusted publisher are configured.
- [ ] Hosted Linux/macOS CI succeeds on the release commit.
- [ ] Exact RC tag triggers the release workflow successfully.
- [ ] Published artifacts and checksums match locally accepted artifacts.
- [ ] Clean public `uv tool install macwise` succeeds.
- [ ] Public verifier confirms PyPI and GitHub artifact/checksum identity.

Homebrew distribution is explicitly deferred and is not a first-release gate. Do not
check an external gate from a local approximation.
