# Getting started

## 1. Install and open

Public `pipx` and Homebrew commands are listed in the README but remain unavailable
until `1.0.0rc1` is published. From a trusted candidate checkout, run `uv sync --locked
--all-groups`, then `uv run macwise`.

MacWise starts with a numbered menu. Choosing a read-only review never requires cleanup
permission. Start with Scan this Mac, then ask about one unfamiliar item.

## 2. Read the evidence labels

- **Verified** means MacWise observed a deterministic local fact.
- **Inferred** means multiple facts support a cautious interpretation.
- **User-confirmed** means your explicit preference supplied necessary context.
- **Unknown** means evidence is missing or ambiguous; it is not a negative answer.

Saved reports can contain private paths and inventory. Do not attach them publicly
without reviewing and redacting them.

## 3. Compare before planning

Use `macwise explain NAME`, `macwise compare LEFT RIGHT`, and `macwise review duplicates`.
Role overlap does not automatically mean interchangeability. Unique learning or workflow
value stays visible.

## 4. Plan before applying

`macwise plan add NAME` creates an immutable preview. `macwise plan show` displays every
proposed action, blocker, rollback step, and limitation without changing installed
software. Unknown or protected targets remain blocked.

Only continue to `macwise apply` after reading the exact preview and approval phrase.
Apply re-collects evidence and refuses changed state. `macwise undo` uses a separate
approval and verifies reverse actions. Related user data is never included.

## 5. Optional Codex conversation

Run `macwise setup codex`, restart Codex, and type `$macwise`. The plugin can review
bounded local facts and pure removal previews, but cannot apply or undo anything. Return
to the terminal for all approval-gated cleanup.

If a command refuses, read its `Next:` guidance and use `macwise doctor` for collector or
recovery status.
