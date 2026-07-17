# Phase 3 Overlap Intelligence Design

## Status and authority

This design implements the user-approved Phase 3 contract in `GOAL.md`: `macwise
compare`, `macwise review duplicates`, all required overlap categories, actual-use
comparison, and learning-value recommendations. The autonomous standing rule permits
safe assumptions to be documented and continued; no missing choice changes that scope.

## Goal

Explain how installed tools relate without calling every related product a duplicate.
MacWise must show what overlaps, what remains unique, which item appears active or
indirectly required, what should not be removed together, and whether learning an
installed tool may have value. It remains read-only and cannot authorize removal.

## Approaches considered

### 1. Versioned exact-match role catalog — selected

Bundle a small deterministic catalog whose entries use exact bundle identifiers,
Homebrew names, and executable aliases. Catalog entries define coarse roles,
capabilities, unique-value notes, and learning-value context. An explicit pair matrix
assigns a required overlap category only where the relationship is known.

Advantages: reproducible, fixture-testable, offline, provenance-friendly, and safe for
hostile names. Unknown software and unknown pairs stay unknown. The required example
families can be represented without claiming that arbitrary similarly named tools are
duplicates.

Cost: the catalog is intentionally incomplete and must be versioned and maintained.

### 2. Heuristic name/description/capability inference — rejected for conclusions

Token similarity and description/executable rules could cover more software, but names
such as “Docker,” “Markdown,” or “Python” do not establish product identity or role.
Heuristics may be useful later to nominate research candidates, but they cannot assign a
user-facing category or recommendation in Phase 3.

### 3. Live web/AI classification — deferred

Selective official research can improve unknown product descriptions, and AI can help
explain structured evidence. However, network freshness, caching, citations, prompt
isolation, model configuration, and typed local integration expand the phase. Dynamic
classification will not be a prerequisite for deterministic Phase 3 behavior.

## Architecture

### Catalog layer

`catalog.py` contains immutable, versioned definitions:

- exact match keys by entity type, identifier, package name, and executable;
- product family and user-facing role labels;
- coarse capabilities and potentially unique functions/data;
- learning value (`high`, `moderate`, `low`, `unknown`) with a bounded rationale;
- explicit pair relations for the nine required categories.

Discovered strings are lookup data only. No fuzzy match, shell execution, network call,
or dynamic import is allowed. Ambiguous exact matches produce no catalog assessment.

### Schema 4 analysis layer

Schema 4 adds three normalized surfaces beside unchanged raw inventory and Phase 2
findings:

1. `CatalogAssessment`: the exact catalog entry matched to one software record, its
   roles/capabilities/unique notes, learning value, basis, confidence, catalog version,
   and limitations.
2. `OverlapRelation`: two software IDs, one required `OverlapCategory`, shared and
   side-specific capabilities, explanation, basis, confidence, and limitations.
3. `GuardedRecommendation`: one or more subject IDs, action, learning value, statement,
   basis, confidence, prerequisites, and limitations.

The category enum contains exactly:

- exact duplicate;
- same product installed twice;
- strong substitute;
- partial overlap;
- complementary tools;
- runtime and frontend;
- dependency and user-facing app;
- legacy and successor;
- not actually related.

Schema 1–3 documents migrate in memory with empty Phase 3 collections. Schema 5 and
later are rejected until supported.

### Deterministic analysis

The overlap service receives software and Phase 2 usage findings.

1. Match each software record to at most one catalog entry using qualified exact keys.
2. Produce assessments only for unambiguous matches.
3. Create relations only from an explicit catalog pair or strong identity evidence;
   otherwise return no relation rather than guessing.
4. Join each member to its existing usage label. A comparison can state that one member
   has stronger observed evidence, but a tie or unknown stays unresolved.
5. Generate guarded recommendations by fixed precedence:
   - indirectly required or active items are `keep` candidates;
   - a high/moderate learning value can yield `learn` only when its catalog rationale is
     explicit;
   - possibly/user-confirmed unused items with an active strong substitute can yield
     `review_consolidation`;
   - complements, runtime/frontends, dependencies, and unresolved evidence yield
     `no_recommendation` or `keep_together`, never removal.

