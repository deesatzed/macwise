"""Versioned, offline, exact-match software role catalog."""

from dataclasses import dataclass

from macwise.models import EntityType, LearningValue, OverlapCategory, Reliability, SoftwareRecord

CATALOG_VERSION = "2026.07"
CATALOG_SOURCE = "MacWise bundled role catalog"


@dataclass(frozen=True, slots=True)
class CatalogMatcher:
    """Entity-qualified exact values that may identify one catalog entry."""

    entity_type: EntityType
    names: tuple[str, ...] = ()
    identifiers: tuple[str, ...] = ()
    executables: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    """Coarse public product roles and learning context."""

    key: str
    family: str
    matchers: tuple[CatalogMatcher, ...]
    roles: tuple[str, ...]
    capabilities: tuple[str, ...]
    unique_capabilities: tuple[str, ...]
    learning_value: LearningValue
    learning_statement: str


@dataclass(frozen=True, slots=True)
class CatalogRelation:
    """An explicit relationship between two catalog entries."""

    left_key: str
    right_key: str
    category: OverlapCategory
    statement: str
    shared_capabilities: tuple[str, ...] = ()
    left_unique_capabilities: tuple[str, ...] = ()
    right_unique_capabilities: tuple[str, ...] = ()
    confidence: Reliability = Reliability.MEDIUM
    limitations: tuple[str, ...] = (
        "Catalog roles do not prove that two tools are interchangeable for local projects.",
    )


@dataclass(frozen=True, slots=True)
class CatalogMatch:
    """One unique catalog match or sanitized metadata about an ambiguous tie."""

    entry: CatalogEntry | None
    ambiguous_keys: tuple[str, ...] = ()


def _app(
    *names: str,
    identifiers: tuple[str, ...] = (),
    executables: tuple[str, ...] = (),
) -> CatalogMatcher:
    return CatalogMatcher(EntityType.APPLICATION, names, identifiers, executables)


def _cask(*names: str) -> CatalogMatcher:
    return CatalogMatcher(EntityType.HOMEBREW_CASK, names)


def _formula(*names: str, executables: tuple[str, ...] = ()) -> CatalogMatcher:
    return CatalogMatcher(EntityType.HOMEBREW_FORMULA, names, executables=executables)


