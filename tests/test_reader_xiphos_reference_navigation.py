"""Synthetic bounded Xiphos navigation commands; no GUI needed."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from reader_xiphos_headless_smoke import _navigation_commands, XiphosSmokeError


class TestXiphosReferenceNavigation(unittest.TestCase):
    def test_shortcut_remains_the_default_existing_navigation(self):
        commands=_navigation_commands("Gen 6:9", "shortcut")
        self.assertEqual(commands[0][-1], "ctrl+l")
        self.assertEqual(commands[1][-1], "Gen 6:9")

    def test_explicit_reference_field_targets_only_test_display(self):
        commands=_navigation_commands("Gen 7:17", "reference-entry")
        self.assertEqual(commands[0], [
            "xdotool","mousemove","--sync","752","121","click","1"])
        self.assertEqual(commands[1][-1], "ctrl+a")
        self.assertEqual(commands[2][-1], "Gen 7:17")
        self.assertEqual(commands[-1][-1], "Return")

    def test_invalid_navigation_mode_fails_closed(self):
        with self.assertRaises(XiphosSmokeError):
            _navigation_commands("Ps 3:1", "guessed-screen-click")
