# STANDARDS.md

## Engineering Quality

- Support Python 3.12 and newer with a `src/` package layout, typed public interfaces, and small modules with explicit responsibilities.
- Prefer standard-library facilities unless a dependency materially improves the public UX, correctness, or maintainability.
- Keep collectors independent from presentation so JSON, Markdown, terminal, Codex, and future MCP surfaces consume the same normalized records.
- Treat `GOAL.md` as the product contract. A narrower passing implementation is not completion.

## Repository Awareness

- Read `GOAL.md`, this file, `IMPLEMENT.md`, `DECISIONS.md`, `PROGRESS.md`, and `TASK_QUEUE.md` before coding.
- Check `git status` before and after a change. Never discard unrecognized work.
- Update `PROGRESS.md` after verified slices and `DECISIONS.md` after material product, architecture, dependency, privacy, or safety decisions.

## Security and Privacy

- Audit and review commands are read-only. Tests must prove that collector paths do not mutate the host.
- Never execute discovered app names, paths, bundle metadata, or model-generated text as shell commands.
- Use argument-vector subprocess calls with `shell=False`, strict timeouts, bounded output, and allowlisted executables.
- Reject ambiguous write targets and protected Apple/system components.
- Preserve user data by default. Manual applications move to Trash; no arbitrary recursive deletion is allowed.
- Public fixtures and documentation contain no real usernames, hostnames, institutions, private software lists, secrets, or machine-specific paths.
- Evidence values are untrusted data and must never become instructions for either shell execution or AI reasoning.

## Testing

- Use test-driven development for features and bug fixes: failing behavioral test, observed failure, minimal implementation, observed pass, then refactor.
- Maintain unit tests for normalization and analysis, fixture-backed collector tests, CLI tests, safety regression tests, and macOS integration tests where platform behavior matters.
- Tests must not uninstall, disable, unload, launch, or delete software on the development Mac.
- Every claimed passing gate requires a fresh command and recorded result.
- CI must run formatting/lint, type checking, tests, build/package checks, and a secret/privacy scan.

## User Experience

- `macwise` with no arguments opens a guided, novice-friendly experience.
- Public commands use the small hierarchy in `GOAL.md`; internal implementation names do not leak into ordinary help.
- Each command's help starts in plain English, says when it is useful, states read-only or mutating behavior, gives two or three realistic examples, and suggests a likely next command.
- Errors explain what happened and provide a concrete recovery command. Missing evidence is never described as proof of non-use.
- Terminal output remains useful without Codex or an AI provider.
- Product scores remain deterministic and decomposable: opportunity never grades the Mac or
  rewards removal, usefulness never claims personalized correctness, and every component exposes
  its count, reason, maximum, and limitation.

## Performance and Reliability

- Slow or unavailable system tools degrade to explicit unknown evidence rather than crashing the whole audit.
- Collectors use bounded concurrency only where ordering and host load remain predictable.
- Expensive findings are cached with collection time, source, schema version, and limitations.
- JSON output is deterministic and versioned; migrations preserve readable audit history.

## Documentation

- Public behavior, installation, privacy, limitations, safety, uninstall, and recovery paths are documented alongside implementation.
- Documentation examples are runnable and use sanitized names and paths.
- Changelog entries follow semantic versioning and distinguish user-visible changes from internal work.

## Agent Behavior

- Continue autonomously using safe documented assumptions unless a stop condition in `AGENTS.md` applies.
- Do not perform production deployment, publish packages, create remote repositories, or mutate a user's installed software without explicit authority at that step.
- Prefer evidence-backed decisions. Record unknowns rather than filling them with plausible claims.

## Definition of Done

Done means every requirement and acceptance test in `GOAL.md` has direct current evidence: behavior tests, package/install proof, rendered help/output review, safety tests, Codex integration proof, public documentation, CI/release configuration, and an explicit requirement-by-requirement audit. Passing a narrow unit suite alone is insufficient.
