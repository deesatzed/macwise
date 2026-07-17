"""Read-only Homebrew inventory from machine-readable command output."""

import json
import os
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol, cast

from macwise.models import (
    CollectorState,
    CollectorStatus,
    EntityType,
    Evidence,
    InstallRole,
    Reliability,
    SoftwareRecord,
    stable_software_id,
)
from macwise.system import CommandResult, CommandState, ReadCommand, run_read_command


class HomebrewRunner(Protocol):
    """The narrow command boundary needed by the Homebrew collector."""

    def __call__(
        self,
        command: ReadCommand,
        arguments: Sequence[str] = (),
        /,
    ) -> CommandResult: ...


@dataclass(frozen=True, slots=True)
class HomebrewCollection:
    """Homebrew records and the limitations that qualify them."""

    software: tuple[SoftwareRecord, ...]
    status: CollectorStatus


def _json_object(text: str, label: str, limitations: list[str]) -> dict[str, Any]:
    try:
        loaded: object = json.loads(text)
    except (json.JSONDecodeError, UnicodeError):
        limitations.append(f"Homebrew {label} metadata could not be read.")
        return {}
    if not isinstance(loaded, dict):
        limitations.append(f"Homebrew {label} metadata had an unexpected shape.")
        return {}
    return cast(dict[str, Any], loaded)


def _json_list(text: str, label: str, limitations: list[str]) -> list[Any]:
    try:
        loaded: object = json.loads(text)
    except (json.JSONDecodeError, UnicodeError):
        limitations.append(f"Homebrew {label} metadata could not be read.")
        return []
    if not isinstance(loaded, list):
        limitations.append(f"Homebrew {label} metadata had an unexpected shape.")
        return []
    return cast(list[Any], loaded)


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _mapping(value: object) -> dict[str, Any] | None:
    return cast(dict[str, Any], value) if isinstance(value, dict) else None


def _objects(document: dict[str, Any], key: str, limitations: list[str]) -> list[dict[str, Any]]:
    raw_items: object = document.get(key, [])
    if not isinstance(raw_items, list):
        limitations.append(f"Homebrew {key} metadata had an unexpected shape.")
        return []
    items: list[dict[str, Any]] = []
    for raw_item in cast(list[object], raw_items):
        item = _mapping(raw_item)
        if item is None:
            limitations.append(f"One Homebrew {key} entry had an unexpected shape.")
            continue
        items.append(item)
    return items


def _installed_version(item: dict[str, Any]) -> str | None:
    installed = item.get("installed")
    if isinstance(installed, str):
        return _text(installed)
    if not isinstance(installed, list) or not installed:
        return _text(item.get("version"))
    latest = _mapping(cast(list[object], installed)[-1])
    return _text(latest.get("version")) if latest is not None else None


def _dependencies(item: dict[str, Any]) -> tuple[str, ...]:
    dependencies: list[str] = []
    runtime = item.get("runtime_dependencies", [])
    if isinstance(runtime, list):
        for raw_dependency in cast(list[object], runtime):
            dependency = _mapping(raw_dependency)
            name = _text(dependency.get("full_name")) if dependency is not None else None
            if name is not None:
                dependencies.append(name)
    if not dependencies:
        raw_names = item.get("dependencies", [])
        if isinstance(raw_names, list):
            dependencies.extend(
                name for raw_name in cast(list[object], raw_names) if (name := _text(raw_name))
            )
    return tuple(dict.fromkeys(dependencies))


def _app_artifacts(item: dict[str, Any]) -> tuple[str, ...]:
    applications: list[str] = []
    artifacts = item.get("artifacts", [])
    if not isinstance(artifacts, list):
        return ()
    for raw_artifact in cast(list[object], artifacts):
        artifact = _mapping(raw_artifact)
        if artifact is None or not isinstance(artifact.get("app"), list):
            continue
        applications.extend(
            app for raw_app in cast(list[object], artifact["app"]) if (app := _text(raw_app))
        )
    return tuple(dict.fromkeys(applications))


def _binary_artifacts(item: dict[str, Any]) -> tuple[str, ...]:
    executables: list[str] = []
    artifacts = item.get("artifacts", [])
    if not isinstance(artifacts, list):
        return ()
    for raw_artifact in cast(list[object], artifacts):
        artifact = _mapping(raw_artifact)
        if artifact is None or not isinstance(artifact.get("binary"), list):
            continue
        values = [
            value
            for raw_value in cast(list[object], artifact["binary"])
            if (value := _text(raw_value)) is not None
        ]
        if values:
            executables.append(Path(values[-1]).name)
    return tuple(sorted(dict.fromkeys(executables), key=str.casefold))


