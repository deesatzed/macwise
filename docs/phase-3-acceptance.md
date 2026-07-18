# Phase 3 Acceptance Audit

Date: 2026-07-17

Verdict: **PASS for MW-200 local read-only scope**. Phase 3 now provides a
versioned exact-match role catalog, all required relationship categories,
evidence-aware comparisons, learning-value guidance, guarded recommendations,
schema-4 reports, and safe ambiguity propagation. This is not an overall-product
or production-readiness verdict: hosted CI/public installation remains open under
MW-011/MW-600, and planning, mutation, Codex integration, and release remain owned
by Phases 4–7.

## Acceptance evidence

| Requirement | Verdict | Direct evidence | Honest limitation |
|---|---|---|---|
| Schema 4 and older audit compatibility | PASS | Model/report tests round-trip catalog assessments, overlap relations, and guarded recommendations; schema 1–3 migrate in memory and future schema 5 rejects. | Every future schema change still requires an explicit migration. |
| Versioned exact-match role catalog | PASS | Catalog tests cover required tool families, unique keys, valid relations, entity qualification, identifier/name/executable priority, exact-only matching, and immutable public data. | The bundled catalog is intentionally small and general; unknown software remains unknown. |
| Ambiguity remains visible | PASS | A typed catalog-match outcome preserves tied catalog keys, the analyzer emits one sanitized limitation, and the audit collector becomes partial. | MacWise does not guess between equally ranked catalog roles. |
| Required overlap categories | PASS | Analyzer fixtures exercise exact duplicate, same product twice, strong substitute, partial overlap, complementary tools, runtime/frontend, dependency/user-facing app, legacy/successor, and not-actually-related. | Catalog relationships describe general roles, not local project interchangeability. |
| Actual-use comparison | PASS | CLI tests name the uniquely stronger observed-use signal independent of argument order and report ties, missing evidence, and dependency-only evidence as unresolved. | Point-in-time evidence is not complete usage history. |
| Learning-value guidance | PASS | Tests preserve per-item `learn` guidance for high/moderate-value unknown or cautious-use items, including members of a neutral pair. | Learning value is general catalog context, not a personalized outcome guarantee. |
| Guarded recommendations | PASS | Tests cover keep, learn, keep-together, review-consolidation, and no-recommendation; model enums contain no removal action and outputs prohibit removal authorization. | Dependency, backup, ambiguity, protection, data, rollback, and approval preflight remain Phase 4–5 work. |
| Phase 3 CLI and Markdown views | PASS | Tests cover `compare`, `review duplicates`, enriched `explain`, help, JSON, and exact ten-heading Markdown output with hostile-text neutralization. | “Duplicate candidates” intentionally includes role-aware overlap groups and labels their exact relationship. |

## Independent review disposition

| Recommendation | Classification | Resolution |
|---|---|---|
| Preserve ambiguous catalog matches and degrade collector state | Accepted / Resolved | Added typed match metadata, sanitized analyzer limitation, partial-state integration, and regressions. |
| State which item has stronger observed-use evidence, or state unresolved | Accepted / Resolved | Added deterministic comparison ranking with reverse-order, tie, missing, and dependency-only handling. |
| Do not suppress compatible learning guidance behind neutral pair guidance | Accepted / Resolved | Neutral `no recommendation` pairs no longer mark their subjects covered; high/moderate learning regressions pass. |

No critical findings remained. The reviewer also confirmed that distinct application
install paths now retain distinct stable IDs.

## Fresh verification

- Python 3.12.11: 142 tests passed.
- Python 3.13.13: 142 tests passed.
- Ruff lint and format checks passed; Pyright reported 0 errors.
- `uv build` produced the `macwise-0.1.0a0` wheel and source distribution.
- The repository privacy contract reported 5 passing tests.
- The bundled read-only skill validated with an ephemeral validator-only PyYAML
  dependency; the pinned workflow parsed as YAML.
- A fresh Python 3.12 environment installed the wheel and passed version,
  schema-4 import/construction, `compare --help`, and
  `review duplicates --help` smokes.
- Scoped TODO/FIXME/HACK/XXX/NotImplemented and skipped/xfail scans returned no
  implementation or test matches.
- `git diff --check` passed before the implementation commit.

## Real read-only evidence

One aggregate-only in-memory audit returned schema 4 with 325 software records and
325 unique IDs, 25 catalog assessments, 6 overlap relations, and 21 guarded
recommendations. The relations covered five category kinds and the recommendations
covered four action kinds. JSON round-trip and the exact ten-heading Markdown allowlist
passed in 19.18 seconds. No inventory names or paths were printed or saved.

All seven collectors reported state: three complete and four partial. Partial overlap or
source collection evidence remains qualified instead of being discarded, guessed, or
promoted to a negative conclusion.

## Claim validation

| Completion requirement | Result | Evidence |
|---|---|---|
| Acceptance criteria defined and met | PASS | `IMPLEMENTATION_PACKET.md`, the Phase 3 design/plan, and the table above. |
| Tests exist and pass | PASS | Focused catalog/model/analyzer/service/CLI/report/security tests plus both 142-test version runs. |
| No blocking scoped stubs | PASS | Scoped marker and skipped-test scans returned no implementation/test matches. |
| Independent review performed and adjudicated | PASS | Three important findings were Accepted, resolved test-first, and reverified; no critical finding remained. |
| Dirty-state truth preserved | PASS | Phase 3 implementation commits are recorded; this acceptance document and truth updates are the only pending scope at audit time. |

**Claim verdict: PASS** for “MW-200 Phase 3 local read-only scope is complete.”

## Still open

1. MW-011 hosted Linux/macOS CI remains unverified because this checkout has no remote
   runner; local macOS version evidence does not substitute for hosted results.
2. Public UV-tool/pipx installation remains unproven until PyPI publication; Homebrew distribution is deferred by D-035.
3. Persistent exact cleanup planning and previews belong to Phase 4.
4. Reversible apply/verify/undo, typed Codex integration, and release work remain
   disabled until their owning phases pass.
