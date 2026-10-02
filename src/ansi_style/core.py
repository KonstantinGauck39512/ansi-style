"""Core implementation for ANSI Style.

This module deliberately keeps the feature surface small: 8 foreground
colours, 8 background colours, and four text attributes. 256-colour and
24-bit RGB are not supported because they add format-complexity (numeric
arguments, colon-separated sub-parameters) that is easy to get wrong and
hard to test without a real terminal.  The trade-off is a library that
works the same way everywhere.

The *only* environmental input we consider is the TERM environment
variable.  We do not consult isatty() at this layer: whether colour is
desirable is a property of the *output stream*, not of the library.  The
Style constructor accepts a flag instead, so callers can wire it to
stdout.isatty() (or a CLI --color flag) at the point of use.
"""

from __future__ import annotations

import os
import re
from typing import Dict, Optional, Tuple


# ANSI SGR parameter for each named style.  Using integers rather than
# per-name classes keeps the code flat and makes composition (wrap with two
# names) a simple join on ";".
_CODES: Dict[str, int] = {
    "reset": 0,
    "bold": 1,
    "dark": 2,
    "italic": 3,
    "underline": 4,
    "blink": 5,
    "reverse": 7,
    "concealed": 8,
    # Foreground (normal intensity)
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
    # Background
    "on_black": 40,
    "on_red": 41,
    "on_green": 42,
    "on_yellow": 43,
    "on_blue": 44,
    "on_magenta": 45,
    "on_cyan": 46,
    "on_white": 47,
}


# Matches a complete SGR sequence: CSI followed by one or more numeric
# parameters separated by ";" and "m".  This covers the single-parameter
# form (\x1b[31m) and the multi-parameter form emitted by .wrap() when
# composing styles (\x1b[31;1m).  Richer sequences (colon-separated
# sub-parameters, non-numeric args) from other libraries may survive
# stripping; this is intentional so the regex does not eat non-SGR CSI
# sequences.
_ANSI_RE = re.compile(r"\x1b\[\d+(;\d+)*m")


def _looks_dumb(term: Optional[str]) -> bool:
    """Return True if *term* looks like a terminal that cannot handle colour.

    The strings "dumb", "unknown", and "" (empty) all indicate that no
    useful terminal is attached.  We treat None (variable unset) the same
    way: if the caller did not tell us a terminal exists, we assume it
    doesn't.
    """
    if not term:
        return True
    return term.lower() in {"dumb", "unknown"}


def _default_enabled() -> bool:
    """Decide whether to enable colour by inspecting the environment.

    Separated from the constructor so tests can patch *this* function (or
    just construct Style(enabled=...) directly).
    """
    return not _looks_dumb(os.environ.get("TERM"))


class Style:
    """Apply ANSI SGR escape sequences to text.

    Parameters:
        enabled: if False, .wrap() returns text unchanged and .strip() still
                 works.  This is the seam where callers attach their own
                 colour policy (a CLI flag, an isatty() check, etc.).

    Example:
        >>> s = Style(enabled=True)
        >>> s.wrap("hello", "red")
        '\\x1b[31mhello\x1b[0m'
        >>> s.wrap("hello", "red bold")
        '\\x1b[31;1mhello\x1b[0m'
    """

    __slots__ = ("enabled",)

    def __init__(self, enabled: Optional[bool] = None) -> None:
        if enabled is None:
            enabled = _default_enabled()
        # We store bool rather than leaving the Optional so the attribute is
        # always directly usable in conditionals downstream.
        self.enabled = bool(enabled)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def wrap(self, text: str, names: str) -> str:
        """Wrap *text* in the SGR sequences named by *names*.

        *names* is a whitespace-separated string ("red", "red bold",
        "on_blue underline").  Unknown names raise ValueError so callers
        catch typos at the call site rather than seeing silently stripped
        text on a colour terminal.

        When disabled, returns *text* untouched.  The reset sequence is
        always appended so styles do not bleed past the wrapped region.
        """
        if not self.enabled:
            return text
        codes = self._parse(names)
        if not codes:
            # Empty name string -> no styling.  We treat this as a no-op
            # rather than raising, because conditional formatting (where the
            # caller may pass an empty string) is a common use case.
            return text
        start = "\x1b[" + ";".join(str(c) for c in codes) + "m"
        return start + text + "\x1b[0m"

    def strip(self, text: str) -> str:
        """Remove the SGR sequences emitted by .wrap() from *text*.

        Also removes sequences produced by other libraries, provided they
        use the numeric-parameter form we recognise (single or
        ";"-separated).
        """
        return _ANSI_RE.sub("", text)

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _parse(self, names: str) -> Tuple[int, ...]:
        out = []
        for chunk in names.split():
            if chunk not in _CODES:
                raise ValueError("unknown style name: %r" % chunk)
            out.append(_CODES[chunk])
        return tuple(out)

    def __repr__(self) -> str:
        return "Style(enabled=%r)" % self.enabled


# A disabled singleton, for callers who want "no colour, ever" without
# allocating a new object each time.  Identity-equal to itself.
DISABLED = Style(enabled=False)

# Module-level convenience instance, enabled when the environment looks
# capable.  Importing this name fixes the decision at import time: if the
# caller later changes os.environ["TERM"], this instance will *not*
# re-evaluate.  That is the intended behaviour — import-time detection keeps
# output stable within a single process.
style = Style()
