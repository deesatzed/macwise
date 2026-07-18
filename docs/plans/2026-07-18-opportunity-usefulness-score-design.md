# Opportunity and Usefulness Score Design

## Objective

Add a deterministic, inspectable scorecard that answers two separate questions:

1. What kinds of worthwhile software-management decisions did MacWise surface on this Mac?
2. How effectively did MacWise turn the available evidence into understandable, safe guidance?

The scorecard must never equate a high score with a bad Mac, reward uninstalling software, or hide
missing evidence inside a single grade.

## User experience

`macwise score` runs the same read-only audit as `macwise scan` and prints two results:

- **Opportunity Profile (0-100):** the amount and variety of review-worthy evidence found.
- **MacWise Usefulness Score (0-100):** evidence coverage, decision yield, explanation quality,
  safety integrity, and review efficiency.

Each total is followed by its component scores, observed counts, limitations, and a small set of
next commands. Scores are descriptive, not cleanup authorization. Structured JSON and Markdown
are available using the same explicit output safeguards as scan.

## Opportunity Profile

The maximum is 100 points across six capped dimensions:

| Dimension | Points | Evidence |
|---|---:|---|
| Startup attention | 20 | Collected startup items, known ownership/state, and idle entries |
| Tool overlap | 20 | Exact catalog relations excluding complementary pairs |
| Storage review | 20 | Measured application bundles and low-free-space volume warnings |
| Possible non-use | 15 | Only supported possibly-unused or user-confirmed-unused labels |
| Knowledge gaps | 15 | Installed records with unknown purpose or unresolved catalog identity |
| Backup attention | 10 | Unavailable destination, stale/unknown last backup, and explicit limitations |

Each dimension uses fixed thresholds stored beside the scoring code and caps independently. A
zero means no supported opportunity was observed; it does not prove none exists. A high score
means “MacWise found several decisions worth reviewing,” not “remove more software.”

## MacWise Usefulness Score

The maximum is 100 points across five quality dimensions:

| Dimension | Points | Measurement |
|---|---:|---|
| Evidence coverage | 25 | Collector completion plus purpose/size/ownership coverage |
| Decision yield | 25 | Evidence-backed recommendations, overlap comparisons, measurable storage targets, and owned startup items |
| Explanation quality | 20 | Findings and recommendations retain basis, confidence, prerequisites, and limitations |
| Safety integrity | 20 | Unknowns remain explicit; no recommendation authorizes removal; backup claims remain guarded; partial collection stays visible |
| Review efficiency | 10 | Prioritized categories and bounded default views are available without discarding `--all` detail |

This is a quality-of-result metric, not a scientific benchmark or personalized outcome guarantee.
Every awarded or withheld component must include a plain-language reason.

## Data model and boundaries

- Add immutable score models with integer bounds, component keys, observed counts, reasons, and
  limitations.
- Compute scores only from the existing normalized `Audit` object; scoring performs no additional
  collection, web access, model call, persistence, or mutation.
- Keep threshold functions small and independently tested.
- Do not put a score into cleanup-plan approval logic.
- Do not rank users, machines, or products against one another.
- Do not publish this Mac's names, paths, or raw inventory.

## Real-Mac evaluation

After synthetic tests pass, run `macwise score --format json --output` into a private temporary
directory. Assess the component reasons against focused read-only commands such as `startup`,
`overlap`, `review largest`, `review unused`, `review unknown`, and `backups`. Save only aggregate
counts, component scores, runtime, and explicit limitations in repository evidence.

## Public documentation

The README and landing page will explain both scores using a sanitized example. Public claims may
state only what the implementation and real-Mac aggregate proof establish. The example must say
that high opportunity is not a negative grade and high usefulness does not prove every
recommendation is personally correct.

## Testing

- Unit-test zero, capped, mixed, partial-collector, stale-backup, unknown-heavy, and
  recommendation-heavy audits.
- CLI-test terminal/JSON/Markdown output, explicit output paths, overwrite refusal, and read-only
  language.
- Regression-test that complementary tools do not add overlap opportunity and that unknown
  evidence cannot be converted into possible non-use.
- Re-run the privacy contract, full test suite, formatting, lint, types, build, clean-clone smoke,
  and hosted CI.

