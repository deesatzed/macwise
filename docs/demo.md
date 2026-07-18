# Synthetic demo

This transcript uses fictional software and intentionally contains no real host paths or
inventory. Exact wording can vary with available evidence.

```text
$ macwise explain "SketchNote"
SketchNote

Verified
- Installed as an application.
- Stored on internal storage.
- No reliable last-use timestamp was available.

Inferred
- Its observed role is Markdown editing.

Unknown
- Missing last-use evidence does not mean the app was never used.

$ macwise compare "SketchNote" "WriteForge"
Relationship: partial overlap
- Both can edit Markdown.
- WriteForge has a verified publishing workflow not established for SketchNote.
- Recommendation: review both; no removal is authorized.

$ macwise plan add "SketchNote"
Plan saved. No installed software or user data changed.

$ macwise plan show
Candidate: SketchNote
Action preview: move the exact application bundle to Trash
Related data: preserved
Approval: not granted
Rollback: restore the exact bundle if the destination remains safe
```

The real CLI shows provenance, limitations, fingerprints, and recovery detail appropriate
to the current audit. See [Getting started](getting-started.md).
