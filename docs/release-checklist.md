# Release checklist

## Local candidate gates

- [x] Exact `1.0.0rc1` identity matches package, plugin, changelog, and workflow.
- [x] Python 3.12, 3.13, and 3.14 tests pass.
- [x] Ruff, formatting, Pyright, build, artifact, privacy, and secret checks pass.
- [x] Clean isolated `uv tool install` from the built wheel succeeds.
- [x] pipx alternative remains installable from the built wheel.
- [x] Independent security/release reviews have no open Critical or Important finding.
- [x] README and responsive static landing page distinguish verified candidate evidence from
  unpublished registry/release commands and contain only sanitized examples.

## External authority gates

- [ ] User confirms release authority for `deesatzed/macwise`.
- [ ] GitHub `pypi` environment and PyPI trusted publisher are configured.
- [x] Hosted Linux/macOS CI succeeds on the accepted candidate baseline; it must run again on the
  final release commit.
- [ ] Exact RC tag triggers the release workflow successfully.
- [ ] Published artifacts and checksums match locally accepted artifacts.
- [ ] Clean public `uv tool install macwise` succeeds.
- [ ] Public verifier confirms PyPI and GitHub artifact/checksum identity.

Homebrew distribution is explicitly deferred and is not a first-release gate. Do not
check an external gate from a local approximation.

The shared online knowledge database is also deferred. The release candidate uses only local
collection and its versioned bundled catalog.
