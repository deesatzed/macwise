# Phase 3 Overlap Intelligence Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use @executing-plans to implement this plan task-by-task.

**Goal:** Deliver deterministic role-aware comparisons, all required overlap categories,
actual-use comparison, and guarded learning/consolidation guidance without authorizing a
cleanup action.

**Architecture:** Schema 4 stores exact catalog assessments, pairwise overlap relations,
and guarded recommendations beside unchanged inventory and Phase 2 findings. A versioned
offline catalog supplies exact identities and explicit relationships; a deterministic
service joins these to Phase 2 usage labels, and CLI/Markdown render evidence and
unknowns without fuzzy guessing.

**Tech Stack:** Python 3.12+, Pydantic v2, Typer, immutable dataclasses, pytest, Ruff,
Pyright, uv.

---

### Task 1: Schema 4 overlap models and migration

**Files:**
- Create: `src/macwise/models/overlap.py`
- Modify: `src/macwise/models/__init__.py`
- Modify: `src/macwise/models/audit.py`
- Modify: `src/macwise/reporting/json_report.py`
- Test: `tests/models/test_overlap.py`
- Modify: `tests/models/test_audit.py`
- Modify: `tests/reporting/test_reports.py`

**Step 1: Write failing model tests**

Test exact enum values for all nine `OverlapCategory` members, `LearningValue`, and
`RecommendationAction`. Test frozen/extra-forbid behavior and invariants:

```python
relation = OverlapRelation(
    id="overlap:docker-podman",
    left_subject_id="application:docker",
    right_subject_id="application:podman",
    category=OverlapCategory.STRONG_SUBSTITUTE,
    statement="Both provide a local container workflow.",
    shared_capabilities=("containers",),
    basis=ClaimBasis.INFERRED,
    confidence=Reliability.MEDIUM,
)
assert relation.left_subject_id != relation.right_subject_id
```

Require catalog assessments to carry a catalog version/source and recommendations to
carry at least one subject, a statement, basis, confidence, prerequisites, and
limitations. Reject a recommendation action of `remove` because no such enum member
exists.

**Step 2: Run the red test**

Run: `uv run pytest -q tests/models/test_overlap.py`

Expected: collection fails because the overlap models do not exist.

**Step 3: Implement strict immutable models**

Add:

```python
class OverlapCategory(StrEnum):
    EXACT_DUPLICATE = "exact_duplicate"
    SAME_PRODUCT_INSTALLED_TWICE = "same_product_installed_twice"
    STRONG_SUBSTITUTE = "strong_substitute"
    PARTIAL_OVERLAP = "partial_overlap"
    COMPLEMENTARY_TOOLS = "complementary_tools"
    RUNTIME_AND_FRONTEND = "runtime_and_frontend"
    DEPENDENCY_AND_USER_FACING_APP = "dependency_and_user_facing_app"
    LEGACY_AND_SUCCESSOR = "legacy_and_successor"
    NOT_ACTUALLY_RELATED = "not_actually_related"
```

Add `CatalogAssessment`, `OverlapRelation`, and `GuardedRecommendation`, plus stable
hash-based IDs that canonicalize relation subject order without embedding local values.

**Step 4: Add schema migration tests and implementation**

Set `AuditDocument.schema_version` to literal 4 and add `catalog_assessments`, `overlaps`,
and `recommendations`. Migrate JSON versions 1, 2, and 3 to 4 in memory; accept 4 and
reject 5. Update prior schema assertions without weakening strict validation.

**Step 5: Verify and commit**

Run:

```bash
uv run pytest -q tests/models tests/reporting/test_reports.py
uv run ruff check src/macwise/models tests/models tests/reporting/test_reports.py
uv run pyright src/macwise/models src/macwise/reporting/json_report.py
```

Commit: `feat: add Phase 3 overlap models`

### Task 2: Versioned exact-match catalog

**Files:**
- Create: `src/macwise/catalog.py`
- Create: `tests/test_catalog.py`

**Step 1: Write the catalog contract tests**

Require:

- unique catalog keys and qualified exact match keys;
- no duplicate explicit pair definitions after canonical ordering;
- valid pair endpoints and no self-pairs;
- all nine category values are supported across explicit and identity-derived rules;
- entries for every required product family in `GOAL.md`;
- no usernames, private paths, institutions, shell fragments, or network calls;
- immutable catalog values and a non-empty version string.

