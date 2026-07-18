# Getting started

## 1. Install and open

After publication, install the command-line app in its own managed environment:

```zsh
uv tool install macwise
macwise
```

If `uv` is not installed, follow the official installation instructions at
<https://docs.astral.sh/uv/getting-started/installation/>. Existing pipx users may use
`pipx install macwise` instead. Homebrew distribution is deferred to a later milestone.
Until `1.0.0rc1` is published, evaluate a trusted candidate checkout:

```zsh
git clone https://github.com/deesatzed/macwise.git
cd macwise
uv sync --locked --all-groups
uv run macwise doctor
uv run macwise
```

MacWise starts with a numbered menu. Choosing a read-only review never requires cleanup
permission. Start with Scan this Mac, then ask about one unfamiliar item.

## 2. Read the evidence labels

- **Verified** means MacWise observed a deterministic local fact.
- **Inferred** means multiple facts support a cautious interpretation.
- **User-confirmed** means your explicit preference supplied necessary context.
- **Unknown** means evidence is missing or ambiguous; it is not a negative answer.

Saved reports can contain private paths and inventory. Do not attach them publicly
without reviewing and redacting them.

## 3. Score the result without grading the Mac

Run `macwise score` after a scan. The Opportunity Profile measures how much supported evidence
deserves review. A high value does not mean the Mac is bad and does not reward removing software.
The separate MacWise Usefulness Score measures coverage, decision yield, explanation structure,
safety, and review efficiency. It does not prove personalized correctness.

Every component shows its points, observed count, reason, and limitation. Use the suggested
focused commands to inspect the evidence behind the score. JSON and Markdown scorecards contain
aggregate counts and no software names or paths.

## 4. Compare before planning

Use `macwise explain NAME`, `macwise compare LEFT RIGHT`, and `macwise overlap`.
Role overlap does not automatically mean interchangeability. Unique learning or workflow
value stays visible.

Long inventories are summarized by default. When the summary says more records exist,
use the exact suggested `--all` command to inspect the complete detail.

## 5. Understand where knowledge comes from

MacWise scans local application metadata and bounded output from macOS, Homebrew,
Spotlight, and Time Machine tools. It does not perform a live web search during a normal
scan. General purposes and overlap roles come from the catalog shipped with this version.
This makes results reproducible, but an unrecognized or newly changed product can remain
unknown until the catalog is updated.

## 6. Plan before applying

`macwise plan add NAME` creates an immutable preview. `macwise plan show` displays every
proposed action, blocker, rollback step, and limitation without changing installed
software. Unknown or protected targets remain blocked.

Only continue to `macwise apply` after reading the exact preview and approval phrase.
Apply re-collects evidence and refuses changed state. `macwise undo` uses a separate
approval and verifies reverse actions. Related user data is never included.

## 7. Optional Codex conversation

Run `macwise setup codex`, restart Codex, and type `$macwise`. The plugin can review
bounded local facts and pure removal previews, but cannot apply or undo anything. Return
to the terminal for all approval-gated cleanup.

If a command refuses, read its `Next:` guidance and use `macwise doctor` for collector or
recovery status.
