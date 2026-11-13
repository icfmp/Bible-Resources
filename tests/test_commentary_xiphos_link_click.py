"""Synthetic fail-closed checks for real Xiphos original OSIS-link mouse navigation."""
from __future__ import annotations
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from commentary_xiphos_link_click import (
    _has_target_phrase, _real_original_targets, probe_real_original_osisref_click,
)
from pilot_preflight import PilotError


class OriginalLinkRealClickTests(unittest.TestCase):
    def test_authentic_source_and_real_html_href_must_join_exactly(self):
        source = (b'<p>Some text <reference osisRef="Bible:Ps.23.1">'
                  b'Psalms twenty three</reference> and words</p>')
        rich = (b'<html><a href="sword:///Ps.23.1">'
                b'Psalms twenty three</a></html>')
        self.assertEqual(
            _real_original_targets(source, rich, "Gen 1:1"), ["Ps 23:1"]
        )
        self.assertEqual(
            _real_original_targets(source, rich, "Ps 23:4"), []
        )
        self.assertEqual(
            _real_original_targets(
                source, b'<a href="sword:///Ps.23.2">Psalms twenty three</a>',
                "Gen 1:1"
            ), []
        )
        self.assertEqual(
            _real_original_targets(
                source, b'<a href="https://example.invalid/Ps.23.1">'
                        b'Psalms twenty three</a>',
                "Gen 1:1"
            ), []
        )
        self.assertEqual(
            _real_original_targets(
                source, b'<a href="sword:///Ps.23.1">Different words</a>',
                "Gen 1:1"
            ), []
        )

    def test_ranges_are_not_silently_converted_to_verses(self):
        source = (b'<reference osisRef="Bible:Ps.23.1-Ps.23.6">'
                  b'Psalms twenty three</reference>')
        rich = b'<a href="sword:///Ps.23.1-Ps.23.6">Psalms twenty three</a>'
        self.assertEqual(_real_original_targets(source, rich, "Gen 1:1"), [])

    def test_ten_distinctive_target_words_must_newly_appear(self):
        source = "Header module passage verse words words " + " ".join(
            "targetword%02d" % n for n in range(19)
        )
        before = b"only the original Genesis chapter appears"
        after = ("a different Bible book now displays " + " ".join(
            "targetword%02d" % n for n in range(19)
        )).encode()
        self.assertTrue(_has_target_phrase(source.encode(), after, before))
        self.assertFalse(_has_target_phrase(source.encode(), before, before))
        self.assertFalse(_has_target_phrase(source.encode(), after, after))
        # Nine words are insufficient for the actual 10-word witness.
        nine = " ".join("targetword%02d" % n for n in range(8, 17))
        self.assertFalse(_has_target_phrase(source.encode(), nine.encode(), before))

    def test_unreviewed_display_fails_closed_before_touching_X11(self):
        with self.assertRaisesRegex(PilotError, "Unapproved"):
            probe_real_original_osisref_click(
                {"DISPLAY": ":0", "GDK_BACKEND": "x11"},
                {}, ["Gen 1:1"], installed_sword_root=Path("/missing")
            )


if __name__ == "__main__":
    unittest.main()