def _cask_artifact_kinds(item: dict[str, Any]) -> tuple[str, ...]:
    kinds: set[str] = set()
    artifacts = item.get("artifacts", [])
    if not isinstance(artifacts, list):
        return ("unknown_shape",)
    for raw_artifact in cast(list[object], artifacts):
        artifact = _mapping(raw_artifact)
        if artifact is None:
            kinds.add("unknown_shape")
            continue
        for raw_kind in artifact:
            kind = _text(raw_kind)
            kinds.add(kind if kind is not None else "unknown_shape")
    return tuple(sorted(kinds, key=str.casefold))


def _tree_size(path: Path) -> int:
    total = path.lstat().st_size
    for current_root, directories, files in os.walk(path, followlinks=False):
        root = Path(current_root)
        retained: list[str] = []
        for directory in directories:
            child = root / directory
            total += child.lstat().st_size
            if not child.is_symlink():
                retained.append(directory)
        directories[:] = retained
        for filename in files:
            total += (root / filename).lstat().st_size
    return total


def _formula_executables(path: Path) -> tuple[str, ...]:
    executables: set[str] = set()
    for current_root, directories, files in os.walk(path, followlinks=False):
        root = Path(current_root)
        directories[:] = [name for name in directories if not (root / name).is_symlink()]
        if root.name in {"bin", "sbin"}:
            executables.update(files)
            executables.update(name for name in directories if (root / name).is_symlink())
            directories[:] = []
    return tuple(sorted(executables, key=str.casefold))


def _installation_details(
    root: Path | None,
    name: str,
    limitations: list[str],
    *,
    formula: bool,
) -> tuple[str | None, int | None, tuple[str, ...]]:
    if root is None:
        return None, None, ()
    if Path(name).name != name or name in {".", ".."}:
        limitations.append(f"Homebrew item {name!r} has an unsafe installed path name.")
        return None, None, ()
    candidate = root / name
    if candidate.is_symlink():
        limitations.append(f"Homebrew installed path for {name!r} is a symbolic link.")
        return None, None, ()
    if not candidate.is_dir():
        limitations.append(f"Homebrew installed path for {name!r} is unavailable.")
        return None, None, ()
    try:
        size = _tree_size(candidate)
        executables = _formula_executables(candidate) if formula else ()
    except OSError:
        limitations.append(f"Homebrew installed metadata for {name!r} could not be read.")
        return str(candidate), None, ()
    return str(candidate), size, executables


PROJECT_FILENAMES = {
    ".bash_profile",
    ".bashrc",
    ".tool-versions",
    ".zprofile",
    ".zshrc",
    "Brewfile",
    "Cargo.toml",
    "Gemfile",
    "Pipfile",
    "go.mod",
    "package-lock.json",
    "package.json",
    "pnpm-lock.yaml",
    "pyproject.toml",
    "requirements.txt",
    "yarn.lock",
}
MAX_PROJECT_FILES = 500
MAX_PROJECT_FILE_BYTES = 1_000_000


def _mentions_item(text: str, name: str) -> bool:
    boundary = r"A-Za-z0-9@._+\-"
    return (
        re.search(
            rf"(?<![{boundary}]){re.escape(name)}(?![{boundary}])",
            text,
            flags=re.IGNORECASE,
        )
        is not None
    )


def _project_references(
    names: Sequence[str],
    roots: Sequence[Path],
    limitations: list[str],
) -> dict[str, tuple[str, ...]]:
    references: dict[str, list[str]] = {name: [] for name in names}
    files_seen = 0
    for root in roots:
        if root.is_symlink() or not root.is_dir():
            limitations.append(f"The approved project folder {root} is not available.")
            continue
        for current_root, directories, files in os.walk(root, followlinks=False):
            current = Path(current_root)
            directories[:] = [
                name
                for name in sorted(directories, key=str.casefold)
                if not (current / name).is_symlink()
            ]
            for filename in sorted(files, key=str.casefold):
                if filename not in PROJECT_FILENAMES and not filename.startswith("requirements"):
                    continue
                files_seen += 1
                if files_seen > MAX_PROJECT_FILES:
                    limitations.append(
                        f"Approved project scanning stopped after {MAX_PROJECT_FILES} manifests."
                    )
                    return {
                        name: tuple(sorted(paths, key=str.casefold))
                        for name, paths in references.items()
                    }
                path = current / filename
                try:
                    if path.is_symlink() or path.stat().st_size > MAX_PROJECT_FILE_BYTES:
                        limitations.append(f"Approved project manifest {path} was not read.")
                        continue
                    text = path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    limitations.append(f"Approved project manifest {path} could not be read.")
                    continue
                relative = path.relative_to(root).as_posix()
                for name in names:
                    if _mentions_item(text, name):
                        references[name].append(relative)
    return {
        name: tuple(sorted(dict.fromkeys(paths), key=str.casefold))
        for name, paths in references.items()
    }


