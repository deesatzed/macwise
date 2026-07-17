# AGENTS.md

## Standing Codex Rules

Before coding, read these files if present:

1. `GOAL.md`
2. `STANDARDS.md`
3. `IMPLEMENT.md`
4. `DECISIONS.md`
5. `PROGRESS.md`
6. `TASK_QUEUE.md`

Treat these files as the project source of truth.

## Autonomous Progress Rule

When running in autonomous mode, do not ask the user for clarification unless the project is truly blocked.

If information is missing but a safe assumption can be made:

- make the assumption,
- document it in `PROGRESS.md`,
- continue.

Stop only for:

- missing credentials,
- missing API keys,
- missing user accounts,
- destructive actions,
- production deployment,
- sensitive data risk,
- legal/compliance uncertainty,
- repeated failure after mitigation attempts,
- product decision that would materially change scope.

## Claude Code Delegation

Codex may use Claude Code as a bounded second-opinion worker when the local `claude` CLI is installed.

Claude delegation is allowed for:

- bounded implementation tasks,
- code review,
- bug triage,
- test gap analysis,
- loophole search,
- first-principles alternatives,
- release readiness.

Codex remains the orchestrator and final decision-maker.

Before delegating:

- create a specific handoff prompt,
- include only relevant context,
- define what Claude may edit,
- define what Claude must not touch,
- request structured Markdown output.

After delegating:

- read Claude's response,
- classify each recommendation as Accepted / Rejected / Needs Investigation,
- implement only accepted recommendations,
- update `PROGRESS.md`,
- update `DECISIONS.md` if needed.

Do not let Claude perform broad repo rewrites.
Do not use unsafe permission bypass flags.
Do not pass secrets, PHI, credentials, private keys, or unnecessary sensitive data to Claude.
Prefer read-only delegation unless the task is tightly scoped and safe.

## Core Rule

Codex decides. Claude contributes. Tests arbitrate. Markdown remembers.
