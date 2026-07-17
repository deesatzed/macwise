"""Read-only Homebrew inventory from machine-readable command output."""

import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
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
        records.append(
            SoftwareRecord(
                id=stable_software_id(EntityType.HOMEBREW_FORMULA, name),
                entity_type=EntityType.HOMEBREW_FORMULA,
                name=name,
                display_name=name,
                identifier=name,
                version=_installed_version(item),
                install_source="homebrew",
                description=_text(item.get("desc")),
                homepage=_text(item.get("homepage")),
                install_role=InstallRole.EXPLICIT if explicit else InstallRole.DEPENDENCY,
                dependencies=dependency_map.get(name, ()),
                reverse_dependencies=tuple(sorted(reverse_map.get(name, []))),
                service_status=service_statuses.get(name),
                evidence=(
                    Evidence(
                        kind="homebrew_formula_metadata",
                        value={
                            "dependencies": list(dependency_map.get(name, ())),
                            "explicit_leaf": explicit,
                            "service_status": service_statuses.get(name),
                            "version": _installed_version(item),
                        },
                        source="brew info --json=v2 --installed; brew leaves",
                        collected_at=collected_at,
                        reliability=Reliability.HIGH,
                    ),
                ),
            )
        )

    for item in _objects(casks_document, "casks", limitations):
        token = _text(item.get("token"))
        if token is None:
            limitations.append("One Homebrew cask entry did not contain a token.")
            continue
        records.append(
            SoftwareRecord(
                id=stable_software_id(EntityType.HOMEBREW_CASK, token),
                entity_type=EntityType.HOMEBREW_CASK,
                name=token,
                display_name=_display_name(item, token),
                identifier=token,
                version=_installed_version(item),
                install_source="homebrew",
                description=_text(item.get("desc")),
                homepage=_text(item.get("homepage")),
                install_role=InstallRole.EXPLICIT,
                app_artifacts=_app_artifacts(item),
                evidence=(
                    Evidence(
                        kind="homebrew_cask_metadata",
                        value={
                            "app_artifacts": list(_app_artifacts(item)),
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
    result = parse_homebrew_inventory(
        formulae_json=info.stdout,
        casks_json=info.stdout,
        leaves_text=leaves.stdout if leaves.state is CommandState.COMPLETE else "",
        services_json=services.stdout if services.state is CommandState.COMPLETE else "[]",
        collected_at=collected_at,
    )
    command_limitations = (*info.limitations, *leaves.limitations, *services.limitations)
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
