# Scorecard evaluation

Date: 2026-07-18

This evaluation used a private real-Mac read-only audit. It records only aggregate counts and
scores. No application names, package names, paths, username, hostname, serial number, or raw
inventory are included.

## Result

- Opportunity Profile: **70/100**
- MacWise Usefulness Score: **86/100**
- Collection and scoring runtime: **25.94 seconds**
- Collector state: 3 complete and 4 partial or unavailable

These are two different measures. The Opportunity Profile says several decisions deserve review;
it does not grade the Mac as bad. The Usefulness Score describes the structure and coverage of this
audit; it does not prove that every recommendation is personally correct.

## Opportunity components

| Component | Score | Aggregate evidence | Interpretation |
|---|---:|---:|---|
| Startup attention | 20/20 | 28 startup items; 7 idle; 14 owner-matched | Review owned and idle items individually; do not disable all startup entries. |
| Tool overlap | 16/20 | 6 total relations; 4 comparison-worthy | Compare unique workflows and observed use; complementary pairs earned no points. |
| Storage review | 15/20 | 69 measured apps; 22 at least 500 MiB; no low-free-space mounted volume | Review large bundles, but do not treat bundle size as guaranteed reclaimable space. |
| Possible non-use | 0/15 | 0 supported cautious non-use findings | Make no unused/removal claim from missing evidence. |
| Knowledge gaps | 15/15 | 53 records with unknown purpose | Research or identify these records; unknown is not a removal recommendation. |
| Backup attention | 4/10 | Backup age/staleness warning present | Verify that current backups run and are usable before relying on cleanup recovery. |

## Usefulness components

| Component | Score | What the result establishes |
|---|---:|---|
| Evidence coverage | 16/25 | Useful local evidence was collected, but four collector surfaces remained incomplete. |
| Decision yield | 25/25 | The audit produced enough bounded comparison, storage, startup, and guarded-guidance signals for focused review. |
| Explanation quality | 15/20 | Most supported findings retained basis/confidence/limits, but the structure was not universal. |
| Safety integrity | 20/20 | Unknowns, backup caveats, closed guidance actions, and non-use evidence boundaries remained intact. |
| Review efficiency | 10/10 | All five focused review domains contained results and have bounded default views. |

## Recommended next reviews on this Mac

1. Start with owner-matched idle startup items; confirm purpose before considering a startup plan.
2. Compare the four non-complementary overlap relations and preserve unique workflows or data.
3. Review the 22 large application bundles, starting with current use and related-data evidence.
4. Research the unknown-purpose list instead of treating it as an uninstall list.
5. Confirm why the latest verifiable backup is stale and complete a fresh usable backup if needed.
6. Make no unused-software change from this run because no item met the supported non-use labels.

## Metric assessment

The result is positive because it compresses a large inventory into five concrete review paths,
preserves the zero non-use result, and exposes incomplete evidence rather than hiding it. The two
scores must remain separate: combining them would confuse “many things worth reviewing” with
“MacWise explained them well.”
