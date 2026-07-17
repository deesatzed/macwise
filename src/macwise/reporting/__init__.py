"""Pure renderers for MacWise audit documents."""

from macwise.reporting.json_report import parse_json, render_json
from macwise.reporting.markdown import render_markdown

__all__ = ["parse_json", "render_json", "render_markdown"]
