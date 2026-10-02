# ANSI Style

A small, dependency-free Python library for applying ANSI colour and text-attribute escape sequences to strings, with built-in detection of terminals that cannot display them.

## Usage

```python
from ansi_style import style, Style, DISABLED

# Module-level instance: enabled when the environment does not look dumb.
print(style.wrap("error", "red bold"))

# Construct your own when you need control (e.g. tie to --color or isatty).
s = Style(enabled=True)
print(s.wrap("warning", "yellow"))

# Strip sequences back out — works on disabled instances too.
print(DISABLED.strip("\x1b[31mhi\x1b[0m"))  # -> "hi"
```

Exported names: `Style`, `style`, `DISABLED`.

## Why this exists

Other colour libraries grow large trying to support every terminal feature: 256-colour palettes, 24-bit RGB, nested attribute stacks, auto-detection across a dozen environment variables.  That machinery is a liability when the goal is just "make log lines red unless we're on a dumb terminal."

ANSI Style supports eight foreground colours, eight background colours, and four text attributes (bold, dark, italic, underline).  That is enough for visible log categorisation and nothing more.  The trade-off: if you need true-colour output, this library will not help you.

The only environmental input considered is the `TERM` environment variable.  The strings `dumb`, `unknown`, and an empty or unset `TERM` all disable output.  The decision is evaluated once at import time for the module-level `style` instance; callers who need a different policy construct their own `Style(enabled=...)` and can wire it to `sys.stdout.isatty()` or a CLI flag.

## Edge cases you will hit

- **Unknown style names raise `ValueError`** when colour is enabled, so typos surface immediately.  When colour is disabled, `.wrap()` returns the text unchanged and does *not* validate the name — the point of disabling is to be a silent passthrough.
- **`.strip()` only removes SGR sequences with a single numeric parameter** (the form this library emits).  Sequences with `;`-separated parameter lists are emitted by `.wrap()` when composing styles, and the stripper *does* handle those; richer sequences from other libraries may survive stripping.  This is intentional: a broader regex risks eating non-SGR CSI sequences.
- **`Style.wrap("text", "") is a no-op**, not an error.  Conditional formatting often produces an empty name string; treating it as a pass-through keeps call sites simple.
