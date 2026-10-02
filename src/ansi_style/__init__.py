"""ANSI Style

Terminal colour and style helpers that detect a dumb terminal.

Public API:
    style    -- Style instance with .wrap(text, names) / .strip(text)
    Style    -- the class itself (for isinstance checks / custom construction)
    DISABLED -- a pre-built Style that emits no escape codes

Design choices documented in README.md.
"""

from .core import Style, style, DISABLED

__all__ = ["Style", "style", "DISABLED"]
__version__ = "1.0.0"
