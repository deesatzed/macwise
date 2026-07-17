# MW-200 Implementation Packet

## Task being attempted

Implement Phase 3 role-aware overlap intelligence: schema-4 catalog assessments,
required relationship categories, actual-use comparison, guarded learning/consolidation
guidance, `compare`, `review duplicates`, and Markdown output.

## User goal

Help a non-expert understand whether installed tools are duplicates, substitutes,
complements, runtimes/frontends, dependencies, or unrelated; show which appears active,
what is unique, and what may be worth learning without authorizing cleanup.

## Controlling design

- `GOAL.md`
- `docs/plans/2026-07-17-phase-3-overlap-intelligence-design.md`
- `docs/plans/2026-07-17-phase-3-overlap-intelligence.md`
- D-022 and D-023 in `DECISIONS.md`

## Expected files and risk

| Area | Files | Risk and boundary |
|---|---|---|
| Schema | `models/overlap.py`, audit/model exports, JSON migration | High: public schema 4; migrations mandatory. |
| Catalog | `catalog.py` | High: false identity/relationship claims; exact matches only. |
| Analysis | `services/overlap.py`, audit service | High: recommendation safety; no removal authorization. |
| UX | CLI/help/Markdown | Medium: ambiguity and basis must remain visible. |
| Tests/docs | focused fixtures, acceptance/truth files | Low: synthetic/public data only. |

## Existing patterns

- Immutable strict Pydantic public models and explicit in-memory migrations.
- Fixed deterministic services after raw evidence collection.
- Exact qualified CLI matching and explicit ambiguity refusal.
- Verified/inferred/user-confirmed/unknown basis and reliability.
- Shared terminal/Markdown sanitization; raw JSON provenance remains untrusted.
- One logical commit per green slice.

## Assumptions

- The approved `GOAL.md` is design approval under the autonomous standing rule.
- A bundled catalog is a versioned inference source, not a claim of exhaustive/current
  product coverage.
- Learning value is coarse catalog context, never a personalized productivity promise.
- Phase 3 may recommend keep, learn, keep-together, review-consolidation, or no action;
  removal and startup changes require later preflight/approval phases.
- No network, AI key, broad scan, persistence, or host mutation is needed.

## Non-goals

- Fuzzy duplicate detection, live research, AI reasoning, or generic similarity search.
- User decisions, cleanup plan, dependency/backup removal preflight, apply, or undo.
- Public release, hosted CI mutation, or Codex setup.

## Acceptance criteria

- Schema 4 round-trips Phase 3 models and migrates schema 1–3.
- Every required category exists and is fixture-tested; unknown pairs remain unknown.
- Required example families have exact catalog identities and explicit role fixtures.
- Actual-use comparisons reuse Phase 2 findings without inventing activity.
- Unique capabilities/data and keep-together constraints gate consolidation guidance.
- `compare`, `review duplicates`, `explain`, and Markdown are useful, sanitized,
  deterministic, read-only, and do not authorize removal.
- Full version/quality/build/privacy/skill/clean-wheel/real-read-only gates pass.

## Verification and rollback

Use red/green focused tests per plan task, then the full local gate. Every slice is a
separate Git commit; rollback is repository-only because Phase 3 adds no host mutation or
persistence.

## Proceed/block verdict

**PROCEED.** No credential, destructive, privacy, legal, or material product blocker is
present. Hosted CI/publication gaps are outside local MW-200 implementation.