Test exact matching and ambiguity:

```python
record = SoftwareRecord(
    id="application:docker",
    entity_type=EntityType.APPLICATION,
    name="Docker",
    display_name="Docker Desktop",
    identifier="com.docker.docker",
)
assert match_catalog_entry(record).key == "docker-desktop"
assert match_catalog_entry(hostile_or_partial_name) is None
```

**Step 2: Observe red**

Run: `uv run pytest -q tests/test_catalog.py`

Expected: import failure for `macwise.catalog`.

**Step 3: Implement the minimal catalog**

Use frozen dataclasses for `CatalogEntry`, `CatalogMatcher`, and `CatalogRelation`.
Match only entity-qualified casefolded exact names, identifiers, or executables. Include
coarse roles/capabilities/unique notes and learning context for the required Docker,
local-AI, Markdown, launcher/automation, and Python families. Encode only relationships
needed by the approved examples and all non-identity categories.

**Step 4: Verify and commit**

Run:

```bash
uv run pytest -q tests/test_catalog.py
uv run ruff check src/macwise/catalog.py tests/test_catalog.py
uv run pyright src/macwise/catalog.py
```

Commit: `feat: add exact role catalog`

### Task 3: Deterministic overlap and recommendation analysis

**Files:**
- Create: `src/macwise/services/overlap.py`
- Create: `tests/services/test_overlap_analysis.py`
- Modify: `src/macwise/services/__init__.py`

**Step 1: Write failing relationship tests**

Fixture-test:

- explicit strong substitute, partial overlap, complementary, runtime/frontend,
  dependency/app, legacy/successor, and not-related relations;
- exact duplicate only with the same reliable `content_digest` evidence;
- same-product-twice from a shared unambiguous catalog identity and distinct install
  paths without a shared digest;
- no relation for fuzzy/ambiguous/unknown pairs;
- canonical stable relation IDs and unique capabilities on the correct side.

**Step 2: Write failing usage/recommendation tests**

Join one Phase 2 usage finding per subject. Test fixed rules:

- active/recent/probable and indirectly-required members are retained as keep evidence;
- complementary/runtime/dependency pairs yield `keep_together`;
- possibly/user-confirmed unused plus an active strong substitute may yield
  `review_consolidation`, never remove;
- high/moderate catalog learning value may yield `learn` with a bounded rationale;
- ties, missing findings, unique capabilities, or unknown relationships prevent an
  unsafe consolidation recommendation;
- all statements exclude “never used” and “safe to remove.”

**Step 3: Observe red**

Run: `uv run pytest -q tests/services/test_overlap_analysis.py`

Expected: import failure for the overlap service.

**Step 4: Implement minimal analysis**

Return an immutable `OverlapAnalysis` dataclass containing assessments, relations,
recommendations, and limitations. Build exact catalog matches once, derive identity
relations, apply the explicit pair matrix, join usage labels, and apply recommendation
precedence. Keep unmatched records intact and absent from catalog conclusions.

**Step 5: Verify and commit**

Run:

```bash
uv run pytest -q tests/services/test_overlap_analysis.py tests/services/test_usage_analysis.py
uv run ruff check src/macwise/services tests/services
uv run pyright src/macwise/services
```

Commit: `feat: analyze role-aware overlaps`

### Task 4: Audit orchestration and partial degradation

**Files:**
- Modify: `src/macwise/services/audit.py`
- Modify: `tests/services/test_audit_service.py`

**Step 1: Write a failing service test**

Inject an `overlap_analyzer`, assert it runs after Phase 2 analysis, receives enriched
software and usage findings, and populates schema-4 assessments/relations/
recommendations. Add a failing analyzer test that preserves the Phase 1–2 audit and
records an unavailable `overlap` status with a public limitation.

**Step 2: Observe red**

Run: `uv run pytest -q tests/services/test_audit_service.py`

Expected: `AuditService` rejects `overlap_analyzer` or schema-4 fields remain empty.

**Step 3: Implement and verify**

Add a typed analyzer protocol/default, run it after `analyze_usage`, sort all public
outputs deterministically, include `overlap` in collector statuses, and degrade
unexpected exceptions without exposing exception text.

