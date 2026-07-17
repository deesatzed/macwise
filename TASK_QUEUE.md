# TASK_QUEUE.md

Tasks are ordered. Start the first `ready` task, preserve the full goal, and update status only after fresh verification.

| ID | Phase | Task | Status | Acceptance Evidence |
|---|---:|---|---|---|
| MW-000 | 0 | Establish truth files, design, implementation plan, Git baseline | done | Files exist, privacy scan passed, initial commit recorded |
| MW-001 | 0/1 | Create installable Python package and tested no-argument guided CLI | done | 2 CLI tests, lint/types/build, and isolated Python 3.12 wheel install smoke passed |
| MW-002 | 1 | Implement versioned evidence/audit models and provenance | done | 6 model tests prove immutable provenance, schema round trip, and absent-evidence language invariant |
| MW-003 | 1 | Implement safe bounded read-command adapter | done | 6 tests prove fixed executables, inert args/no shell, bounded env/time/output, and structured failures |
| MW-004 | 1 | Inventory applications from approved roots | done | 6 synthetic bundle tests cover metadata/size/location, partial failures, recursion, no execution, and no symlink following |
| MW-005 | 1 | Inventory Homebrew formulae/casks with explicit/dependency distinction | done | 5 fixture/command tests cover metadata, services, cask mapping, unavailable/partial states, and dependency-candidate regression |
| MW-006 | 1 | Inventory internal/external drives | done | 5 plist/command tests cover capacity/security/location, unmounted/unavailable volumes, and guarded path resolution; real read-only smoke completed |
| MW-007 | 1 | Produce versioned JSON and Markdown audit reports | done | 5 service/report tests prove partial aggregation, stable ordering, versioned JSON round trip, stable Markdown, limitations, and unknown-language invariants |
| MW-008 | 1 | Complete all Phase 1 commands/help and guided routing | done | 36 CLI tests cover 24 help surfaces, required hierarchy, guided/noninteractive routing, formats, explicit output safeguards, and later-phase refusal paths |
| MW-009 | 1 | Close application, Homebrew, and drive inventory field gaps | done | 94-test gate plus real read-only smokes cover schema migration, signing/architecture/running/helpers, approved roots, Brew sizes/executables/project refs/linked state/location/correlation, and physical/APFS/ownership/Time Machine fields |
| MW-010 | 1 | Add malicious metadata and cross-parser/rendering security fixtures | done | 98-test gate plus hostile plist/Homebrew/disk/prompt fixtures prove containment, raw JSON preservation, Markdown/terminal neutralization, inert CLI matching, and the future prompt boundary |
| MW-011 | 1 | Re-run Phase 1 requirement and clean-platform acceptance | ready | Updated acceptance matrix, fresh complete gate, macOS/Linux CI, clean wheel/pipx smoke |
| MW-100 | 2 | Explain/review with usage, startup, related data, and backups | pending | Phase 2 acceptance suite and reports |
| MW-200 | 3 | Role-aware overlap and learning-value intelligence | pending | Required comparison fixture suite |
| MW-300 | 4 | Persistent cleanup plan and exact previews, no actions | pending | Safety/preflight tests prove zero mutation |
| MW-400 | 5 | Approval-gated reversible apply/verify/undo | pending | Isolated filesystem/Homebrew adapter tests and manual safe demo |
| MW-500 | 6 | Bundled Codex skill, setup, and typed read-only integration | pending | Clean-home integration tests and `$macwise` workflow proof |
| MW-600 | 7 | Public docs, privacy/security review, packaging, CI, Homebrew, release candidate | pending | Clean installs, CI, release artifacts, public acceptance audit |
