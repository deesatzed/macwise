# Contributing to MacWise

MacWise welcomes focused fixes, tests, documentation, sanitized macOS fixtures, and evidence collectors that preserve the product's novice-facing safety model.

## Before changing code

Read `GOAL.md`, `STANDARDS.md`, `IMPLEMENT.md`, `DECISIONS.md`, `PROGRESS.md`, and `TASK_QUEUE.md`. Check the current branch and working tree, then choose one coherent task.

## Development setup

```bash
git clone https://github.com/deesatzed/macwise.git
cd macwise
uv sync --locked --all-groups
```

Use synthetic fixtures. Never commit a real application list, username, hostname, institution, secret, private path, or external-volume name.

## Test-first workflow

For a behavior change:

1. Add a focused failing test.
2. Run it and confirm the failure is caused by the missing behavior.
3. Implement the smallest coherent change.
4. Run the narrow test and the complete gate.
5. Update project truth files when progress or a durable decision changes.

Complete local gate:

```bash
uv run pytest
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv build
```

## Collector rules

- Prefer plist or JSON output over formatted terminal tables.
- Use the fixed command adapter; never construct a shell command from discovered data.
- Apply time and output bounds.
- Turn missing sources into limitations or unknowns, not negative claims.
- Do not launch unknown applications.
- Do not add mutation to an audit collector.

## Pull requests

Keep changes scoped and explain user-visible behavior, safety impact, tests, and limitations. Do not claim a phase or feature complete without requirement-level evidence.
