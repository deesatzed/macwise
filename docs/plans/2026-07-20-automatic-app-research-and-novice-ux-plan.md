# Automatic App Research and Novice UX Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the novice checkup start with three clear choices, automatically identify unresolved applications through privacy-bounded public sources, and keep public knowledge separate from cleanup authority.

**Architecture:** Add immutable public-identification models, a provider protocol, an expiring local claim cache, and a checkup-only enrichment service. The audit and safety-analysis layers remain local and deterministic: enriched descriptions are rendered with source/date/confidence but cannot create use, overlap, planning, apply, or undo conclusions. Replace the top-level eleven-option menu with a three-choice entry and route detailed topics through a second-level menu.

**Tech Stack:** Python 3.12+, Pydantic v2, standard-library HTTPS/JSON/cache I/O, Typer, Rich, platformdirs, pytest, Ruff, Pyright, uv.

---

### Task 1: Record the product-boundary decision and feature contract

**Files:**
- Modify: `DECISIONS.md`
- Modify: `GOAL_SIMPLE_UX.md`
- Modify: `TASK_QUEUE.md`
- Modify: `PROGRESS.md`
- Test: `tests/repository/test_public_foundation.py`

**Step 1: Write the failing repository-contract test**

Add assertions that public product truth describes:
- automatic checkup-only public identification;
- no inventory upload, account, telemetry, or background update;
- `--offline` as the privacy-preserving escape hatch;
- public facts as non-authoritative for cleanup.

**Step 2: Run it to verify it fails**

Run: `uv run pytest -q tests/repository/test_public_foundation.py`

Expected: FAIL because current truth files still say no live research is allowed.

**Step 3: Update the contract documents**

Add D-041 (or next available ID) that supersedes only the live-lookup prohibition in `GOAL_SIMPLE_UX.md`. Keep D-022's deterministic overlap rule and the evaluator's no-network boundary unchanged. Add a ready MW-606 task with the acceptance evidence from the approved design.

**Step 4: Run the focused test to verify it passes**

Run: `uv run pytest -q tests/repository/test_public_foundation.py`

Expected: PASS.

**Step 5: Commit**

```bash
git add DECISIONS.md GOAL_SIMPLE_UX.md TASK_QUEUE.md PROGRESS.md tests/repository/test_public_foundation.py
git commit -m "docs: define automatic app identification boundary"
```

### Task 2: Define strict public-identification data models

**Files:**
- Create: `src/macwise/models/knowledge.py`
- Modify: `src/macwise/models/__init__.py`
- Test: `tests/models/test_knowledge.py`

**Step 1: Write failing model tests**

Cover:
- `LookupIdentity` accepts only bundle ID, name, publisher, and optional version;
- `PublicPurposeClaim` requires a bounded purpose, HTTPS source URL, source type,
  retrieval time, expiry, confidence, exact/tentative match method, and limitation;
- invalid URLs, arbitrary extra fields, control text, overlong strings, future retrieval
  times, expired-at-creation claims, and unsafe source values are rejected;
- claims carry no path, usage, startup, plan, or inventory fields.

**Step 2: Run it to verify it fails**

Run: `uv run pytest -q tests/models/test_knowledge.py`

Expected: FAIL because `macwise.models.knowledge` does not exist.

**Step 3: Implement minimal immutable models**

Use frozen Pydantic models with strict field bounds and a small `ClaimConfidence` /
`MatchMethod` enum. Add a `PublicLookupResult` union-like model for resolved,
unresolved, unavailable, and conflict outcomes so failures are explicit.

**Step 4: Run the focused model tests**

