# Phase 7 Implementation Packet

## Task

Prepare and locally prove the `1.0.0rc1` public release candidate: pipx artifact,
Homebrew-tap candidate, public docs/demo, release automation, security review, and final
acceptance. External publication is excluded until separately authorized.

## Files and risk

| Surface | Expected change | Primary risk |
|---|---|---|
| `pyproject.toml`, lock, changelog | RC identity and metadata | Version/artifact drift |
| `.github/workflows/release.yml` | Pinned least-privilege release pipeline | Token or supply-chain misuse |
| `packaging/homebrew/` | Resource-locked tap candidate | Uninstallable or network-dependent formula |
| `README.md`, `docs/`, demo assets | Current novice instructions and proof | Aspirational claims or privacy leak |
| repository/release tests | Artifact, workflow, pipx, formula, privacy gates | Tests accidentally publish or mutate live state |

## Assumptions

- D-033 selects PyPI-first plus a separate tap and `1.0.0rc1`.
- Local work may build/install temporary artifacts but may not tag, push, publish, create
  remote repositories, or use credentials.
- Homebrew is locally available, but external artifact URLs do not exist until release.
- A deterministic synthetic transcript is an acceptable demo artifact for the RC.

## Non-goals

- Production deployment, public release, package signing with user credentials, tap
  creation, claims about hosted CI results, or live destructive host testing.
- New product behavior unrelated to packaging/release correctness.

## Execution

1. Test and set exact RC metadata/artifact contents.
2. Test and update public docs, synthetic demo, privacy/security statements.
3. Test and add pinned exact-tag release automation.
4. Prove isolated pipx install and installed CLI/MCP behavior.
5. Build and test a resource-locked Homebrew tap candidate as far as local infrastructure
   permits; record any external-only proof honestly.
6. Run security/release-readiness review and resolve Important findings test-first.
7. Produce final requirement audit and publication handoff.

## Acceptance

- Python 3.12/3.13 suites, Ruff, format, Pyright, build, artifact inspection, clean pipx,
  privacy/secret scans, workflow structure, plugin/skill validation, and release review pass.
- Formula has exact version and hashes and passes local audit/install/test when possible.
- All 15 novice acceptance tests are mapped to direct evidence or an explicit external
  blocker; no local approximation is relabeled as hosted/public proof.

## Rollback

Revert one logical task commit. Never remove user packages, taps, or credentials. All
install proofs use isolated homes/prefixes or disposable environments.

## Proceed decision

Proceed with local RC preparation. Stop before external publication because D-P03
credentials, tap ownership, and release authority remain unresolved.