def _display_name(item: dict[str, Any], fallback: str) -> str:
    raw_name = item.get("name")
    if isinstance(raw_name, list):
        for candidate in cast(list[object], raw_name):
            if (name := _text(candidate)) is not None:
                return name
    return _text(cast(object, raw_name)) or fallback


def parse_homebrew_inventory(
    *,
    formulae_json: str,
    casks_json: str,
    leaves_text: str,
    services_json: str,
    collected_at: datetime,
    cellar_root: Path | None = None,
    caskroom_root: Path | None = None,
    project_roots: Sequence[Path] = (),
) -> HomebrewCollection:
    """Normalize captured Homebrew metadata without accessing the host."""
    limitations: list[str] = []
    formulae_document = _json_object(formulae_json, "formula", limitations)
    casks_document = _json_object(casks_json, "cask", limitations)
    service_items = _json_list(services_json, "service", limitations)
    leaves = {line.strip() for line in leaves_text.splitlines() if line.strip()}

    service_statuses: dict[str, str] = {}
    for raw_service in service_items:
        service = _mapping(raw_service)
        if service is None:
            limitations.append("One Homebrew service entry had an unexpected shape.")
            continue
        name = _text(service.get("name"))
        status = _text(service.get("status"))
        if name is not None and status is not None:
            service_statuses[name] = status

    formula_items = _objects(formulae_document, "formulae", limitations)
    cask_items = _objects(casks_document, "casks", limitations)
    item_names = [name for item in formula_items if (name := _text(item.get("name"))) is not None]
    item_names.extend(
        token for item in cask_items if (token := _text(item.get("token"))) is not None
    )
    project_reference_map = _project_references(item_names, project_roots, limitations)
    dependency_map: dict[str, tuple[str, ...]] = {}
    for item in formula_items:
        name = _text(item.get("name"))
        if name is not None:
            dependency_map[name] = _dependencies(item)
    reverse_map: dict[str, list[str]] = {name: [] for name in dependency_map}
    for dependent, dependencies in dependency_map.items():
        for dependency in dependencies:
            if dependency in reverse_map:
                reverse_map[dependency].append(dependent)

    records: list[SoftwareRecord] = []
    for item in formula_items:
        name = _text(item.get("name"))
        if name is None:
            limitations.append("One Homebrew formula entry did not contain a name.")
            continue
        explicit = name in leaves
        install_path, size_bytes, executables = _installation_details(
            cellar_root,
            name,
            limitations,
            formula=True,
        )
        linked = _text(item.get("linked_keg")) is not None if "linked_keg" in item else None
        pinned_value = item.get("pinned")
        pinned = pinned_value if isinstance(pinned_value, bool) else None
        records.append(
            SoftwareRecord(
                id=stable_software_id(EntityType.HOMEBREW_FORMULA, name),
                entity_type=EntityType.HOMEBREW_FORMULA,
                name=name,
                display_name=name,
                identifier=name,
                version=_installed_version(item),
                install_path=install_path,
                install_source="homebrew",
                description=_text(item.get("desc")),
                homepage=_text(item.get("homepage")),
                size_bytes=size_bytes,
                executables=executables,
                install_role=InstallRole.EXPLICIT if explicit else InstallRole.DEPENDENCY,
                dependencies=dependency_map.get(name, ()),
                reverse_dependencies=tuple(sorted(reverse_map.get(name, []))),
                service_status=service_statuses.get(name),
                linked=linked,
                pinned=pinned,
                caveats=_text(item.get("caveats")),
                project_references=project_reference_map.get(name, ()),
                evidence=(
                    Evidence(
                        kind="homebrew_formula_metadata",
                        value={
                            "dependencies": list(dependency_map.get(name, ())),
                            "explicit_leaf": explicit,
                            "service_status": service_statuses.get(name),
                            "version": _installed_version(item),
                            "linked": linked,
                            "pinned": pinned,
                            "project_references": list(project_reference_map.get(name, ())),
                        },
                        source="brew info --json=v2 --installed; brew leaves",
                        collected_at=collected_at,
                        reliability=Reliability.HIGH,
                    ),
                ),
            )
        )

    for item in cask_items:
        token = _text(item.get("token"))
        if token is None:
            limitations.append("One Homebrew cask entry did not contain a token.")
            continue
        install_path, size_bytes, _filesystem_executables = _installation_details(
            caskroom_root,
            token,
            limitations,
            formula=False,
        )
        pinned_value = item.get("pinned")
        pinned = pinned_value if isinstance(pinned_value, bool) else None
        records.append(
            SoftwareRecord(
                id=stable_software_id(EntityType.HOMEBREW_CASK, token),
                entity_type=EntityType.HOMEBREW_CASK,
                name=token,
                display_name=_display_name(item, token),
                identifier=token,
                version=_installed_version(item),
                install_path=install_path,
                install_source="homebrew",
                description=_text(item.get("desc")),
                homepage=_text(item.get("homepage")),
                size_bytes=size_bytes,
                executables=_binary_artifacts(item),
                install_role=InstallRole.EXPLICIT,
                app_artifacts=_app_artifacts(item),
                cask_artifact_kinds=_cask_artifact_kinds(item),
                pinned=pinned,
                caveats=_text(item.get("caveats")),
                project_references=project_reference_map.get(token, ()),
                evidence=(
                    Evidence(
                        kind="homebrew_cask_metadata",
                        value={
                            "app_artifacts": list(_app_artifacts(item)),
                            "cask_artifact_kinds": list(_cask_artifact_kinds(item)),
                            "executables": list(_binary_artifacts(item)),
                            "pinned": pinned,
                            "project_references": list(project_reference_map.get(token, ())),
                            "version": _installed_version(item),
                        },
                        source="brew info --json=v2 --installed",
                        collected_at=collected_at,
                        reliability=Reliability.HIGH,
                    ),
                ),
            )
        )

    records.sort(key=lambda record: (record.entity_type.value, record.name.casefold()))
    return HomebrewCollection(
        software=tuple(records),
        status=CollectorStatus(
            collector="homebrew",
            state=CollectorState.COMPLETE if not limitations else CollectorState.PARTIAL,
            collected_at=collected_at,
            records_count=len(records),
            limitations=tuple(limitations),
        ),
    )


