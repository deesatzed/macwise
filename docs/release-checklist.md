# Release checklist

## Local candidate gates

- [ ] Exact `1.0.0rc1` identity matches package, plugin, changelog, workflow, and formula.
- [ ] Python 3.12 and 3.13 full suites pass.
- [ ] Ruff, formatting, Pyright, build, artifact, privacy, and secret checks pass.
- [ ] Clean pipx install and installed-wheel STDIO call pass.
- [ ] Homebrew formula has exact hashes and passes the available local audit/install test.
- [ ] Hosted ephemeral formula audit/install/test succeeds from the exact built sdist.
- [ ] Independent security and release-readiness reviews have no open Critical/Important finding.
- [ ] Final acceptance distinguishes synthetic/local evidence from hosted/public evidence.

## External authority gates

- [ ] User confirms GitHub repository/tap ownership and release authority.
- [ ] Protected PyPI trusted-publishing environment is configured.
- [ ] Hosted Linux/macOS CI succeeds on the release commit.
- [ ] Exact RC tag triggers the release workflow successfully.
- [ ] Published artifacts and checksums match locally accepted artifacts.
- [ ] Clean public `pipx install macwise` succeeds.
- [ ] Clean public `brew install deesatzed/tap/macwise` succeeds.
- [ ] Cross-channel verifier confirms PyPI, GitHub artifacts/checksums, and tap formula agree.

Do not check an external gate from a local approximation.
