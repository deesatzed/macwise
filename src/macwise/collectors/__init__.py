"""Read-only evidence collectors."""

from macwise.collectors.applications import ApplicationCollection, collect_applications
from macwise.collectors.homebrew import (
    HomebrewCollection,
    collect_homebrew,
    parse_homebrew_inventory,
)

__all__ = [
    "ApplicationCollection",
    "HomebrewCollection",
    "collect_applications",
    "collect_homebrew",
    "parse_homebrew_inventory",
]
