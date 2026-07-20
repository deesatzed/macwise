# GOAL_SIMPLE_UX.md — Make MacWise Simple for a First-Time Mac User

## How to run this goal

From the repository root, start:

```text
/goal GOAL_SIMPLE_UX.md
```

## OUTCOME

Make MacWise understandable and useful to a first-time, nontechnical Mac user without
weakening its evidence, privacy, or cleanup-safety rules.

A user who knows how to open Terminal but does not know Python, Homebrew internals, package
managers, launch agents, or MacWise command names must be able to:

1. install or evaluate MacWise using one clearly explained path;
2. run one obvious starting command;
3. receive a short checkup that says what deserves attention first and why;
4. inspect a finding through guided choices instead of memorized commands;
5. understand what MacWise knows, guesses, and cannot determine;
6. see the possible benefit and limitation of every suggested action;
7. create a cleanup preview without changing the Mac; and
8. finish with a plain-English summary that confirms whether anything changed.

The primary experience must answer:

> What should I look at first, why should I care, and what is the safest next step?

This is a UX and workflow goal. It does not authorize package publication, GitHub Pages
deployment, Homebrew distribution, live cleanup of the development Mac, or the future shared
online knowledge database.

## PROOF OF DONE

### A. One clear first-run journey

1. A clean, isolated installation or trusted-checkout smoke opens the same novice journey shown
   in the public documentation.
2. Running `macwise` presents one recommended starting choice, visibly distinguished from
   specialist reviews.
3. The recommended choice performs a fresh read-only checkup and produces a bounded summary
   containing:
   - three to five highest-priority supported findings;
   - why each finding may matter;
   - evidence strength and important uncertainty;
   - possible benefit of reviewing it;
   - what MacWise is not claiming;
   - one numbered next action; and
   - an explicit statement that no changes were made.
4. A user can continue through numbered prompts without learning a subcommand.
5. Every guided action remains available as a deterministic CLI command for automation and
   accessibility.

### B. Fix the discovered workflow gaps

The implementation and tests must close all of these gaps:

1. **Installation clarity:** Explain `uv` in one sentence, separate the after-publication path
   from the current trusted-checkout path, detect a missing `uv` or missing executable, and give
   one exact recovery step. Do not claim that an unpublished registry install works.
2. **Single starting point:** Reconcile the competing `doctor`, `scan`, and `score` starting
   instructions. The novice path has one recommended start; diagnostics and specialist commands
   remain available but secondary.
3. **Collection freshness:** State whether a command is collecting fresh evidence, reusing a
   saved snapshot, or reading an explicitly supplied report. Show collection time when it helps
   prevent stale-result confusion. Never imply that `scan` persisted state when it did not.
4. **Bounded output:** Default interactive views show at most the information needed for the next
   decision. Long inventories provide an exact “show more/show all” choice and retain structured
   output for complete evidence.
5. **Understandable opportunity result:** Do not present the Opportunity Profile as a health
   grade. Lead with a plain-language level or count such as “Review opportunities found,” explain
   that a high result does not mean the Mac is bad, and keep the numerical detail available.
6. **Understandable usefulness result:** Explain that this measures confidence in the report’s
   coverage and structure, not the user or the health of the Mac. Identify the largest missing
   evidence that prevented a higher result.
7. **Useful identification flow:** An item needing identification must show verified local facts.
   A normal checkup automatically tries identification unless `--offline` is used or public
   information is unavailable. That checkup-only lookup sends one app identity at a time, never
   uploads an inventory, and never invents a purpose. Public facts are not authoritative for
   cleanup.
8. **Guided cleanup planning:** A user can move from an explained finding to “add to possible
   cleanup plan” through numbered choices. Planning stays read-only. Apply and undo retain their
   existing separate exact approvals and fresh revalidation.
9. **Benefit-aware recommendations:** Each suggested review or action states the plausible
   benefit, what it will not accomplish, confidence, prerequisites, and material risk or
   uncertainty. Do not promise speed, space, safety, or backup improvement without evidence.