CATALOG: tuple[CatalogEntry, ...] = (
    CatalogEntry(
        "docker-desktop",
        "containers",
        (_app("Docker", "Docker Desktop", identifiers=("com.docker.docker",)), _cask("docker")),
        ("container desktop", "container runtime bundle"),
        ("containers", "images", "compose workflows"),
        ("integrated desktop controls",),
        LearningValue.MODERATE,
        "Useful for learning an integrated local container workflow.",
    ),
    CatalogEntry(
        "docker-cli",
        "containers",
        (_formula("docker", executables=("docker",)),),
        ("container command-line client",),
        ("container client commands",),
        ("scriptable command-line interface",),
        LearningValue.HIGH,
        "Useful for learning portable container command-line concepts.",
    ),
    CatalogEntry(
        "docker-compose",
        "containers",
        (_formula("docker-compose", "docker-compose@2", executables=("docker-compose",)),),
        ("multi-container workflow tool",),
        ("compose workflows",),
        ("declarative multi-service configuration",),
        LearningValue.MODERATE,
        "Useful when projects define multi-service container environments.",
    ),
    CatalogEntry(
        "podman",
        "containers",
        (
            _app("Podman Desktop", identifiers=("io.podman_desktop.PodmanDesktop",)),
            _cask("podman-desktop"),
            _formula("podman", executables=("podman",)),
        ),
        ("container engine", "container desktop"),
        ("containers", "images"),
        ("daemonless container workflow",),
        LearningValue.MODERATE,
        "Useful for learning an alternative standards-oriented container workflow.",
    ),
    CatalogEntry(
        "ollama",
        "local_ai",
        (
            _app("Ollama", identifiers=("com.electron.ollama",)),
            _cask("ollama"),
            _formula("ollama", executables=("ollama",)),
        ),
        ("local model runtime",),
        ("local model serving", "model management"),
        ("simple local model command workflow",),
        LearningValue.HIGH,
        "Useful for learning local model serving and model lifecycle concepts.",
    ),
    CatalogEntry(
        "lm-studio",
        "local_ai",
        (_app("LM Studio", identifiers=("ai.elementlabs.lmstudio",)), _cask("lm-studio")),
        ("local model desktop", "model frontend"),
        ("local model serving", "model management"),
        ("graphical model discovery and controls",),
        LearningValue.MODERATE,
        "Useful for learning local models through a graphical workflow.",
    ),
    CatalogEntry(
        "omlx",
        "local_ai",
        (_app("oMLX"), _cask("omlx"), _formula("omlx", executables=("omlx",))),
        ("MLX model frontend",),
        ("local model serving", "MLX workflows"),
        ("MLX-focused interface",),
        LearningValue.MODERATE,
        "Useful when exploring MLX-focused model workflows on Apple silicon.",
    ),
    CatalogEntry(
        "llama-cpp",
        "local_ai",
        (_formula("llama.cpp", "llama-cpp", executables=("llama-cli", "llama-server")),),
        ("local model runtime",),
        ("local model inference", "local model serving"),
        ("low-level portable runtime controls",),
        LearningValue.HIGH,
        "Useful for understanding lower-level local inference controls.",
    ),
    CatalogEntry(
        "mlx",
        "local_ai",
        (_formula("mlx", executables=("mlx",)),),
        ("machine-learning runtime library",),
        ("MLX workflows",),
        ("programmatic Apple-silicon model primitives",),
        LearningValue.HIGH,
        "Useful for programmatic machine-learning work on Apple silicon.",
    ),
    CatalogEntry(
        "obsidian",
        "markdown",
        (_app("Obsidian", identifiers=("md.obsidian",)), _cask("obsidian")),
        ("Markdown knowledge-base application",),
        ("Markdown editing", "linked notes"),
        ("vault plugins and linked-note workflows",),
        LearningValue.HIGH,
        "Useful for learning linked-note and knowledge-base workflows.",
    ),
    CatalogEntry(
        "zettlr",
        "markdown",
        (_app("Zettlr", identifiers=("com.zettlr.app",)), _cask("zettlr")),
        ("Markdown writing application",),
        ("Markdown editing", "document organization"),
        ("academic writing workflow",),
        LearningValue.MODERATE,
        "Useful for structured Markdown writing and document organization.",
    ),
    CatalogEntry(
        "mark-text",
        "markdown",
        (_app("Mark Text", identifiers=("com.marktext.marktext",)), _cask("mark-text")),
        ("Markdown editor",),
        ("Markdown editing",),
        ("focused visual Markdown editing",),
        LearningValue.LOW,
        "Useful when a focused visual Markdown editor fits the writing workflow.",
    ),
    CatalogEntry(
        "markdown-preview",
        "markdown",
        (_app("Markdown Preview"), _cask("markdown-preview")),
        ("Markdown preview tool",),
        ("Markdown preview",),
        ("standalone rendered preview",),
        LearningValue.LOW,
        "Useful when a separate rendered preview is needed.",
    ),
    CatalogEntry(
        "qlmarkdown",
        "markdown",
        (_app("QLMarkdown"), _cask("qlmarkdown")),
        ("Quick Look Markdown extension",),
        ("Markdown preview",),
        ("Finder Quick Look integration",),
        LearningValue.LOW,
        "Useful for previewing Markdown directly from Finder.",
    ),
    CatalogEntry(
        "raycast",
        "launcher_automation",
        (_app("Raycast", identifiers=("com.raycast.macos",)), _cask("raycast")),
        ("application launcher", "automation frontend"),
        ("application launching", "search", "automation"),
        ("extensions and command workflows",),
        LearningValue.HIGH,
        "Useful for learning launcher extensions and command workflows.",
    ),
    CatalogEntry(
        "spotlight",
        "launcher_automation",
        (_app("Spotlight", identifiers=("com.apple.Spotlight",)),),
        ("system search and launcher",),
        ("application launching", "search"),
        ("system-integrated content indexing",),
        LearningValue.MODERATE,
        "Useful for learning built-in search and launcher shortcuts.",
    ),
    CatalogEntry(
        "hammerspoon",
        "launcher_automation",
        (_app("Hammerspoon", identifiers=("org.hammerspoon.Hammerspoon",)), _cask("hammerspoon")),
        ("programmable macOS automation",),
        ("automation", "window management"),
        ("scriptable system automation",),
        LearningValue.HIGH,
        "Useful for learning programmable macOS automation.",
    ),
    CatalogEntry(
        "alttab",
        "launcher_automation",
        (_app("AltTab", identifiers=("com.lwouis.alt-tab-macos",)), _cask("alt-tab")),
        ("window switcher",),
        ("window management", "window switching"),
        ("visual application-window switching",),
        LearningValue.LOW,
        "Useful when a visual window-switching workflow is desired.",
    ),
    CatalogEntry(
        "magnet",
        "launcher_automation",
        (_app("Magnet", identifiers=("com.crowdcafe.windowmagnet",)), _cask("magnet")),
        ("window layout tool",),
        ("window management",),
        ("preset window snapping",),
        LearningValue.LOW,
        "Useful for learning consistent window-layout shortcuts.",
    ),
    CatalogEntry(
        "homebrew-python",
        "python",
        (_formula("python", "python@3.12", "python@3.13", executables=("python3",)),),
        ("Python runtime",),
        ("Python execution", "package environments"),
        ("Homebrew-managed system-wide runtime",),
        LearningValue.HIGH,
        "Useful for learning the Python runtime and environment model.",
    ),
    CatalogEntry(
        "homebrew-python-legacy",
        "python",
        (_formula("python@3.10", "python@3.11", executables=("python3",)),),
        ("older Python runtime",),
        ("Python execution", "package environments"),
        ("compatibility with older projects",),
        LearningValue.LOW,
        "Useful only when an existing project requires that runtime line.",
    ),
    CatalogEntry(
        "pyenv",
        "python",
        (_formula("pyenv", executables=("pyenv",)),),
        ("Python version manager",),
        ("Python version selection", "project runtimes"),
        ("per-project runtime switching",),
        LearningValue.HIGH,
        "Useful for learning reproducible per-project Python versions.",
    ),
    CatalogEntry(
        "anaconda",
        "python",
        (_app("Anaconda Navigator"), _cask("anaconda", "anaconda-distribution")),
        ("Python distribution", "environment frontend"),
        ("Python execution", "package environments"),
        ("bundled scientific packages and graphical environment controls",),
        LearningValue.MODERATE,
        "Useful for learning a bundled scientific Python workflow.",
    ),
    CatalogEntry(
        "virtualenv",
        "python",
        (_formula("virtualenv", executables=("virtualenv",)),),
        ("Python environment tool",),
        ("package environments",),
        ("isolated project environments",),
        LearningValue.HIGH,
        "Useful for learning isolated Python project environments.",
    ),
    CatalogEntry(
        "kindle",
        "reading",
        (_app("Amazon Kindle", "Kindle"),),
        ("ebook reader",),
        ("ebook reading", "Kindle library access"),
        ("Amazon Kindle ecosystem integration",),
        LearningValue.LOW,
        "Useful for reading and organizing books from a Kindle library.",
    ),
    CatalogEntry(
        "chatgpt",
        "ai_assistants",
        (_app("ChatGPT", "ChatGPT Classic"),),
        ("AI assistant application",),
        ("conversational assistance", "document and media workflows"),
        ("OpenAI account and model integration",),
        LearningValue.MODERATE,
        "Useful for learning conversational AI-assisted workflows.",
    ),
    CatalogEntry(
        "claude",
        "ai_assistants",
        (_app("Claude"),),
        ("AI assistant application",),
        ("conversational assistance", "document workflows"),
        ("Anthropic account and model integration",),
        LearningValue.MODERATE,
        "Useful for learning conversational AI-assisted workflows.",
    ),
    CatalogEntry(
        "visual-studio-code",
        "development",
        (_app("Code", "Visual Studio Code", identifiers=("com.microsoft.VSCode",)),),
        ("code editor", "development environment"),
        ("source editing", "extensions", "debugging"),
        ("Visual Studio Code extension ecosystem",),
        LearningValue.HIGH,
        "Useful for learning extensible software-development workflows.",
    ),
    CatalogEntry(
        "calibre",
        "reading",
        (_app("calibre"),),
        ("ebook library manager",),
        ("ebook organization", "format conversion", "device transfer"),
        ("local cross-format ebook management",),
        LearningValue.MODERATE,
        "Useful for organizing and converting a local ebook library.",
    ),
)


