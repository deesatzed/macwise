# Shared Knowledge Database Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a privacy-preserving, signed, revisioned shared knowledge database that MacWise can explicitly update from a public Hugging Face dataset and use offline alongside local evidence.

**Architecture:** Introduce strict immutable knowledge models, a signed snapshot verifier, an atomic local snapshot store, and an injected downloader with a Hugging Face production adapter. Existing bundled catalog records become the always-available fallback; verified shared records augment them without overriding observed host facts or authorizing cleanup.

**Tech Stack:** Python 3.12+, Pydantic v2, `cryptography` Ed25519, `huggingface_hub`, Typer, platformdirs, pytest, Ruff, Pyright, uv.

---

### Task 1: Define strict shared-knowledge schema and sanitized fixtures

**Files:**
- Create: `src/macwise/knowledge/models.py`
- Create: `src/macwise/knowledge/__init__.py`
- Create: `tests/knowledge/test_models.py`
- Create: `tests/fixtures/knowledge/valid/manifest.json`
- Create: `tests/fixtures/knowledge/valid/products.jsonl`
- Create: `tests/fixtures/knowledge/valid/relationships.jsonl`
- Create: `tests/fixtures/knowledge/valid/issues.jsonl`
- Create: `tests/fixtures/knowledge/valid/advisories.jsonl`
- Create: `tests/fixtures/knowledge/valid/sources.jsonl`

1. Write failing tests for frozen strict models: manifest, product, matcher, relationship, issue/advisory, source, source reference, applicability, and complete snapshot.
2. Assert rejection of unknown fields, duplicate IDs, invalid URLs, unsafe matcher values, unsupported schemas, future timestamps, missing references, invalid confidence/basis combinations, oversized fields, prompt/control text, and version/platform ranges that cannot be parsed.
3. Run `uv run pytest -q tests/knowledge/test_models.py` and observe import/behavior failures.
4. Implement the smallest Pydantic models and pure `load_snapshot(directory)` validator that parse bounded JSONL line-by-line and validate cross-file references.
5. Rerun the focused suite until green, then run model/security suites.
6. Commit as `feat: define shared knowledge schema`.

### Task 2: Verify signed manifests and file integrity

**Files:**
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Create: `src/macwise/knowledge/integrity.py`
- Create: `tests/knowledge/test_integrity.py`
- Create: `tests/fixtures/knowledge/keys/test-public.key`
- Create: `tests/fixtures/knowledge/valid/signatures/manifest.ed25519`

1. Add direct bounded `cryptography` dependency and refresh the lockfile.
2. Write failing tests that verify canonical manifest bytes with an embedded Ed25519 public key and reject wrong keys, changed bytes, malformed signatures, unknown key IDs, digest mismatches, count mismatches, symlinks, special files, missing files, extra authority-bearing files, and oversized snapshots.
3. Observe the focused RED result.
4. Implement canonical-byte verification, fixed filename allowlists, descriptor-safe regular-file reads, SHA-256 verification, and bounded counts/sizes.
5. Prove that failure returns a typed error and never yields a partially trusted snapshot.
6. Run focused and hostile-metadata suites, then commit as `feat: verify signed knowledge snapshots`.

### Task 3: Add atomic local snapshot persistence and fallback selection

**Files:**
- Create: `src/macwise/knowledge/store.py`
- Create: `tests/knowledge/test_store.py`
- Modify: `src/macwise/catalog.py`
- Test: `tests/test_catalog.py`

1. Write failing tests for read-only absent state, staging, verified activation, immutable revision directories, atomic active pointer, previous-revision rollback, corrupted-active refusal, bounded retained revisions, concurrent update locking, and reset-to-bundled behavior.
2. Add selection tests proving bundled catalog fallback works without state/network and shared exact matchers augment rather than overwrite local facts.
3. Observe RED.
4. Implement the store using the existing platform state root and locking patterns; never mutate the Hugging Face cache or bundled resources.
5. Implement a knowledge-provider interface consumed by catalog matching, with deterministic precedence and provenance on every assessment.
6. Run knowledge/catalog/overlap suites and commit as `feat: activate verified knowledge snapshots`.

### Task 4: Implement bounded Hugging Face revision downloads

**Files:**
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Create: `src/macwise/knowledge/huggingface.py`
- Create: `src/macwise/knowledge/update.py`
- Create: `tests/knowledge/test_huggingface.py`
- Create: `tests/knowledge/test_update_service.py`