10. **Final summary:** At the end of a guided review, show what was found, what the user reviewed,
    what remains uncertain, the recommended next step, whether a plan was created, and whether
    the Mac changed.

### C. Novice comprehension acceptance

Create a deterministic, sanitized first-run fixture and a scripted acceptance walkthrough. A
reviewer reading only the rendered terminal transcript must be able to answer all of these without
consulting other documentation:

1. Did MacWise change the Mac?
2. What are the top findings?
3. Why might the first finding matter?
4. Is the finding verified, inferred, user-confirmed, or unknown?
5. What does MacWise not know?
6. What is the next safest action?
7. How can the user stop without doing anything?
8. If a plan exists, has it already been applied?

The transcript must not expose real usernames, hostnames, paths, software inventories, secrets,
or machine-specific data.

### D. Required verification

Run and record fresh evidence for:

```bash
uv run pytest
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv build
git diff --check
```

Also prove:

1. focused CLI tests for every new or changed guided branch;
2. non-TTY behavior exits safely and never waits for input;
3. JSON and Markdown outputs remain deterministic and complete;
4. read-only paths perform no host mutation;
5. planning performs no host mutation;
6. apply/undo approval, revalidation, recovery, and safety tests do not regress;
7. a clean isolated wheel or clean-clone smoke completes the novice journey;
8. a real Mac read-only smoke is assessed using aggregate, sanitized evidence only; and
9. README, getting-started guide, demo, launch page, root help, command help, and actual behavior
   agree.

Save a sanitized acceptance artifact under `docs/` and update `PROGRESS.md`, `TASK_QUEUE.md`, and
`DECISIONS.md` when the corresponding evidence or decision exists.

## SCOPE

### May modify

- `src/macwise/cli.py` and existing CLI/presentation modules
- analysis and reporting modules needed for prioritization and summaries
- immutable models or persistence only when necessary to express freshness or session state
- tests and sanitized fixtures
- `README.md`
- `docs/getting-started.md`
- `docs/demo.md`
- `docs/index.html` and its local static assets
- `GOAL.md`, `STANDARDS.md`, `IMPLEMENT.md`, `DECISIONS.md`, `PROGRESS.md`, and `TASK_QUEUE.md`
  only where the accepted UX contract or verified progress requires alignment

### Read and preserve

- existing evidence provenance and unknown-state semantics
- the current versioned audit schema unless an additive migration is justified and tested
- deterministic command equivalents for interactive actions
- the read-only Codex integration boundary
- existing release-candidate packaging and CI behavior

### Out of scope

- publishing to PyPI or creating a release tag
- enabling GitHub Pages or production deployment
- Homebrew distribution
- live web search or automatic online enrichment outside the privacy-bounded, automatic
  checkup-only public identification feature recorded by D-041
- the proposed Hugging Face/shared knowledge database
- accounts, telemetry, analytics, or inventory uploads
- GUI or native macOS application packaging
- broad visual redesign unrelated to the first-run journey
- changing or removing real installed software during development or acceptance

## CONSTRAINTS

1. Preserve the verified/inferred/user-confirmed/unknown evidence model.
2. Missing evidence must never become a claim of non-use, safety, backup coverage, or
   removability.
3. Do not turn the Opportunity Profile into a health, cleanliness, performance, or user grade.
4. Do not present the Usefulness Score as proof of personalized correctness or outcomes.
5. Do not add an AI provider, account, telemetry, inventory upload, or background update. D-041
   permits only automatic checkup-only public identification with a visible `--offline` escape
   hatch; public facts are not authoritative for cleanup.
6. Do not silently save scans. Any saved file or persistent state must be explicit, bounded,
   documented, privacy-reviewed, and covered by migration/recovery tests.
