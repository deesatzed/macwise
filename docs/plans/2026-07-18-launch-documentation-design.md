# MacWise Launch Documentation Design

## Objective

Give a prospective user one honest, beginner-friendly path from discovering MacWise to
installing it, running a safe first review, understanding the result, and finding deeper
documentation. The public surface comprises the repository README and a lightweight static
landing page suitable for GitHub Pages.

## Audience and promise

The primary audience is a Mac user who wants to understand installed software without first
learning Homebrew internals, macOS service tools, or MacWise's architecture. The launch promise
is deliberately narrow: MacWise gathers local evidence, explains its limits, and keeps review
separate from cleanup approval. It does not promise omniscient app knowledge or automatic
cleanup.

## Chosen approach

- Keep the landing page in `docs/index.html` with local CSS and no JavaScript framework.
- Make the page usable directly from the checkout and compatible with GitHub Pages.
- Keep the README as the canonical compact technical entry point.
- Use sanitized, representative examples shaped by the verified CLI behavior.
- Link to focused getting-started, demo, privacy, threat-model, security, and release documents.
- State release evidence precisely: local gates and hosted CI are verified; PyPI and a GitHub
  Release remain unpublished until their external workflows succeed.
- Keep Homebrew distribution and the shared online knowledge database visibly deferred.

## Page structure

1. Hero: what MacWise does, release-candidate status, and installation/read-the-docs actions.
2. Trust strip: read-only review, explicit unknowns, and separately approved cleanup.
3. Example results: storage, startup, overlap, and explanation excerpts with sanitized names.
4. Workflow: scan, understand, compare, plan, and only then optionally apply.
5. Safety boundaries: what MacWise can and cannot change.
6. Installation: published-package command clearly separated from trusted-checkout evaluation.
7. Codex integration: optional and read-only.
8. Release status and documentation links.

## Visual direction

Use a calm native-Mac-inspired visual system: warm off-white canvas, deep ink text, restrained
blue and green accents, large readable type, compact terminal cards, and generous whitespace.
Avoid stock imagery, dashboards full of invented metrics, animation, and claims not supported by
the repository evidence. The page must remain legible at narrow mobile widths and with reduced
motion preferences.

## Verification

- Validate internal and repository links.
- Check public files for private usernames, machine paths, secrets, and real inventories.
- Confirm README commands and status claims against the current CLI and acceptance records.
- Render and inspect the landing page at desktop and mobile widths.
- Run the repository formatting, lint, type, test, build, privacy, and documentation gates.
- Do not enable production publication or create a release in this documentation pass.

