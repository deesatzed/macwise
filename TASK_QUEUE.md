# TASK_QUEUE.md

Tasks are ordered. Start the first `ready` task, preserve the full goal, and update status only after fresh verification.

| ID | Phase | Task | Status | Acceptance Evidence |
|---|---:|---|---|---|
| MW-000 | 0 | Establish truth files, design, implementation plan, Git baseline | done | Files exist, privacy scan passed, initial commit recorded |
| MW-001 | 0/1 | Create installable Python package and tested no-argument guided CLI | done | 2 CLI tests, lint/types/build, and isolated Python 3.12 wheel install smoke passed |
| MW-002 | 1 | Implement versioned evidence/audit models and provenance | done | 6 model tests prove immutable provenance, schema round trip, and absent-evidence language invariant |
| MW-003 | 1 | Implement safe bounded read-command adapter | pending | Unit tests prove no shell, timeout/output bounds, structured failures |
| MW-004 | 1 | Inventory applications from approved roots | pending | Synthetic plist fixtures and read-only macOS smoke |
| MW-005 | 1 | Inventory Homebrew formulae/casks with explicit/dependency distinction | pending | JSON fixture tests and dependency-candidate regression |
| MW-006 | 1 | Inventory internal/external drives | pending | Diskutil plist fixtures and volume classification tests |
| MW-007 | 1 | Produce versioned JSON and Markdown audit reports | pending | Golden/snapshot tests and schema round trip |
| MW-008 | 1 | Complete all Phase 1 commands/help and guided routing | pending | Help contract matrix and CLI behavior tests |
| MW-100 | 2 | Explain/review with usage, startup, related data, and backups | pending | Phase 2 acceptance suite and reports |
| MW-200 | 3 | Role-aware overlap and learning-value intelligence | pending | Required comparison fixture suite |
| MW-300 | 4 | Persistent cleanup plan and exact previews, no actions | pending | Safety/preflight tests prove zero mutation |
| MW-400 | 5 | Approval-gated reversible apply/verify/undo | pending | Isolated filesystem/Homebrew adapter tests and manual safe demo |
| MW-500 | 6 | Bundled Codex skill, setup, and typed read-only integration | pending | Clean-home integration tests and `$macwise` workflow proof |
| MW-600 | 7 | Public docs, privacy/security review, packaging, CI, Homebrew, release candidate | pending | Clean installs, CI, release artifacts, public acceptance audit |