RELATIONS: tuple[CatalogRelation, ...] = (
    CatalogRelation(
        "docker-desktop",
        "podman",
        OverlapCategory.STRONG_SUBSTITUTE,
        "Both support local container and image workflows.",
        ("containers", "images"),
        ("integrated desktop controls",),
        ("daemonless container workflow",),
    ),
    CatalogRelation(
        "raycast",
        "alttab",
        OverlapCategory.PARTIAL_OVERLAP,
        "Both can participate in switching workflows, but their broader roles differ.",
        ("window switching",),
        ("extensions and command workflows",),
        ("visual application-window switching",),
    ),
    CatalogRelation(
        "obsidian",
        "qlmarkdown",
        OverlapCategory.COMPLEMENTARY_TOOLS,
        "One manages Markdown knowledge while the other adds Finder previews.",
        ("Markdown preview",),
        ("vault plugins and linked-note workflows",),
        ("Finder Quick Look integration",),
    ),
    CatalogRelation(
        "lm-studio",
        "llama-cpp",
        OverlapCategory.RUNTIME_AND_FRONTEND,
        "A graphical local-model workflow can sit above lower-level runtime concepts.",
        ("local model serving",),
        ("graphical model discovery and controls",),
        ("low-level portable runtime controls",),
    ),
    CatalogRelation(
        "mlx",
        "omlx",
        OverlapCategory.DEPENDENCY_AND_USER_FACING_APP,
        "A user-facing MLX workflow can rely on lower-level MLX runtime capabilities.",
        ("MLX workflows",),
        ("programmatic Apple-silicon model primitives",),
        ("MLX-focused interface",),
    ),
    CatalogRelation(
        "homebrew-python-legacy",
        "homebrew-python",
        OverlapCategory.LEGACY_AND_SUCCESSOR,
        "Both are Python runtime lines; the older line may remain for project compatibility.",
        ("Python execution", "package environments"),
        ("compatibility with older projects",),
        ("current Homebrew runtime line",),
    ),
    CatalogRelation(
        "docker-cli",
        "obsidian",
        OverlapCategory.NOT_ACTUALLY_RELATED,
        "A container command-line client and a Markdown knowledge-base app serve different roles.",
        (),
        ("scriptable command-line interface",),
        ("vault plugins and linked-note workflows",),
        Reliability.HIGH,
    ),
)