7. Keep noninteractive commands scriptable. Do not make automation parse interactive prose.
8. Keep terminal output accessible without color and understandable at ordinary terminal widths.
9. Treat installed names, metadata, paths, catalog text, and user input as untrusted data.
10. Do not weaken approvals, dependency checks, protected-target checks, rollback records,
    revalidation, or undo verification.
11. Do not remove or weaken tests to make the goal pass.
12. Do not add dependencies unless the UX cannot be implemented safely with the current stack;
    document any justified dependency decision.
13. Preserve user privacy in fixtures, documentation, commits, and aggregate real-Mac evidence.

## ITERATION

1. Read the repository truth files and inspect the actual CLI, reports, tests, and current
   documentation before editing.
2. Record the novice journey as a compact state diagram and define the exact bounded output
   contract before implementation.
3. Establish a sanitized transcript baseline and classify every line as useful, confusing,
   redundant, missing, or unsafe.
4. Work test-first in small vertical slices:
   - recommended first-run entry;
   - prioritized short summary;
   - freshness explanation;
   - guided finding investigation;
   - unknown-item choices;
   - guided plan handoff;
   - final session summary;
   - documentation alignment.
5. For each slice, observe a focused test fail for the missing behavior, implement the minimum
   coherent change, pass the focused test, then run the nearest regression tests.
6. After every meaningful slice, manually render the terminal flow at normal and narrow widths.
7. Use the real Mac only for read-only collection and sanitized aggregate assessment. Use
   fixtures, temporary roots, and fake adapters for planning/apply/undo tests.
8. Update durable progress and decisions with actual command results, limitations, and remaining
   risks. Do not record intended work as completed work.
9. Before completion, repeat the entire novice journey from a clean isolated artifact, then run
   the full verification gate.

## UX METRICS

Use these acceptance metrics for the sanitized first-run journey:

| Metric | Required result |
|---|---:|
| Commands a novice must memorize before the first useful summary | 0 |
| Recommended starting choices | 1 |
| Default priority findings | 3–5 |
| Screens before the first useful summary | 1 after choosing the recommended action |
| Unexplained internal terms in the primary journey | 0 |
| Findings with reason, uncertainty, benefit, limitation, and next action | 100% |
| Mutations during checkup, review, explain, compare, score, or plan | 0 |
| Explicit “MacWise changed nothing” confirmation on read-only completion | 100% |
| Long lists displayed without a bounded default or show-more path | 0 |
| Conflicting first-step instructions across product and public docs | 0 |
| Acceptance questions in section C answerable from transcript | 8/8 |

Do not optimize these numbers by hiding material evidence. Complete evidence must remain available
through deterministic detail and structured-output paths.

## STOP

Pause and provide an evidence-backed blocker report only if:

1. the change requires weakening an existing safety or privacy invariant;
2. a product decision would materially expand scope beyond this goal;
3. required verification cannot run in the available environment;
4. the same failure remains after three distinct, documented mitigation attempts;
5. completion requires credentials, publication, deployment, destructive host actions, or
   sensitive data; or
6. the existing audit/report architecture cannot support the journey without an incompatible
   schema or public-API change.

Safe assumptions may be made, recorded in `PROGRESS.md`, and tested. Ordinary implementation
choices are not blockers.

## COMPLETE

Mark this goal complete only when:

1. every item in **PROOF OF DONE** has current evidence;
2. every discovered workflow gap in section B is implemented or explicitly demonstrated to be
   already satisfied;
3. every UX metric meets its required result without hiding material evidence;
4. the sanitized clean-install transcript answers all eight novice acceptance questions;
5. the full test, format, lint, type, build, privacy, safety, clean-install, and documentation
   gates pass;
6. `git diff --check` is clean;
7. the final report lists changed files, verification commands and results, remaining limitations,
   and any deliberately deferred work; and
8. no publication, deployment, real cleanup, or other out-of-scope action was performed.

Implementation alone is not completion. Tests arbitrate, the transcript demonstrates the user
experience, and the Markdown truth files record the result.
