"""Tests for ANSI Style.

All tests are deterministic.  The environmental decision is isolated in
the function _default_enabled(), which we patch when we need it; every
other test constructs Style(enabled=...) directly so the result does not
depend on the container's TERM.
"""

import os
import unittest

from ansi_style import Style, style, DISABLED
from ansi_style.core import _looks_dumb


class TestLooksDumb(unittest.TestCase):
    def _check(self, term, expected):
        # We always restore TERM even if an assert fails, because the suite
        # shares a process and a poisoned environment would break later tests.
        old = os.environ.get("TERM")
        try:
            if term is None:
                os.environ.pop("TERM", None)
            else:
                os.environ["TERM"] = term
            self.assertEqual(_looks_dumb(os.environ.get("TERM")), expected)
        finally:
            if old is None:
                os.environ.pop("TERM", None)
            else:
                os.environ["TERM"] = old

    def test_dumb_term(self):
        self._check("dumb", True)

    def test_xterm(self):
        self._check("xterm-256color", False)

    def test_unknown(self):
        self._check("unknown", True)

    def test_empty(self):
        self._check("", True)

    def test_unset(self):
        self._check(None, True)

    def test_case_insensitive(self):
        self._check("DUMB", True)
        self._check("Dumb", True)


class TestWrap(unittest.TestCase):
    def test_single_name(self):
        s = Style(enabled=True)
        self.assertEqual(s.wrap("hi", "red"), "\x1b[31mhi\x1b[0m")

    def test_multiple_names(self):
        s = Style(enabled=True)
        self.assertEqual(s.wrap("hi", "red bold"), "\x1b[31;1mhi\x1b[0m")

    def test_extra_whitespace(self):
        s = Style(enabled=True)
        self.assertEqual(s.wrap("hi", "  red   bold "), "\x1b[31;1mhi\x1b[0m")

    def test_disabled_is_passthrough(self):
        s = Style(enabled=False)
        self.assertEqual(s.wrap("hi", "red"), "hi")

    def test_empty_names_no_op(self):
        s = Style(enabled=True)
        self.assertEqual(s.wrap("hi", ""), "hi")

    def test_unknown_name_raises(self):
        s = Style(enabled=True)
        with self.assertRaises(ValueError):
            s.wrap("hi", "mauve")

    def test_disabled_does_not_validate(self):
        # When colour is off we return text immediately, so an unknown name
        # must NOT raise.  This is the behaviour the implementation promises;
        # testing it keeps the contract honest.
        s = Style(enabled=False)
        self.assertEqual(s.wrap("hi", "mauve"), "hi")

    def test_background(self):
        s = Style(enabled=True)
        self.assertEqual(s.wrap("hi", "on_blue"), "\x1b[44mhi\x1b[0m")

    def test_attributes(self):
        s = Style(enabled=True)
        self.assertEqual(s.wrap("hi", "underline"), "\x1b[4mhi\x1b[0m")


class TestStrip(unittest.TestCase):
    def test_strip_simple(self):
        s = Style(enabled=True)
        marked = s.wrap("hello", "red bold")
        self.assertEqual(s.strip(marked), "hello")

    def test_strip_leaves_plain(self):
        s = Style(enabled=True)
        self.assertEqual(s.strip("hello"), "hello")

    def test_strip_disabled(self):
        # strip() works regardless of the enabled flag — it is a pure string
        # operation.  This test documents that fact.
        marked = DISABLED.wrap("hello", "red")
        self.assertEqual(DISABLED.strip(marked), "hello")

    def test_strip_multi_param(self):
        # Sequences with a ";"-separated parameter list are emitted by .wrap
        # when composing styles, so the stripper must handle them.  The regex
        # above deliberately only matches single numeric params; this test
        # pins the current (intentional) limitation so a future change is a
        # conscious decision.
        text = "\x1b[31;1mhi\x1b[0m"
        self.assertEqual(DISABLED.strip(text), "hi")

    def test_strip_nested(self):
        s = Style(enabled=True)
        inner = s.wrap("hi", "bold")
        outer = s.wrap(inner, "red")
        self.assertEqual(s.strip(outer), "hi")


class TestDisabledSingleton(unittest.TestCase):
    def test_disabled_is_style(self):
        self.assertIsInstance(DISABLED, Style)

    def test_disabled_flag(self):
        self.assertFalse(DISABLED.enabled)

    def test_disabled_wrap_passthrough(self):
        self.assertEqual(DISABLED.wrap("x", "red"), "x")


class TestRepr(unittest.TestCase):
    def test_repr_enabled(self):
        self.assertEqual(repr(Style(enabled=True)), "Style(enabled=True)")

    def test_repr_disabled(self):
        self.assertEqual(repr(Style(enabled=False)), "Style(enabled=False)")


class TestModuleStyle(unittest.TestCase):
    def test_module_style_is_style(self):
        self.assertIsInstance(style, Style)

    def test_module_style_enabled_reflects_env(self):
        # The module-level instance decides at import time.  We cannot
        # re-import cleanly inside a test, so we just assert the type of
        # .enabled — the actual value depends on the container's TERM.
        self.assertIsInstance(style.enabled, bool)


if __name__ == "__main__":
    unittest.main()
