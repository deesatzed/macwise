"""Read-only evidence collectors."""

from macwise.collectors.applications import (
    ApplicationCollection,
    collect_applications,
    collect_host_applications,
)
from macwise.collectors.homebrew import (
    HomebrewCollection,
    collect_homebrew,
    parse_homebrew_inventory,
)
from macwise.collectors.storage import (
    StorageCollection,
    collect_storage,
    parse_volume_info,
    resolve_storage_location,
)

__all__ = [
    "ApplicationCollection",
    "HomebrewCollection",
    "StorageCollection",
    "collect_applications",
    "collect_homebrew",
    "collect_host_applications",
    "collect_storage",
    "parse_homebrew_inventory",
    "parse_volume_info",
    "resolve_storage_location",
]
