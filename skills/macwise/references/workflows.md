# MacWise conversational workflows

## Explain AI-app overlap and actual use

For a request such as “Explain which AI apps overlap and which ones I actually use”:

1. Call `audit_mac` to establish one current snapshot and expose decisive collector
   limitations.
2. Use `list_software` only if exact AI-app identities are not already known.
3. Call `find_overlaps` with exact returned identities. Report only catalog-backed
   relationships and their limitations.
4. Call `inspect_software` for each relevant identity to obtain direct-use,
   dependency, and installation evidence.
5. Present verified facts, deterministic inference, and unknowns separately. If usage
   evidence is absent, say “No reliable use evidence was found”; never say “unused.”
6. Explain learning value and unique capabilities separately from actual use. Do not
   turn overlap alone into a removal recommendation.

## Cleanup question

For “Can I remove this?” or another cleanup question:

1. Resolve one exact identity and inspect its evidence.
2. Call `get_removal_preview` only for a pure, nonpersistent explanation.
3. State that the result is not a saved plan, approval, or action.
4. Route any state change to the standalone terminal: `macwise plan`, review its exact
   preview, then separately run `macwise apply`; use `macwise undo` when technically
   possible.
5. Never generate an approval phrase or fingerprint for the user, and never execute the
   terminal sequence from the Codex integration.
