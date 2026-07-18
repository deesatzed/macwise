"""Centralized novice-friendly help for every public MacWise command."""


def _help(
    summary: str,
    useful_when: str,
    safety: str,
    examples: tuple[str, ...],
    next_steps: tuple[str, ...],
) -> str:
    example_lines = "\n".join(f"  {example}" for example in examples)
    next_lines = "\n".join(f"  {step}" for step in next_steps)
    return f"""{summary}

Useful when: {useful_when}

{safety}

Examples:
{example_lines}

Next:
{next_lines}
"""


READ_ONLY = "This command is read-only and does not remove or change anything."
AUDIT_FILE = (
    "Scanning is read-only and does not change installed software. A file is written only when "
    "you explicitly use --output."
)
PLAN_STATE = (
    "This command writes only local MacWise planning state when an item is added; it does "
    "not change installed software or user data."
)
PLAN_ADD_STATE = (
    "This command writes only local MacWise planning state; it does not change installed "
    "software or user data."
)

HELP: dict[str, str] = {
    "root": _help(
        "Understand the software installed on this Mac and decide what deserves attention.",
        "you want guidance and do not know which MacWise command to choose.",
        "Running the guided menu does not remove or change anything.",
        ("macwise", "macwise scan", "macwise review apps"),
        ("Run macwise scan for a read-only inventory.", "Run macwise help to see all commands."),
    ),
    "scan": _help(
        "Creates a read-only inventory of applications, Homebrew software, and storage volumes.",
        "you want a fresh overview or a JSON or Markdown audit to review later.",
        AUDIT_FILE,
        (
            "macwise scan",
            "macwise scan --format json",
            "macwise scan --format markdown --output audit.md",
        ),
        ("Run macwise review apps.", "Run macwise storage."),
    ),
    "review": _help(
        "Groups installed software into simple views so you can review one question at a time.",
        "the full scan is too broad and you want apps, Homebrew, storage, or uncertainty views.",
        READ_ONLY,
        ("macwise review apps", "macwise review brew", "macwise review largest"),
        ("Run macwise explain NAME.", "Run macwise plan after reviewing an item."),
    ),
    "review_apps": _help(
        "Lists application bundles MacWise found in approved application folders.",
        "you want to see app names, versions, locations, sizes, and internal or external storage.",
        READ_ONLY,
        ("macwise review apps", 'macwise explain "Example App"'),
        ("Run macwise review largest.", "Run macwise explain NAME."),
    ),
    "review_brew": _help(
        "Lists Homebrew formulae and casks while separating selected tools from dependencies.",
        "you want to understand command-line software without treating libraries as chosen apps.",
        READ_ONLY,
        ("macwise review brew", "macwise explain formula:openssl@3"),
        ("Run macwise startup.", "Run macwise explain NAME."),
    ),
    "review_startup": _help(
        "Shows the startup evidence MacWise can currently verify and states what remains unknown.",
        "you want to know which installed tools may run in the background.",
        READ_ONLY,
        ("macwise review startup", "macwise startup"),
        ("Run macwise explain NAME.", "Run macwise scan."),
    ),
    "review_duplicates": _help(
        "Groups explicit role-aware overlap candidates and distinguishes duplicates, substitutes, complements, dependencies, and successors.",
        "you want to consolidate software with similar roles.",
        READ_ONLY,
        ("macwise review duplicates", "macwise compare Docker Podman"),
        ("Run macwise compare NAME NAME.", "Run macwise scan."),
    ),
    "review_largest": _help(
        "Lists the largest measured application bundles and says when related data is still unknown.",
        "you want to find measured software space without overstating reclaimable storage.",
        READ_ONLY,
        ("macwise review largest", "macwise storage"),
        ("Run macwise explain NAME.", "Run macwise plan."),
    ),
    "review_unused": _help(
        "Lists only possibly-unused or user-confirmed-unused findings and shows the evidence and limitations behind each label.",
        "you want to find possibly unused tools without unsafe assumptions.",
        READ_ONLY,
        ("macwise review unused", "macwise explain NAME"),
        ("Run macwise review unknown.", "Run macwise scan."),
    ),
    "review_unknown": _help(
        "Lists installed records whose purpose or other important metadata is still unknown.",
        "you want to focus research on ambiguous software rather than search for everything.",
        READ_ONLY,
        ("macwise review unknown", "macwise explain NAME"),
        ("Run macwise explain NAME.", "Run macwise scan --format markdown."),
    ),
    "explain": _help(
        "Explains one installed item's facts, usage, startup, related data, catalog roles, overlaps, learning value, and guarded guidance.",
        "you see an unfamiliar app or Homebrew tool and want a cautious first explanation.",
        READ_ONLY,
        ("macwise explain Raycast", "macwise explain ollama", "macwise explain formula:openssl@3"),
        ("Run macwise compare NAME NAME.", "Run macwise plan."),
    ),
    "compare": _help(
        "Compares two or more installed items by explicit roles, overlap category, actual-use evidence, unique capabilities, and learning value.",
        "you want to understand whether installed tools substitute for or complement each other.",
        READ_ONLY,
        ("macwise compare Docker Podman", "macwise compare Raycast Hammerspoon"),
        ("Run macwise review duplicates.", "Run macwise explain NAME."),
    ),
    "startup": _help(
        "Shows collected launch and Homebrew startup items, conservative owners, and enabled/running unknowns.",
        "you want a cautious view of software that may run in the background.",
        READ_ONLY,
        ("macwise startup", "macwise review startup"),
        ("Run macwise explain NAME.", "Run macwise scan."),
    ),
    "storage": _help(
        "Shows internal and external volumes, free space, and verified application bundle locations.",
        "you want to know which drive holds software and which drive could regain measured space.",
        READ_ONLY,
        ("macwise storage", "macwise review largest"),
        ("Run macwise review largest.", "Run macwise backups."),
    ),
    "backups": _help(
        "Reports only backup facts MacWise can verify and refuses to equate configuration with coverage.",
        "you want to understand backup limitations before planning cleanup.",
        READ_ONLY,
        ("macwise backups", "macwise plan"),
        ("Run macwise storage.", "Run macwise plan after backup evidence is available."),
    ),
    "plan": _help(
        "Builds and previews an immutable cleanup plan with explicit safety checks.",
        "you have reviewed software and want an exact, non-destructive preview.",
        PLAN_STATE,
        ("macwise plan", "macwise plan show", 'macwise plan add "Example.app"'),
        ("Run macwise plan add NAME.", "Run macwise explain NAME."),
    ),
    "plan_add": _help(
        "Adds one exact reviewed item to a saved cleanup preview and runs planning preflight.",
        "you have inspected an item and want to consider it without changing the Mac.",
        PLAN_ADD_STATE,
        ('macwise plan add "Example.app"', "macwise plan show"),
        ("Run macwise plan show.", "Run macwise explain NAME."),
    ),
    "plan_show": _help(
        "Shows the exact cleanup preview and unresolved safety checks without applying it.",
        "you want to review every proposed change before approval.",
        READ_ONLY,
        ("macwise plan show", "macwise plan"),
        ("Resolve every warning before macwise apply.", "Run macwise scan."),
    ),
    "apply": _help(
        "Freshly revalidates and applies an explicitly reviewed schema-2 cleanup plan after exact approval.",
        "you have reviewed every ordered action, warning, and inverse and are ready for action-time confirmation.",
        "This command can change installed software and startup state. It requires an exact approval fingerprint, does not elevate privileges, preserves related user data, journals before mutation, verifies afterward, and stops on the first failure.",
        ("macwise plan show", "macwise apply", "macwise apply --approve 'APPLY FINGERPRINT'"),
        ("Review fresh revalidation output.", "Run macwise undo to inspect recovery."),
    ),
    "undo": _help(
        "Reviews and reverses the latest fully verified MacWise execution in reverse order after separate exact approval.",
        "you need to restore a previously verified MacWise action from its append-only recovery manifest.",
        "This command can restore installed software and startup state without elevation. Trash restoration is exact; Homebrew reinstall is best-effort and may not restore the captured version.",
        ("macwise undo", "macwise undo --approve 'UNDO FINGERPRINT'", "macwise doctor"),
        ("Review every inverse before approval.", "Run macwise scan after verified undo."),
    ),
    "doctor": _help(
        "Checks whether this Mac can run MacWise collectors and reports missing optional tools.",
        "a scan failed or you want to verify local prerequisites.",
        READ_ONLY,
        ("macwise doctor", "macwise scan"),
        ("Run macwise scan.", "Use the reported recovery hint for any missing tool."),
    ),
    "setup": _help(
        "Configures optional integrations without making them part of the standalone CLI requirement.",
        "you want to connect MacWise to a supported conversational tool.",
        "Setup changes only MacWise-owned user integration files and refuses unsafe or conflicting paths.",
        ("macwise setup codex", "macwise doctor"),
        ("Run macwise setup codex.", "Run macwise scan first."),
    ),
    "setup_codex": _help(
        "Installs or updates the bundled read-only MacWise Codex experience for this user.",
        "you want to type $macwise inside Codex and review local audit evidence conversationally.",
        "Setup changes only MacWise-owned plugin files and its personal plugin entry; Codex tools cannot apply or undo cleanup.",
        ("macwise setup codex", "macwise doctor"),
        (
            "Start a new Codex session and type $macwise.",
            "Run macwise doctor if setup reports a prerequisite problem.",
        ),
    ),
    "help": _help(
        "Shows the guided MacWise command overview and points to detailed command help.",
        "you are unsure what to run next or want to rediscover the small command hierarchy.",
        READ_ONLY,
        ("macwise help", "macwise scan --help"),
        ("Run macwise.", "Run macwise scan."),
    ),
}