Run: `uv run pytest -q tests/models/test_knowledge.py`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/macwise/models/knowledge.py src/macwise/models/__init__.py tests/models/test_knowledge.py
git commit -m "feat: define public app identification claims"
```

### Task 3: Add a privacy-enforcing lookup protocol and provider fakes

**Files:**
- Create: `src/macwise/knowledge/__init__.py`
- Create: `src/macwise/knowledge/providers.py`
- Test: `tests/knowledge/test_providers.py`

**Step 1: Write failing provider tests**

Create a recording fake provider. Assert that:
- one call receives exactly one `LookupIdentity`;
- a checkup can never pass an audit, path, usage, startup, dependency, backup, or plan;
- providers return typed outcomes rather than raw HTML;
- timeout, malformed source response, ambiguity, and provider failure become typed,
  nonfatal outcomes;
- a tentative name-only result cannot be promoted to exact.

**Step 2: Run it to verify it fails**

Run: `uv run pytest -q tests/knowledge/test_providers.py`

Expected: FAIL because the provider protocol is absent.

**Step 3: Implement the minimal protocol**

Define a narrow `PublicPurposeProvider` protocol:
```python
def lookup(self, identity: LookupIdentity) -> PublicLookupResult: ...
```
Keep the public client behind this protocol. Implement an in-memory fake only for
tests at this task; do not add network calls yet.

**Step 4: Run the focused tests**

Run: `uv run pytest -q tests/knowledge/test_providers.py`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/macwise/knowledge src/macwise/models tests/knowledge/test_providers.py
git commit -m "feat: add privacy-bounded lookup protocol"
```

### Task 4: Build an atomic, expiring local claim cache

**Files:**
- Create: `src/macwise/knowledge/cache.py`
- Test: `tests/knowledge/test_cache.py`

**Step 1: Write failing cache tests**

Use a temporary state root and assert:
- exact identity lookup finds a current cached claim;
- expired, mismatched, malformed, symlinked, or partial cache data is refused;
- write stages then atomically activates only fully valid data;
- bounded retention removes only cache entries, never scan/audit data;
- the cache stores claims, not an inventory or lookup history;
- cache read/write errors degrade to an explicit unavailable result.

**Step 2: Run it to verify it fails**

Run: `uv run pytest -q tests/knowledge/test_cache.py`

Expected: FAIL because the cache module is absent.

**Step 3: Implement the minimal cache**

Follow existing `src/macwise/persistence/locking.py` and state-root conventions.
Store one strict JSON record per stable identity under a dedicated bounded cache
directory; use atomic rename and descriptor-safe regular-file reads.

**Step 4: Run cache and hostile-file tests**

Run: `uv run pytest -q tests/knowledge/test_cache.py tests/persistence`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/macwise/knowledge/cache.py tests/knowledge/test_cache.py
git commit -m "feat: cache verified public app claims"
```

### Task 5: Implement one documented public-source adapter behind the protocol

**Files:**
- Create: `src/macwise/knowledge/http.py`
- Create: `src/macwise/knowledge/sources.py`
- Test: `tests/knowledge/test_http.py`
- Test: `tests/knowledge/test_sources.py`
- Modify: `DECISIONS.md`

**Step 1: Confirm the source contract before coding**

Research only official source documentation for the selected public API. Record its
terms, fields, identity matching capability, rate-limit behavior, and whether it
allows automated retrieval. Select a documented source that can support an exact
bundle-ID or publisher/product match. Do not ship HTML scraping, an unofficial
endpoint, an AI answer endpoint, or a provider requiring an undeclared account/API
key.

**Step 2: Write failing adapter tests with a local HTTP fixture**

Assert:
- requests use HTTPS, fixed user agent, strict connect/read timeout, small response
  cap, and controlled redirects;
- the URL/query contains only allowed `LookupIdentity` fields;
- an exact source match yields a cited claim;
- a same-name/different-publisher result, malformed payload, oversized response,
  redirect to non-HTTPS, non-200 response, and rate limit are refused or typed
  unavailable;
- tests never contact the public network.

**Step 3: Run it to verify it fails**

Run: `uv run pytest -q tests/knowledge/test_http.py tests/knowledge/test_sources.py`

Expected: FAIL because the HTTP client and source adapter do not exist.

**Step 4: Implement the smallest safe adapter**

Use a standard-library HTTPS client with injected transport for tests. Parse only
the source's structured fields into `PublicPurposeClaim`; store a source URL and
a concise purpose only after identity validation. If no compliant public source is
available, stop this task, record the evidence in `DECISIONS.md`, and leave the
provider unavailable rather than falling back to scraping.

**Step 5: Run the focused tests**

Run: `uv run pytest -q tests/knowledge/test_http.py tests/knowledge/test_sources.py`

Expected: PASS.

**Step 6: Commit**

```bash
git add src/macwise/knowledge/http.py src/macwise/knowledge/sources.py tests/knowledge/test_http.py tests/knowledge/test_sources.py DECISIONS.md
git commit -m "feat: add cited public app source adapter"
```

### Task 6: Enrich checkup only, without altering safety analysis

**Files:**
- Create: `src/macwise/services/identification.py`
- Modify: `src/macwise/services/__init__.py`
- Modify: `src/macwise/services/checkup.py`
- Modify: `src/macwise/models/checkup.py`
- Test: `tests/services/test_identification.py`
- Test: `tests/services/test_checkup_service.py`
- Test: `tests/services/test_planning.py`
- Test: `tests/services/test_overlap.py`

**Step 1: Write failing service and safety-regression tests**

Build a synthetic audit with cataloged, cached, exact-public, tentative-public, and
unavailable applications. Assert:
- only unresolved applications are requested;
- cache precedes network;
- default checkup uses identification while `offline=True` does not;
- a current exact public claim improves the identification count and supplies a
  cited description;
- tentative/unavailable claims remain "Needs identification";
- overlap, usage, plan, apply, and undo inputs are byte-for-byte unchanged by
  public claims.

**Step 2: Run it to verify it fails**

Run: `uv run pytest -q tests/services/test_identification.py tests/services/test_checkup_service.py`

Expected: FAIL because no enrichment service exists.

**Step 3: Implement the orchestration service**

Derive lookup identities from `SoftwareRecord` without passing the audit onward.
Use catalog → cache → provider precedence. Return a separate immutable
identification summary consumed by checkup rendering; do not mutate observed
software records or catalog assessments.

**Step 4: Run focused safety suites**

Run: `uv run pytest -q tests/services/test_identification.py tests/services/test_checkup_service.py tests/services/test_planning.py tests/services/test_overlap.py`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/macwise/services src/macwise/models/checkup.py tests/services
git commit -m "feat: enrich checkup app identification safely"
```