1. Add a bounded direct `huggingface_hub` dependency and refresh the lockfile.
2. Define an injected downloader protocol and write failing fake-adapter tests proving the service first resolves an immutable commit, downloads only allowlisted files at that commit, enforces timeout/offline/bounds, verifies before staging, activates atomically, preserves the prior revision on every failure, and records a sanitized last-error status.
3. Add request-privacy tests proving repository/revision/filename are the only application-controlled download fields and no software names, IDs, paths, usage, startup, or recommendation data enter the adapter.
4. Observe RED.
5. Implement the update service and a narrow `huggingface_hub` adapter using dataset `repo_type`, configurable public repo ID, explicit revision, isolated MacWise cache directory, and `local_files_only` offline support.
6. Run focused tests entirely against fakes/local fixtures—no network-dependent unit tests—and commit as `feat: download immutable knowledge revisions`.

### Task 5: Add novice-facing knowledge commands

**Files:**
- Modify: `src/macwise/cli.py`
- Modify: `src/macwise/help_text.py`
- Create: `tests/cli/test_knowledge_commands.py`

1. Write failing CLI tests for `macwise knowledge status`, `update`, and `reset` help and behavior.
2. Require `update` to state that it contacts a public repository, reveal no inventory, show resolved revision/signature/counts, and refuse noninteractive ambiguity.
3. Require `status` and normal scan/explain commands to remain network-free and show bundled/shared provenance plus staleness.
4. Require reset to preview the exact shared revision being deactivated and use explicit confirmation while preserving downloaded files for rollback.
5. Observe RED, implement the minimal Typer group and injected services, then rerun CLI/help/privacy suites.
6. Commit as `feat: add shared knowledge controls`.

### Task 6: Merge shared claims into explain and compare without overclaiming

**Files:**
- Modify: `src/macwise/services/overlap.py`
- Modify: `src/macwise/cli.py`
- Modify: `src/macwise/reporting/markdown.py`
- Test: `tests/services/test_overlap_analysis.py`
- Test: `tests/cli/test_phase_three_views.py`
- Test: `tests/reporting/test_reports.py`

1. Write failing tests for version/macOS applicability, expired claims, conflicting sources, vendor-confirmed versus community-reported evidence, source citations, retrieval dates, lifecycle status, known issues, fixed versions, and alternative relationships.
2. Assert that public claims never override installed version/path/dependency/use facts and never independently produce remove/disable/apply authority.
3. Observe RED.
4. Add pure applicability and conflict-resolution functions with explicit unknown/stale/conflict output.
5. Render separate `Shared public knowledge` sections in explain/compare/Markdown with URLs, dates, basis, confidence, and active snapshot revision.
6. Run analysis/reporting/safety suites and commit as `feat: cite shared public knowledge`.

### Task 7: Seed, validate, document, and prove the local pipeline

**Files:**
- Create: `knowledge/README.md`
- Create: `knowledge/schema/` validation artifacts as required by Tasks 1–2
- Create: `scripts/build_knowledge_snapshot.py`
- Create: `scripts/verify_knowledge_snapshot.py`
- Modify: `README.md`
- Modify: `docs/getting-started.md`
- Modify: `docs/privacy.md`
- Modify: `docs/threat-model.md`
- Modify: `DECISIONS.md`
- Modify: `PROGRESS.md`
- Modify: `TASK_QUEUE.md`
- Test: `tests/repository/test_public_foundation.py`

1. Convert the current bundled public catalog into a sanitized seed dataset with explicit sources/review dates where defensible; leave unsupported claims absent.
2. Add deterministic build/verify scripts and repository tests for schema, signatures, source URLs, private-path patterns, prompt text, duplicate identities, cross references, and reproducible manifests.
3. Document update networking, caching, rollback, privacy, contribution review, source hierarchy, freshness, and limitations.
4. Record the dependency/trust/governance decision and exact acceptance evidence.
5. Run the full test, format, lint, type, build, privacy, and repository gates.
6. Build a local signed fixture repository, run update/status/explain/offline/rollback end to end from a clean wheel and clean clone, and save only aggregate evidence.
7. Commit and push the verified local implementation. Do not create or publish the Hugging Face dataset without separate account authorization.

### Task 8: External Hugging Face publication acceptance

**Files:**
- Modify only after explicit authorization: dataset repository files and MacWise default configuration
- Modify after verified publication: `PROGRESS.md`, `TASK_QUEUE.md`, release documentation

1. Obtain the authorized Hugging Face namespace/repository ID and maintainer credentials outside logs.
2. Create the public dataset repository and dataset card with the approved license and governance policy.
3. Publish one signed, validated snapshot and record its immutable commit revision.
4. Configure MacWise's default repo/trust key through a reviewed commit.
5. From a new clone and empty cache, run explicit update, offline reuse, pinned rollback, corrupt-download refusal, and inventory-request privacy inspection.
6. Record exact public evidence and hosted CI; only then claim the shared database publicly operational.

