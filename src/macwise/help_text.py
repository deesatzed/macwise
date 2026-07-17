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
        "Explains the current status of overlap analysis without guessing that related tools duplicate each other.",
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
        "Explains why reliable unused-software conclusions require more evidence than a missing date.",
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
        "Explains verified identity and installation facts for one installed item and labels missing evidence.",
        "you see an unfamiliar app or Homebrew tool and want a cautious first explanation.",
        READ_ONLY,
        ("macwise explain Raycast", "macwise explain ollama", "macwise explain formula:openssl@3"),
        ("Run macwise compare NAME NAME.", "Run macwise plan."),
    ),
    "compare": _help(
        "Compares named software only when role-aware overlap evidence is available.",
        "you want to understand whether installed tools substitute for or complement each other.",
        READ_ONLY,
        ("macwise compare Docker Podman", "macwise compare Raycast Hammerspoon"),
        ("Run macwise review duplicates.", "Run macwise explain NAME."),
    ),
    "startup": _help(
        "Shows verified Homebrew service activity and clearly marks other startup sources not yet assessed.",
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
        "Builds and previews a cleanup plan only after planning safety checks are available.",
        "you have reviewed software and want an exact, non-destructive preview.",
        READ_ONLY,
        ("macwise plan", "macwise plan show", 'macwise plan add "Example.app"'),
        ("Run macwise scan.", "Run macwise explain NAME."),
    ),
    "plan_add": _help(
        "Adds one unambiguous reviewed item to a future cleanup preview.",
        "you have inspected an item and want to consider it without changing the Mac.",
        READ_ONLY,
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
        "Applies an explicitly reviewed cleanup plan only when reversible execution is available.",
        "you have approved a complete plan and are ready for action-time confirmation.",
        "This command can change installed software, but the current release refuses to act because reversible execution is not available yet.",
        ("macwise plan show", "macwise apply"),
        ("Run macwise plan show.", "Resolve every safety warning first."),
    ),
    "undo": _help(
        "Restores a reversible MacWise action from its rollback manifest when that capability is available.",
        "you need to reverse a previously verified MacWise action.",
        "This command can restore installed software, but the current release refuses because no action manifests can exist yet.",
        ("macwise undo", "macwise doctor"),
        ("Run macwise doctor.", "Review the original action manifest."),
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
        "Setup is not read-only because it can change local integration configuration; unavailable setup targets refuse safely.",
        ("macwise setup codex", "macwise doctor"),
        ("Run macwise setup codex.", "Run macwise scan first."),
    ),
    "setup_codex": _help(
        "Installs the bundled MacWise Codex experience when the integration package is ready.",
        "you want to type $macwise inside Codex and review local audit evidence conversationally.",
        "Setup is not read-only because it can change local Codex configuration; this build refuses safely because integration is not ready.",
        ("macwise setup codex", "macwise doctor"),
        ("Run macwise scan.", "Retry setup after the Codex integration phase is installed."),
    ),
    "help": _help(
        "Shows the guided MacWise command overview and points to detailed command help.",
        "you are unsure what to run next or want to rediscover the small command hierarchy.",
        READ_ONLY,
        ("macwise help", "macwise scan --help"),
        ("Run macwise.", "Run macwise scan."),
    ),
}