### Task 7: Replace the top-level menu and simplify checkup rendering

**Files:**
- Modify: `src/macwise/cli.py`
- Modify: `src/macwise/reporting/checkup.py`
- Modify: `src/macwise/help_text.py`
- Test: `tests/cli/test_guided_menu.py`
- Test: `tests/cli/test_checkup_command.py`
- Test: `tests/reporting/test_checkup.py`

**Step 1: Write failing UI tests**

Assert:
- top-level interactive menu has exactly choices 1–3;
- choice 1 runs the fresh checkup; choice 2 opens a short topic menu; choice 3
  prints help;
- non-TTY invocation does not prompt and points to `macwise checkup`;
- checkup starts with "Your Mac at a glance" and a single "Start here" result;
- at most three priority cards are visible by default;
- unresolved items render "Needs identification," never raw "unknown purpose";
- the network disclosure appears before first provider activity;
- `--offline` is clear and the completion says nothing changed;
- terminal line length remains at most 100 characters.

**Step 2: Run it to verify it fails**

Run: `uv run pytest -q tests/cli/test_guided_menu.py tests/cli/test_checkup_command.py tests/reporting/test_checkup.py`

Expected: FAIL because the menu still accepts 1–11 and rendering uses old headings.

**Step 3: Implement the smallest presentation change**

Keep direct commands stable. Add a `more options` guided handler and a checkup
`--offline` flag. Render the fixed six-section hierarchy from the design. Preserve
the existing session-only user context and explicit plan-preview handoff, but never
offer public identity text as an implicit cleanup candidate.

**Step 4: Run focused CLI and rendering tests**

