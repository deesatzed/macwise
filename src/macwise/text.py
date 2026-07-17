"""Safe presentation helpers for untrusted evidence values."""

import unicodedata


def safe_display_text(value: object) -> str:
    """Collapse control, format, newline, and repeated whitespace for human display."""
    text = str(value)
    visible = "".join(
        " " if unicodedata.category(character) in {"Cc", "Cf"} else character for character in text
    )
    return " ".join(visible.split())
