# Sanitized walkthrough

This transcript uses fictional products and paths. It demonstrates the shape of verified
MacWise output without publishing a real person's software inventory. Exact wording varies with
the evidence available on each Mac.

## Start with the recommended checkup

```text
$ macwise checkup
Fresh read-only checkup
Collected: 2026-07-19T14:00:00+00:00
This is fresh evidence collected for this command. It was not silently saved.

What deserves attention first

1. Review software that starts automatically (5 observed)
   Why: Found 5 startup items; 2 appeared idle and 4 had a matched owner.
   Evidence: Launch-item and Homebrew-service records visible to read-only collectors.
   Possible benefit: Reviewing them can clarify unwanted background activity.
   What this does not prove: A startup item is not automatically unnecessary or slow.
   Safest next step: macwise startup

Confidence in this report: 78/100
Largest missing evidence: Evidence coverage is incomplete.

MacWise changed nothing on this Mac.
```

The timestamp and counts are fictional. The real checkup shows at most five priority domains.

## Score the audit, not the person or Mac

```text
$ macwise score
MacWise scorecard

Review opportunities found: Moderate (44/100 detail score)
This counts supported topics worth reviewing. It does not grade this Mac or its owner.

- Startup attention: 8/20 (5 observed)
- Tool overlap: 8/20 (2 observed)
- Storage review: 10/20 (5 observed)
- Possible non-use: 0/15 (0 observed)
- Knowledge gaps: 8/15 (8 observed)
- Backup attention: 10/10 (3 observed)

Confidence in this report: 78/100
This measures evidence coverage and explanation structure. It does not prove personalized correctness.
Largest missing evidence: Evidence coverage is incomplete.
```

These fictional values demonstrate interpretation. Each real component also prints why points
were awarded, its limitation, and the next focused commands. A zero possible-non-use component
means no item met the cautious evidence requirement; it is not converted into a hidden guess.

## Review storage without APFS noise

```text
$ macwise storage
Storage volumes

- Macintosh HD: internal, 156 GiB free, /
- Project Drive: external, 1.5 TiB free, /Volumes/Project Drive
- Backup Drive: external, 77 GiB free, /Volumes/Backup Drive

Showing 3 user-relevant mounted volumes. Use --all for support and unmounted volumes.
This command is read-only. MacWise did not change this Mac.
```

## Understand one application

```text
$ macwise explain Harbor
Harbor

Verified facts
- Type: application
- Installed size: 2.3 GiB
- Usage: recently used (medium confidence)

Inferred findings
- Catalog roles: container desktop, container runtime bundle
- Related overlap: Dockyard — strong substitute

Unknowns and limitations
- Backup coverage: not verified

Guarded guidance: keep
- Current use or dependency evidence supports keeping this item.
```

“Recently used” is limited evidence, not a permanent requirement assessment.

## Compare overlap without declaring a winner

```text
$ macwise compare Harbor Dockyard
Role-aware comparison

Actual-use comparison: Harbor has stronger observed use evidence than Dockyard.

Harbor and Dockyard
Relationship: strong substitute
Shared capabilities: containers, images
Harbor unique: integrated desktop controls
Dockyard unique: daemonless container workflow

Guarded guidance
- Keep: current use evidence supports keeping Harbor.
- Learn: Dockyard may teach an alternative container workflow.
- No recommendation: available evidence does not justify consolidation.
```

Overlap starts a review; it does not authorize removal.

## Preview before any cleanup

```text
$ macwise plan add "SketchNote"
Added SketchNote to cleanup plan revision 1. No installed software or user data changed.

$ macwise plan show
Candidate: SketchNote
Action preview: move the exact application bundle to Trash
Related data: preserved
Approval: not granted
Rollback: restore the exact bundle if the destination remains safe
```

Apply performs fresh revalidation and requires an exact approval phrase. Undo has a separate
approval. This walkthrough intentionally stops before either mutating command.

Return to [Getting started](getting-started.md), the [launch page](index.html), or the
[repository README](../README.md).