Run: `uv run pytest -q tests/cli/test_guided_menu.py tests/cli/test_checkup_command.py tests/reporting/test_checkup.py`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/macwise/cli.py src/macwise/reporting/checkup.py src/macwise/help_text.py tests/cli tests/reporting
git commit -m "feat: simplify novice checkup journey"
```

### Task 8: Make detailed reviews bounded and speak in plain language

**Files:**
- Modify: `src/macwise/cli.py`
- Modify: `src/macwise/help_text.py`
- Test: `tests/cli/test_review_commands.py`
- Test: `tests/cli/test_explain_command.py`

**Step 1: Write failing output tests**

Assert that:
- review commands show a one-sentence interpretation before records;
- default output shows a bounded number plus an exact `--all` command;
- unknown/research language uses "Needs identification" with an explanation;
- `explain` separates Verified local facts from Public app information with source,
  date, confidence, and limitation;
- no list calls an item removable merely because it lacks a public result.

**Step 2: Run it to verify it fails**

Run: `uv run pytest -q tests/cli/test_review_commands.py tests/cli/test_explain_command.py`

Expected: FAIL because existing labels and layout predate public identification.

**Step 3: Implement minimal renderer wording changes**

Reuse the existing bounded list helpers. Do not rewrite inventory data or remove
expert detail. Add the public claim section only when present and keep unresolved
items actionable through `macwise explain NAME` or a clearly named offline
recovery path.

**Step 4: Run focused CLI tests**

Run: `uv run pytest -q tests/cli/test_review_commands.py tests/cli/test_explain_command.py`

Expected: PASS.

**Step 5: Commit**

```bash
git add src/macwise/cli.py src/macwise/help_text.py tests/cli
git commit -m "feat: clarify detailed app review output"
```

### Task 9: Document privacy, source limits, and user workflow

**Files:**
- Modify: `README.md`
- Modify: `docs/getting-started.md`
- Modify: `docs/privacy.md`
- Modify: `docs/index.html`
- Modify: `CHANGELOG.md`
- Test: `tests/repository/test_public_foundation.py`
- Test: `tests/repository/test_docs_links.py`

**Step 1: Write failing documentation-contract tests**

Assert the public docs:
- show `macwise` / `macwise checkup` as the first path;
- explain automatic one-app-at-a-time identification and `--offline`;
- distinguish local facts from cited public information;
- say no inventory, paths, usage, or cleanup plan is uploaded;
- say sources can be unavailable or wrong and never authorize cleanup;
- use the three-choice menu and bounded result shape.

**Step 2: Run it to verify it fails**

Run: `uv run pytest -q tests/repository/test_public_foundation.py tests/repository/test_docs_links.py`

Expected: FAIL because current docs promise a network-free normal checkup and show
the older menu.

**Step 3: Update public documentation**

Use a sanitized walkthrough containing one identified app, one unavailable lookup,
one citation, and one `--offline` run. Do not include real inventory, user paths,
or source credentials. Update the landing page only with claims the tests prove.

**Step 4: Run documentation tests**

Run: `uv run pytest -q tests/repository/test_public_foundation.py tests/repository/test_docs_links.py`

Expected: PASS.

**Step 5: Commit**

```bash
git add README.md docs/getting-started.md docs/privacy.md docs/index.html CHANGELOG.md tests/repository
git commit -m "docs: explain automatic app identification"
```

### Task 10: Run the complete safety, package, and clean-clone proof

**Files:**
- Modify: `PROGRESS.md`
- Modify: `TASK_QUEUE.md`
- Create: `docs/automatic-identification-acceptance.md`

**Step 1: Run the full local gate**

Run:

```bash
uv run pytest -q
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv build
git diff --check
```

Expected: all commands exit 0.

**Step 2: Run focused privacy and mutation-adjacent regressions**

Run:

```bash
uv run pytest -q tests/knowledge tests/services/test_planning.py tests/services/test_overlap.py tests/execution tests/cli
```

Expected: PASS with no real network request, Homebrew change, startup change,
application removal, or cache of a private inventory.

**Step 3: Prove an isolated clean-clone installation**

Clone the feature commit into a temporary directory, run `uv sync --locked`,
install the wheel into an isolated `UV_TOOL_DIR` and `UV_TOOL_BIN_DIR`, then
execute:
```bash
macwise --help
macwise checkup --help
macwise checkup --offline
```
Use a fake/local provider fixture for the automated cited-lookup proof. A real
public-source smoke is optional and must be recorded only as aggregate success/
failure and source name, never as a local inventory.

**Step 4: Record only evidence-backed results**

Write the exact commands, versions, pass counts, rendered transcript assertions,
and any source availability limitation to `docs/automatic-identification-acceptance.md`.
Update task status only after all gates pass.

**Step 5: Commit**

```bash
git add PROGRESS.md TASK_QUEUE.md docs/automatic-identification-acceptance.md
git commit -m "test: prove automatic identification safety"
```

