# Phase 2 Acceptance Audit

Date: 2026-07-17

Verdict: **PASS for MW-100 local read-only scope**. Phase 2 explain/review behavior,
schema migration, evidence collection, deterministic analysis, reports, package build,
clean wheel installation, and real-Mac read-only execution have direct evidence. This is
not a production-readiness or overall-goal verdict: hosted CI/public installation remains
open under MW-011/MW-600, and Phase 3+ intelligence and all mutating behavior remain
disabled.

## Acceptance evidence

| Requirement | Verdict | Direct evidence | Honest limitation |
|---|---|---|---|
| Schema 3 and older audit compatibility | PASS | Model/report tests round-trip startup, path, backup, and basis-tagged findings; schema 1 and 2 migrate in memory; schema 4 is rejected. | Every future schema change still needs an explicit migration. |
| Stable exact and qualified matching | PASS | CLI tests prove exact cross-type ambiguity refuses and `app:`, `cask:`, and `formula:` qualification resolves the intended type. | Partial-name matches can still be ambiguous and correctly refuse. |
| Multi-signal usage labels | PASS | Table tests cover running/service, recent Spotlight, dependency/project, startup/configured, stale-positive, no-evidence, and user-confirmed paths with precedence, basis, confidence, and reasons. | Point-in-time local evidence is not a complete usage history. |
| Startup inventory and ownership | PASS | Plist/Homebrew fixtures cover launch agents, launch daemons, services, exact owner matches, ambiguous owners, malformed input, symlinks, and unknown enabled/running state. | Login/background item APIs and every extension class are not yet exhaustive; absent data remains unknown. |
| Related-data measurements | PASS | Collector tests prove allowlisted identifier/name-derived Library paths, bounded traversal, no directory-symlink following, size/location/recency facts, and partial limits. | Measurements are estimates, not a full home-directory inventory. |
| Backup facts without coverage claims | PASS | Backup tests cover configuration, available destinations, last-verifiable timestamp, path exclusion tri-state, partial command failure, and preservation of existing facts; no `covered` field exists. | Configuration, timestamp, and non-exclusion do not prove recoverability. |
| `macwise explain` | PASS | Output tests cover four basis sections, usage reason, startup state, related path size/location, backup limitation, ambiguity, sanitization, read-only wording, and unavailable recommendation. | Overlap, learning value, and recommendation remain Phase 3+. |
| `macwise review unused` | PASS | Tests prove only `possibly_unused` and `user_confirmed_unused` appear and that missing evidence never qualifies an item. | The command does not create user confirmations yet. |
| `macwise startup` and `macwise backups` | PASS | Tests cover owner labels, tri-state state, destinations, timestamp, exclusions, limitations, and explicit refusal to infer coverage. | Collector limitations remain visible on hosts where metadata is unavailable. |
| Markdown and hostile rendering | PASS | Reports render verified/inferred/user-confirmed/unknown findings plus startup/data/backup sections; the hostile suite asserts the exact seven allowed level-2 headings and rejects injected structure/control text. | Raw JSON intentionally retains provenance values and must continue to be treated as untrusted data. |

## Fresh verification

- Python 3.12.11: 118 tests passed.
- Python 3.13.13: 118 tests passed.
- Ruff lint and format checks passed; Pyright reported 0 errors.
- `uv build` produced `macwise-0.1.0a0` wheel and source distribution.
- The repository privacy contract reported 5 passing tests.
- The bundled read-only skill validated; the pinned workflow parsed as YAML.
- A fresh Python 3.12 environment installed the wheel and passed version, root, explain,
  review-unused, startup, and backup help smokes. The installed wheel also rendered a
  synthetic Phase 2 report correctly.
- Scoped TODO/FIXME/HACK/XXX/NotImplemented and skipped/xfail scans returned no matches.

## Real read-only evidence

One in-memory audit returned schema 3 with 325 software records, 325 findings, 28 startup
records, 97 related paths, and six usage-label kinds in 25.54 seconds. JSON round-trip,
the seven-heading Markdown allowlist, absence of “never used,” and absence of a backup
coverage field all passed. No inventory was saved.

A second aggregate-only run completed in 19.2 seconds. Storage, Homebrew, and backup
collectors were complete; application, startup, and usage collectors were partial with
11, 7, and 4 explicit limitations respectively. Backup configuration, an available
destination, and a last-verifiable timestamp were observed, but are not represented as
coverage. Partial collector results are acceptable under the product contract because
they remain qualified rather than discarded or promoted to negative conclusions.

## Claim validation

| Completion requirement | Result | Evidence |
|---|---|---|
| Acceptance criteria defined and met | PASS | `IMPLEMENTATION_PACKET.md`, the Phase 2 plan, and the table above. |
| Tests exist and pass | PASS | Focused model/collector/service/CLI/report/security tests plus both 118-test version runs. |
| No blocking scoped stubs | PASS | Scoped marker and skipped-test scans returned no matches. |
| Review performed | PASS | Codex inspected the complete diff, failure paths, hostile rendering, real collector states, and package output; tests arbitrate acceptance. Independent delegation is optional and was not required. |

**Claim verdict: PASS** for “MW-100 Phase 2 local read-only scope is complete.”

## Still open

1. MW-011 hosted Linux/macOS CI remains unverified because this checkout has no remote
   runner; local macOS version evidence does not substitute for hosted results.
2. Public PyPI/pipx and Homebrew tap installation remain unproven until publication.
3. Role-aware overlap, learning value, and guarded recommendations belong to Phase 3.
4. Persistent planning, reversible apply/undo, typed Codex integration, and release work
   remain disabled until their owning phases pass.
