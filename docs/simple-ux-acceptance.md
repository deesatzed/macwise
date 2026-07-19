# Simple first-run UX acceptance

This sanitized transcript uses fictional inventory and paths. It is the acceptance surface for
the first-time journey; it contains no private machine inventory.

```text
$ macwise
MacWise

What would you like to do?

1. Check up this Mac (Recommended)
2. Review installed apps
3. Review Homebrew software
...

Choose 1-11: 1
Fresh read-only checkup
Collected: 2026-07-19T14:00:00+00:00
This is fresh evidence collected for this command. It was not silently saved.

What deserves attention first

1. Review software that starts automatically (5 observed)
   Why: Five startup items were observed; two appeared idle.
   Evidence: Local launch-item and Homebrew-service records.
   Possible benefit: Review can clarify unwanted background activity.
   What this does not prove: A startup item is not automatically unnecessary or slow.
   Safest next step: macwise startup

2. Identify software MacWise does not recognize (3 observed)
   Why: Three installed records had no known purpose in local evidence or the bundled catalog.
   Evidence: Verified local inventory compared with the bundled catalog.
   Possible benefit: Identification makes later decisions better informed.
   What this does not prove: Unknown does not mean unused or safe to remove.
   Safest next step: macwise review unknown

Confidence in this report: 78/100
This measures report coverage and structure, not a health grade or personalized truth.
Largest missing evidence: Application purpose coverage is incomplete.

MacWise changed nothing on this Mac.

Choose a finding number to review, or 0 to finish safely.
Choose 0-2: 2

Focused review
Identify software MacWise does not recognize

Unknown-item choices
1. SketchNote (application)
2. paper-tool (Homebrew formula)
0. Go back without choosing an item
Choose 0-2: 1

What would you like to do?
1. Show verified local facts
2. Tell MacWise what you use it for (this session only)
3. Leave it unknown
4. Add it to a possible cleanup plan
0. Return to the checkup summary
Choose 0-4: 1

Verified local facts
- Name: SketchNote
- Type: application
- Version: 2.1
- Location: /Applications/SketchNote.app
- Measured size: 640.0 MiB
MacWise did not search the web or upload this inventory.

Choose a finding number to review, or 0 to finish safely.
Choose 0-2: 0

Session summary
Reviewed: 1 priority
Still uncertain: 1 priority
No cleanup plan was created or applied.
You can stop here safely.
MacWise changed nothing on this Mac.
```

## Acceptance questions

1. **Did MacWise change the Mac?** No. It says this after the checkup and in the session summary.
2. **What are the top findings?** Startup items and unknown-purpose software in this fixture.
3. **Why might the first finding matter?** It may reveal unwanted background activity.
4. **What is the evidence status?** Local startup and inventory facts are verified; interpretation
   remains limited by the stated non-claims.
5. **What does MacWise not know?** It does not know whether a startup item is unnecessary or slow,
   and application purpose coverage is incomplete.
6. **What is the safest next action?** Review the focused startup evidence or choose a numbered
   unknown item; neither changes the Mac.
7. **How can the user stop?** Enter `0` at the review prompt.
8. **Was a cleanup plan applied?** No plan was created or applied in this transcript.

The interactive checkup reuses the one audit collected at the start. Direct specialist commands
collect their own fresh evidence. A saved report exists only when the user explicitly supplies an
`--output` path.