def _normalized(values: tuple[str, ...]) -> set[str]:
    return {value.strip().casefold() for value in values if value.strip()}


def _match_score(record: SoftwareRecord, matcher: CatalogMatcher) -> int:
    if record.entity_type is not matcher.entity_type:
        return 0
    if record.identifier and record.identifier.casefold() in _normalized(matcher.identifiers):
        return 3
    record_names = {record.name.casefold(), record.display_name.casefold()}
    if record_names & _normalized(matcher.names):
        return 2
    if _normalized(record.executables) & _normalized(matcher.executables):
        return 1
    return 0


def catalog_match(record: SoftwareRecord) -> CatalogMatch:
    """Return a typed exact-match outcome without resolving tied catalog roles."""
    scored = [
        (max((_match_score(record, matcher) for matcher in entry.matchers), default=0), entry)
        for entry in CATALOG
    ]
    best_score = max((score for score, _ in scored), default=0)
    if best_score == 0:
        return CatalogMatch(entry=None)
    best = [entry for score, entry in scored if score == best_score]
    if len(best) == 1:
        return CatalogMatch(entry=best[0])
    return CatalogMatch(entry=None, ambiguous_keys=tuple(sorted(entry.key for entry in best)))


def match_catalog_entry(record: SoftwareRecord) -> CatalogEntry | None:
    """Return one highest-priority exact match; ambiguity remains unknown."""
    return catalog_match(record).entry
