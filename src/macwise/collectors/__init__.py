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
from macwise.collectors.startup import (
    StartupCollection,
    StartupRoot,
    collect_startup,
    parse_launch_plist,
)
from macwise.collectors.storage import (
    StorageCollection,
    collect_storage,
    parse_volume_info,
    resolve_storage_location,
)
from macwise.collectors.usage import UsageCollection, UsageSignal, collect_usage

__all__ = [
    "ApplicationCollection",
    "HomebrewCollection",
    "StartupCollection",
    "StartupRoot",
    "StorageCollection",
    "UsageCollection",
    "UsageSignal",
    "collect_applications",
    "collect_homebrew",
    "collect_host_applications",
    "collect_startup",
    "collect_storage",
    "collect_usage",
    "parse_homebrew_inventory",
    "parse_launch_plist",
    "parse_volume_info",
    "resolve_storage_location",
]
