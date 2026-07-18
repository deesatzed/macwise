# Shared Knowledge Database Design

## Goal

Give every MacWise user current, reusable public knowledge about common applications and Homebrew packages without uploading private installed-software inventories or requiring a MacWise service account.

## Product boundary

MacWise retains three distinct evidence layers:

1. **Local observed evidence** — installed versions, paths, sizes, dependencies, startup state, usage signals, storage, and backup facts collected on the Mac.
2. **Bundled fallback knowledge** — the small reviewed catalog shipped with the package so core explanations work offline from first launch.
3. **Shared public knowledge** — an optional, revisioned snapshot downloaded from a public Hugging Face dataset repository and matched entirely on-device.

Shared knowledge never overrides verified local facts. Every rendered claim identifies its layer, source, review date, and confidence. Missing, stale, conflicting, or version-inapplicable public claims remain explicit rather than silently becoming recommendations.

## Hugging Face repository

The canonical dataset is publicly readable and maintainer-write-only for version one. Hugging Face dataset repositories provide Git revision history, immutable commit revisions, dataset cards, JSON/JSONL support, and revision-aware downloads and caching. Community members may propose changes through a reviewed contribution workflow, but installed clients cannot write directly to the canonical dataset.

The initial repository contains:

```text
README.md
manifest.json
products.jsonl
relationships.jsonl
issues.jsonl
advisories.jsonl
sources.jsonl
signatures/manifest.ed25519
```

`manifest.json` declares the schema version, snapshot identifier, generated/reviewed timestamps, record counts, file SHA-256 digests, minimum compatible MacWise version, canonical repository, and signing-key identifier. The detached Ed25519 signature covers the canonical manifest bytes. MacWise ships the corresponding public trust key.

## Record model

Product records use a stable public product ID plus exact, entity-qualified matchers: bundle identifiers, exact app names, Homebrew formula/cask tokens, and known executable names. They contain roles, capabilities, unique capabilities, general learning context, lifecycle status, and source references.

Relationship records connect two stable product IDs with an explicit category, shared and unique capabilities, scope limitations, sources, and review date. No relationship is inferred from fuzzy names.

Issue and advisory records are version- and platform-scoped. They distinguish vendor-confirmed, structured-advisory, maintainer-confirmed, and community-reported evidence. Each claim has a source URL, publication and retrieval dates, status, confidence, affected/fixed versions when known, and expiration or revalidation policy.

Source records contain the canonical URL, publisher, source type, title, retrieval date, and optional content digest. Dataset text is untrusted data and is sanitized before display; it never becomes a command, path authority, or cleanup authorization.

## Client workflow

`macwise knowledge status` reports the active bundled/shared revision, age, source, signature state, record counts, and last update error.

`macwise knowledge update` is an explicit network operation. It downloads the manifest and signature, verifies the trust key and schema, applies strict file/record/output bounds, downloads files at the resolved immutable commit, verifies every digest, parses all records strictly, validates cross-record references, and atomically activates the complete snapshot. Failure preserves the previous verified snapshot.

`macwise knowledge reset` removes only the selected shared snapshot pointer and returns to bundled fallback knowledge. Cached older snapshots are retained under bounded cleanup policy for rollback, not mixed into active results.

Normal scan/review/explain commands never contact the network. They read the locally active snapshot. An optional update reminder may report staleness but cannot download silently.

## Privacy and contribution workflow

Dataset matching occurs locally. The update request reveals only ordinary HTTP metadata needed to download a public dataset; it does not contain the software inventory, usernames, paths, usage, startup state, or recommendations.

Version one does not implement client submissions. A later explicit proposal command may export one sanitized candidate record only after showing the exact payload and obtaining confirmation. Until then, contributors use the public repository review workflow. CI validates schema, sources, URLs, duplicate identities, reference integrity, prohibited private paths, prompt-shaped text, and signature generation before maintainers publish a snapshot.

## Recommendation safety

Public issues and alternatives provide context, not removal authority. Recommendations combine applicable shared claims with local evidence and continue to require local dependency, backup, ambiguity, protection, data, and rollback preflight. Community reports cannot independently produce remove or disable guidance.

## Evaluation

The shared database is evaluated separately from installation correctness:

- exact-match precision and collision rate;
- coverage of significant installed products;
- source validity and claim freshness;
- version/platform applicability accuracy;
- alternative/relationship expert agreement;
- stale/conflicting claim calibration;
- user task success and decision confidence;
- update latency, cache behavior, rollback, and offline operation;
- privacy proof that inventories never enter network requests.

The first milestone succeeds when a locally hosted synthetic dataset proves the entire signed-update/rollback/offline pipeline. Publication to a real Hugging Face repository is a separate credentialed acceptance step.

