# Simple First-Run UX Design

## Decision

Add `macwise checkup` as the single recommended first-run action and route menu choice 1 to it.
Keep `scan` as the complete inventory/report command, `score` as the transparent measurement
command, and `doctor` as troubleshooting. This avoids changing the meaning of established
structured outputs while giving novices one clear path.

## Journey

```text
macwise
  -> 1. Check up this Mac (recommended)
  -> fresh read-only collection
  -> 3-5 prioritized review cards
  -> numbered focus choices
  -> focused evidence or safe planning handoff
  -> session summary and explicit no-change statement
```

Each priority card contains: reason, evidence boundary, plausible benefit, non-claim or
limitation, and one focused next action. Interactive follow-up reuses the just-collected audit;
direct commands collect fresh evidence and say so. No scan is silently persisted.

## Prioritization

Use deterministic evidence already supported by MacWise. Rank domains, not individual removal
targets: stale/unavailable backup, low-free-space volumes or large measured apps, actionable
overlap relations, startup items needing review, cautious non-use findings, and unknown-purpose
records. Cap output at five cards. Unknown-purpose results are research prompts, never cleanup
recommendations.

## Safety and state

The checkup is read-only and keeps its audit only in process memory for the current interaction.
Planning remains an explicit immutable preview. Apply and undo remain outside the guided checkup
and retain exact approval, fresh revalidation, and recovery behavior. Non-TTY execution prints the
menu and exact `macwise checkup` command without prompting.

## Verification

Fixture-backed CLI tests prove prioritization, bounds, evidence language, interactive reuse,
unknown handling, safe plan handoff, final summary, and non-TTY behavior. Existing structured
scan/score and execution safety tests remain unchanged. A sanitized transcript and isolated-wheel
smoke provide artifact-level proof.
