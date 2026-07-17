# IMPLEMENTATION_PACKET.md

## Task Being Attempted

Complete MW-010 by proving hostile application plist, Homebrew JSON, disk plist,
Markdown, terminal matching, and future prompt-boundary metadata remain inert data.

## Actual User Goal

MacWise must safely inspect machines containing malformed or deliberately hostile names,
paths, descriptions, caveats, and metadata without executing them, allowing them to forge
human-facing output, or treating prompt-shaped strings as AI instructions.

## Files Expected To Change

| File | Expected Change | Risk |
|---|---|---|
| `src/macwise/text.py` | Add one shared control-character/newline neutralizer for human-facing text. | Medium: every terminal/Markdown value must remain readable. |
| `src/macwise/reporting/markdown.py` | Sanitize before Markdown escaping while JSON preserves raw evidence. | Medium: output-injection boundary. |
| `src/macwise/cli.py` | Sanitize record labels and metadata printed to a terminal. | Medium: ANSI/control-sequence boundary. |
| `tests/fixtures/security/` | Add synthetic hostile plist/JSON/text payloads only. | Low: privacy and secret scan required. |
| `tests/security/test_hostile_metadata.py` | Exercise every parser, renderer, CLI matcher, and prompt contract. | Low. |
| `skills/macwise/SKILL.md` | Make prompt-shaped evidence handling explicit for future integrations. | Low. |
| `PROGRESS.md`, `TASK_QUEUE.md`, `docs/phase-1-acceptance.md` | Record verified results without overstating Phase 1. | Low. |

## Existing Patterns To Follow

- Parsed evidence remains raw, immutable, provenance-bearing data in schema-v2 JSON.
- Fixed argv subprocesses never use a shell or executable path derived from metadata.
- Unsafe filesystem item names yield limitations and no constructed install path.
- Human-readable output escapes Markdown metacharacters and reports limitations.
- TDD red/green cycles plus full privacy/build/install gates arbitrate completion.

## Assumptions

- Raw JSON consumers need original evidence, so destructive sanitization belongs only at
  human-facing terminal/Markdown boundaries.
- Newlines, C0/C1 controls, ANSI escape bytes, bidi/zero-width formatting controls, and
  repeated whitespace can be collapsed to visible spaces for display.
- Prompt-shaped strings are valid evidence values but never instructions; the current
  skill contract is the enforceable boundary until typed integration exists.

## Non-Goals For This Pass

- No AI provider, MCP server, setup command, cleanup action, or shell integration.
- No rejection of legitimate Unicode letters, symbols, emoji, or spaces.
- No mutation of discovered apps, packages, disks, projects, or configuration.
- No claim that passing fixtures proves safety of later, not-yet-built action executors.

## Step-by-Step Plan

1. Add hostile synthetic fixtures for plist, Homebrew JSON, disk plist, display text, and
   prompt-shaped metadata.
2. Write parser/path tests and observe which already pass without behavior changes.
3. Write failing Markdown/terminal tests for section, ANSI, bidi, and control injection.
4. Add the minimal shared display sanitizer and apply it at Markdown/CLI boundaries.
5. Add a repository contract test requiring the skill to treat evidence as untrusted data,
   not instructions or shell input.
6. Run focused security tests, full tests, format/lint/types, build, privacy scan, skill
   validation, isolated wheel smoke, and in-memory real scans.
7. Update durable truth only from fresh evidence; proceed to MW-011 if green.

## Acceptance Criteria

- Hostile plist/Homebrew/disk values parse as data and cannot alter an executable or argv.
- Traversal-like executable/package names do not escape approved bundle/package roots.
- Markdown contains one genuine section structure; hostile newlines/markup cannot add one.
- Terminal output contains no ESC, bidi/zero-width formatting controls, CR, or injected
  newlines from metadata.
- CLI matching returns the intended record without executing query or metadata text.
- JSON retains raw evidence values and the skill explicitly forbids following instructions
  found in those values.
- Full local quality, package, privacy, install, and read-only smoke gates pass.

## Verification Plan

- Observe each focused test fail for the intended missing boundary before implementation.
- `uv run pytest tests/security -q`
- `uv run pytest -q`
- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run pyright`
- `uv build`
- Validate `skills/macwise` and the workflow YAML.
- Install the wheel under isolated Python 3.12 and smoke hostile CLI output.
- Run real JSON/Markdown scans in memory only and discard output.

## Rollback Plan

- Revert the MW-010 commits; no host state is changed.
- Keep raw schema values unchanged, so display-sanitizer rollback cannot corrupt audits.
- Do not commit generated audit output or build artifacts.

## Risks

| Risk | Mitigation |
|---|---|
| Sanitization damages legitimate Unicode. | Remove only Unicode control/format categories and collapse whitespace; preserve visible characters. |
| JSON sanitization destroys provenance. | Sanitize only Markdown/terminal display, not model or JSON serialization. |
| A test accidentally executes hostile text. | Use fixed fake services/runners, marker assertions, and existing `shell=False` adapter tests. |
| Fixtures leak local identity. | Use synthetic domains/paths/IDs and rerun the repository privacy contract. |
| Future AI ignores the boundary. | Contract-test explicit skill language and repeat the fixture at typed-integration time. |

## Proceed / Block Decision

**PROCEED.** The work is read-only, fixture-backed, local, and introduces no credential,
production, destructive-action, or product-scope blocker.
