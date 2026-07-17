# RISK_NOTES.md

## Risks

| Risk | Severity | Why It Matters | Mitigation |
|---|---|---|---|
| The folder had no Git repository | Medium | There is no change history, rollback surface, or public-repo metadata yet. | Initialize Git after control docs are written; commit logical verified slices. |
| Greenfield scope spans seven substantial phases | High | A superficial broad scaffold could look complete while failing user acceptance. | Build tested vertical slices, keep the full task queue visible, and audit each explicit requirement before completion. |
| Host inventory parses variable/unavailable system tools | High | Incorrect parsers can misidentify apps, dependencies, drives, or backups. | Isolate adapters, consume plist/JSON where available, fixture-test variants, use timeouts, and preserve unknowns. |
| Read-only audit runs on a real Mac | Critical | Accidental mutation could harm the development machine. | Allowlist fixed read commands, use `shell=False`, prohibit mutation in collectors, and add mutation-spy tests. |
| Later cleanup changes installed software | Critical | A bad target or incomplete rollback can lose apps or data. | Defer execution until planning is mature; reject ambiguity/system targets; preserve data; Trash first; approval plus rollback manifest and undo. |
| Public output may expose private machine information | High | Reports, fixtures, logs, or docs could leak usernames, paths, or software inventory. | Synthetic fixtures, path redaction, privacy scan, and review before commits/releases. |
| Homebrew libraries may be presented as user choices | High | Users could remove indirect dependencies and break tools. | Record explicit/leaf status and reverse dependencies; test that libraries are not ordinary remove candidates. |
| Missing usage or backup metadata may be overinterpreted | High | Unsafe recommendations could be presented with false confidence. | Model evidence provenance and limitations; use `unknown`/`no reliable evidence` language by invariant. |
| External publishing needs credentials and ownership | Medium | Local readiness cannot prove public installation or release. | Prepare and test artifacts locally; stop for credentials/authority only when publication is the next action. |

## Safe Next Step

Establish the package/test harness and first failing CLI behavior test for the non-TTY no-argument guided experience. It exercises the primary UX without invoking any host collector or mutation.
