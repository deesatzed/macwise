"""Pure renderers for MacWise audit documents."""

from macwise.reporting.json_report import render_json
from macwise.reporting.markdown import render_markdown

__all__ = ["render_json", "render_markdown"]
