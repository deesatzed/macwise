# Automatic App Research and Novice UX Design

## Status

Approved product direction, 2026-07-20. This design supersedes the network-free
unknown-item portion of `GOAL_SIMPLE_UX.md`; it does not change the separate
network-free `macwise-eval` boundary.

## Problem observed in real use

MacWise can collect a trustworthy local inventory, but common applications can
appear under **"unknown purpose"** because the bundled role catalog is small and
application bundles normally do not contain a plain-language purpose. The current
no-argument menu also presents eleven peer choices before the user sees any useful
result. Several detailed commands then expose a large, flat list with raw labels
and technical fields before explaining what matters.

For a new user, this is backwards: the product should first explain the Mac in a
small number of plain-language findings, and should identify ordinary software
without requiring the user to research it manually.

## Chosen experience

### First run

`macwise` displays only three choices:

```text
MacWise

Start here
1. Check up this Mac (Recommended)
   Find the few things worth reviewing. Nothing will be changed.

More options
2. Explore a specific topic
3. Help and command list

Choose 1-3:
```

Choice 1 is the only primary path. It runs one fresh, read-only audit, then
automatically identifies applications that lack a sufficiently trustworthy local
description. Choice 2 is a short second-level menu for Apps, Homebrew, Startup,
Storage, Backups, and Cleanup planning. Expert commands remain stable and
scriptable; they are not removed or made to parse interactive prose.

### Checkup result

The checkup has this fixed order:

1. **Your Mac at a glance** — a one-line scope and read-only confirmation.
2. **Start here** — one highest-priority supported finding with why it matters
   and one safe next action.
3. **Worth a look** — at most two more findings; users select a number only if
   they want details.
4. **Apps MacWise identified** — a small count and only unresolved exceptions,
   not a full inventory.
5. **What MacWise did not determine** — short, human-readable limitations.
6. **Nothing was changed** — repeated plainly at completion.

Every displayed finding contains exactly: what was observed, why it may matter,
what it does not prove, and the safest next step. Raw paths, all candidates,
machine-oriented collector statuses, and long lists remain behind explicit
`--all`, `scan --output`, and specialist review commands.

The primary UI calls an unresolved item **"Needs identification"**, not
"unknown purpose." It never implies that the item is unused, unwanted, unsafe,
or removable.

## Automatic app-identification design

### Provider order

For an application with no usable local description, MacWise resolves a purpose
in this order:

1. **Bundled catalog** — reviewed offline facts included with the package.
2. **Verified local cache** — prior public result whose identity, source, and
   expiry remain valid.
3. **Public web lookup** — an automatic, bounded request for that one unresolved
   application.

The initial web implementation uses a source-provider interface, not an AI model
and not an opaque generic answer. It gives first-party publisher pages and Apple
App Store listings priority. A fallback web-search provider may supply a candidate
only when the result identifies the same bundle identifier or developer/product
pair. Search-only name matches are marked tentative and may describe a purpose,
but never confer a safety, usage, overlap, removal, or cleanup conclusion.

This intentionally differs from the future signed shared knowledge database:
automatic lookup makes a narrow per-app request now; a later curated database can
reduce those requests and improve reuse. They share a claim schema and trust
rules, but neither is a prerequisite for the other.

### What leaves the Mac

One unresolved application lookup may contain only:

- bundle identifier, when available;
- application display name;
- signing publisher/team name, when available; and
- installed version only if a source supports version-specific facts.

It must never send an inventory, paths, user name, host name, serial number,
usage history, startup state, dependencies, storage, backups, plans, or other
installed software. There is no account, telemetry, background updater, or
inventory upload. `--offline` disables lookup and uses only bundled/cache data.

Before a first automatic lookup in a session, the terminal says plainly:

```text
Identifying 4 apps with public app information.
MacWise sends one app name or bundle ID at a time, never your app list or files.
Run with --offline to skip online identification.
```

This is automatic as requested, but visible rather than silent. A timeout,
offline machine, rate limit, or source failure yields **"Needs identification —
online information was unavailable"** with a recovery option. It never fabricates
a purpose or blocks the rest of the checkup.

### Claim and cache contract

Each accepted public claim is a bounded, typed record containing:

- exact matched identity and match method;
- concise purpose and category;
- source URL, source type, retrieval time, expiry, and confidence;
- publisher/product identity used to verify the match; and
- explicit limitations.

The cache is local, bounded, expiring, and atomically written. It is an
identification cache, not a scan archive. A cached claim is rendered as
"Public app information, checked 2026-07-20" with a source link. Conflicting or
expired claims remain explicit rather than merged into a confident sentence.

No public claim may overwrite observed local facts or create an overlap relation,
direct/indirect use finding, backup assertion, plan candidate, apply action, or
undo action. Cleanup safety remains governed by the existing deterministic
preflight and approval model.

## Safety and quality rules

- Requests use a fixed HTTPS client, strict timeouts, redirect policy, response
  size limits, and allowlisted provider adapters; untrusted response text is
  never executed or used as an instruction.
- The provider accepts structured facts only. It rejects missing identity,
  ambiguous identity, unsupported source, unsafe URL, overly long text, control
  text, stale schema, and conflicts that cannot be disclosed.
- Tests use injected fakes/local HTTP fixtures. The normal test suite never
  requires the public internet.
- The product records source, date, confidence, and limitation beside every
  public explanation, so users can distinguish local evidence from public
  information.
- Identification quality is measured separately from cleanup quality: resolution
  rate, exact-identity rate, cache freshness, unresolved reason, source coverage,
  and tested false-match refusal. It is never presented as a grade of the user or
  their Mac.

## Compatibility and migration

The existing `scan`, `review`, `explain`, `compare`, JSON, Markdown, and
noninteractive CLI contracts remain available. Structured audit exports include
public claims only when an explicit output mode permits it; default scan remains
local collection unless `--identify` is selected. The novice `checkup` owns the
automatic default because it is intentionally interactive and explains the
network boundary. This avoids silently changing automation or bulk-export
privacy expectations.

`GOAL_SIMPLE_UX.md` and D-039 remain valid for the single-checkup workflow,
bounded output, and read-only behavior. Their prohibition on live lookup is
superseded for this explicit, privacy-bounded checkup identification feature; a
new decision record must preserve that distinction.

## Acceptance evidence

The implementation is accepted only when:

1. a new-user transcript presents three initial choices and reaches a useful
   bounded checkup through the recommended first choice;
2. common fixture applications obtain cited purpose claims through a fake
   first-party/App Store provider while mismatched names and identities are
   refused;
3. request-capture tests prove only the four allowed fields can leave the Mac;
4. offline, timeout, malformed, conflicting, expired, and cached results are
   clear, nonfatal, and never called evidence of non-use or removability;
5. public claims cannot change overlap, usage, plan, apply, or undo outcomes;
6. all detailed views retain bounded defaults and a clear show-more path; and
7. README, getting-started, privacy, help, and landing-page examples accurately
   disclose automatic checkup lookup, `--offline`, local caching, and limits.