No Phase 3 rule emits an uninstall command, declares removal safe, or treats missing
evidence as non-use. Recommendation text must name unique capabilities/data and the
remaining preflight requirements.

## Data flow

```text
Phase 1 inventory + Phase 2 usage findings
                  |
                  v
        exact catalog assessment
                  |
                  v
       explicit pair relationship graph
                  |
                  v
 actual-use comparison + guarded recommendation
                  |
          +-------+--------+
          |                |
       schema 4      CLI / Markdown views
```

Audit orchestration runs overlap analysis after usage/startup/path/backup analysis. A
catalog-analysis exception degrades to empty Phase 3 results and an explicit collector
status/limitation without discarding the Phase 1–2 audit.

## User experience

### `macwise compare NAME [NAME ...]`

- requires at least two unambiguous installed records;
- supports the existing `app:`, `cask:`, and `formula:` qualifiers;
- shows identity/role, pair category, shared capabilities, unique capabilities, usage
  label/basis/confidence, learning value, and guarded recommendation;
- states “relationship unknown” for a pair with no explicit relation;
- ends with the read-only/no-removal-authorization boundary.

### `macwise review duplicates`

The heading is “Overlap candidates — not all are duplicates.” Results are grouped by
category. Exact/same-product candidates are visually distinct from strong substitutes,
partial overlap, complements, runtime/frontend, dependency/app, and successor pairs.
`not_actually_related` pairs are shown only in an explicit comparison, not as cleanup
candidates.

### Explain and reports

`macwise explain` adds catalog roles, unique capabilities, learning value, related
overlap members, and any guarded recommendation. Markdown adds catalog, overlap, and
recommendation sections while preserving verified/inferred/user/unknown distinctions.
JSON remains the canonical lossless representation.

## Required catalog coverage

Sanitized fixtures exercise all nine categories and these product families:

- Docker Desktop / Docker CLI / Compose / Podman;
- Ollama / LM Studio / oMLX / llama.cpp / MLX;
- Obsidian / Zettlr / Mark Text / Markdown Preview / QLMarkdown;
- Raycast / Spotlight / Hammerspoon / AltTab / Magnet;
- Homebrew Python / pyenv / Anaconda / virtual-environment tooling.

Coverage means deterministic role/relationship fixtures, not a promise that every
version or local model file is discovered. Local model data remains path evidence when
an allowlisted collector can identify it.

## Error handling and safety

- Unknown catalog entry: retain the software record and render catalog/relationship
  unknown.
- Multiple catalog matches: emit an explicit ambiguity limitation; no relation.
- Missing Phase 2 usage finding: actual-use comparison unknown.
- Catalog inconsistency: fail validation in tests/startup and degrade the analysis slice
  rather than inventing a result.
- Hostile catalog-like metadata: exact inert comparisons only; every human value passes
  the existing display sanitizer.
- No network, broad home scan, shell, mutation, persistence, or removal command is added.

## Testing

- Schema tests cover all enums/models, invariants, stable IDs, schema-1/2/3 migration,
  round-trip, and future rejection.
- Catalog contract tests require unique exact keys, valid relation endpoints, symmetric
  normalization, all nine categories, all required example families, and no private
  paths/names.
- Analysis table tests cover explicit relationships, unknown/ambiguous pairs, usage
  precedence, unique capability retention, learning-value logic, and every guarded
  recommendation boundary.
- CLI/report tests cover qualification, actual-use comparison, grouping, unknowns,
  read-only wording, and hostile structure injection.
- Full Python 3.12/3.13, quality, build, privacy, skill, clean-install, and real read-only
  gates repeat before MW-200 is accepted.

## Non-goals

- No arbitrary fuzzy duplicate detector.
- No live web research, AI dependency, or personalized productivity claim.
- No user-decision persistence, cleanup plan, backup preflight, removal command, or
  startup disable.
- No claim that catalog coverage is complete or current beyond its versioned contents.