def collect_homebrew(
    *,
    collected_at: datetime,
    runner: HomebrewRunner = run_read_command,
    project_roots: Sequence[Path] = (),
) -> HomebrewCollection:
    """Collect installed Homebrew items through fixed, read-only command arguments."""
    info = runner(ReadCommand.BREW, ("info", "--json=v2", "--installed"))
    if info.state is not CommandState.COMPLETE:
        state = (
            CollectorState.UNAVAILABLE
            if info.state is CommandState.UNAVAILABLE
            else CollectorState.PARTIAL
        )
        return HomebrewCollection(
            software=(),
            status=CollectorStatus(
                collector="homebrew",
                state=state,
                collected_at=collected_at,
                records_count=0,
                limitations=info.limitations,
            ),
        )

    leaves = runner(ReadCommand.BREW, ("leaves",))
    services = runner(ReadCommand.BREW, ("services", "list", "--json"))
    prefix = runner(ReadCommand.BREW, ("--prefix",))
    cellar = runner(ReadCommand.BREW, ("--cellar",))
    caskroom = runner(ReadCommand.BREW, ("--caskroom",))
    root_limitations: list[str] = []

    def command_path(result: CommandResult, label: str) -> Path | None:
        if result.state is not CommandState.COMPLETE:
            return None
        value = result.stdout.strip()
        path = Path(value) if value else None
        if path is None or not path.is_absolute():
            root_limitations.append(f"The Homebrew {label} path metadata could not be read.")
            return None
        return path

    prefix_path = command_path(prefix, "prefix")
    cellar_path = command_path(cellar, "Cellar")
    caskroom_path = command_path(caskroom, "Caskroom")
    if prefix_path is not None:
        if cellar_path is not None and not cellar_path.is_relative_to(prefix_path):
            root_limitations.append("The Homebrew Cellar path is outside the reported prefix.")
            cellar_path = None
        if caskroom_path is not None and not caskroom_path.is_relative_to(prefix_path):
            root_limitations.append("The Homebrew Caskroom path is outside the reported prefix.")
            caskroom_path = None

    result = parse_homebrew_inventory(
        formulae_json=info.stdout,
        casks_json=info.stdout,
        leaves_text=leaves.stdout if leaves.state is CommandState.COMPLETE else "",
        services_json=services.stdout if services.state is CommandState.COMPLETE else "[]",
        collected_at=collected_at,
        cellar_root=cellar_path,
        caskroom_root=caskroom_path,
        project_roots=project_roots,
    )
    command_limitations = (
        *info.limitations,
        *leaves.limitations,
        *services.limitations,
        *prefix.limitations,
        *cellar.limitations,
        *caskroom.limitations,
        *root_limitations,
    )
    if not command_limitations:
        return result
    return HomebrewCollection(
        software=result.software,
        status=result.status.model_copy(
            update={
                "state": CollectorState.PARTIAL,
                "limitations": (*result.status.limitations, *command_limitations),
            }
        ),
    )