Run: `uv run pytest -q tests/services/test_audit_service.py`

Commit: `feat: assemble overlap intelligence`

### Task 5: Compare and overlap-review CLI

**Files:**
- Modify: `src/macwise/cli.py`
- Modify: `src/macwise/help_text.py`
- Modify: `tests/cli/test_phase_three_views.py`
- Modify: `tests/cli/test_help_contract.py`

**Step 1: Write failing CLI acceptance tests**

Cover:

- compare requires at least two names and refuses missing/ambiguous records;
- qualifiers reuse the exact matcher;
- every related pair prints category, shared/unique capabilities, both usage labels and
  basis/confidence, learning value, and guarded guidance;
- unknown pair prints “relationship unknown”;
- `review duplicates` is headed “Overlap candidates — not all are duplicates,” groups
  categories, excludes not-related pairs, and never says all entries are duplicates;
- no output contains removal authorization or host mutation language.

**Step 2: Observe red**

Run: `uv run pytest -q tests/cli/test_phase_three_views.py`

Expected: current Phase 3 refusal strings fail the output assertions.

**Step 3: Implement deterministic rendering**

Resolve all requested records from one audit, canonicalize selected IDs, render matching
relations and recommendations, and explicitly render unknown pairs. Extend `explain`
with catalog roles, unique capabilities, learning value, and related overlap members.
Update help from refusal language to current read-only behavior.

**Step 4: Verify and commit**

Run:

```bash
uv run pytest -q tests/cli tests/security
uv run ruff check src/macwise/cli.py src/macwise/help_text.py tests/cli
```

Commit: `feat: deliver role-aware compare views`

### Task 6: Schema-4 Markdown and hostile rendering

**Files:**
- Modify: `src/macwise/reporting/markdown.py`
- Modify: `tests/reporting/test_reports.py`
- Modify: `tests/security/test_hostile_metadata.py`

**Step 1: Write failing report tests**

Require catalog assessment, role-aware relations, actual-use labels, learning value,
recommendations, prerequisites/limitations, and unknown relationships in distinct
sections. Update the hostile exact-heading allowlist and prove injected catalog strings
cannot forge headings, bullets, ANSI, or bidi structure while raw JSON round-trips.

**Step 2: Observe red**

Run: `uv run pytest -q tests/reporting tests/security`

Expected: missing Phase 3 sections and old heading allowlist.

**Step 3: Implement, verify, and commit**

Render all Phase 3 values through `_markdown_text`, retain basis/confidence, and end with
the no-removal-authorization boundary.

Run:

```bash
uv run pytest -q tests/reporting tests/security
uv run ruff check src/macwise/reporting tests/reporting tests/security
uv run pyright src/macwise/reporting
```

Commit: `feat: report Phase 3 overlap evidence`

### Task 7: Phase 3 acceptance

**Files:**
- Create: `docs/phase-3-acceptance.md`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `PROGRESS.md`
- Modify: `TASK_QUEUE.md`
- Modify: `DECISIONS.md` only if implementation evidence changes a decision

**Step 1: Run fresh gates using @verification-before-completion**

Run:

```bash
uv run --python 3.12 pytest -q
uv run --python 3.13 pytest -q
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv build
python3 /path/to/skill-creator/scripts/quick_validate.py skills/macwise
python3 -c "import pathlib, yaml; assert isinstance(yaml.safe_load(pathlib.Path('.github/workflows/ci.yml').read_text()), dict)"
uv run pytest -q tests/repository/test_public_foundation.py
git diff --check
```

Repeat a clean wheel help/render smoke and one aggregate-only real read-only audit. Do
not save or print names/paths.

**Step 2: Validate the completion claim**

Use @claim-validation. Check acceptance criteria, tests, TODO/FIXME/HACK/
NotImplemented markers, skipped tests, dirty state, real partial limitations, and every
open external gate. Verdict MW-200 independently from overall-product readiness.

**Step 3: Update truth and commit**

Only mark MW-200 done if the direct evidence passes. Keep hosted CI/public publication,
planning, mutation, Codex integration, and release explicitly open.

Commit: `docs: accept local Phase 3 intelligence`
