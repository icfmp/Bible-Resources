"""Synthetic tests; only structure metadata may escape source markup review."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from source_osis_note_markup_shape import inspect_markup, SourceMarkupShapeError

XML = b"""<?xml version='1.0' encoding='UTF-8'?>
<osis xmlns='http://www.bibletechnologies.net/2003/OSIS/namespace'><osisText>
<div type='book' osisID='Gen'><chapter osisID='Gen.1'>
<verse sID='Gen.1.1' osisID='Gen.1.1'/>Some private Bible prose
<note n='a'>Private note prose <hi type='italic'>side</hi>
<m who='example'>Secret metric label</m> surrounding words
<m>Hidden numeric 7.4</m> private tail <hi type='bold'>detail</hi>
</note><verse eID='Gen.1.1'/>
</chapter></div></osisText></osis>"""


class MarkupShapeTests(unittest.TestCase):
    def test_only_structural_shapes_no_note_words(self):
        report=inspect_markup(XML,expected_sha256=sha256(XML).hexdigest(),
                              host="Gen.1.1",note_index=1,local_tag="m")
        self.assertEqual(report["occurrences_in_note"],2)
        self.assertEqual(report["occurrences_in_whole_source"],2)
        self.assertEqual(report["bounded_shapes"][0]["parent_local_tag"],"note")
        self.assertEqual(report["bounded_shapes"][0]["attribute_keys"],["who"])
        self.assertEqual(report["bounded_shapes"][1]["child_local_tags"],[])
        self.assertFalse(report["scripture_and_note_prose_exposed"])
        raw=json.dumps(report)
        for secret in ("Secret metric label","Hidden numeric 7.4",
                       "private Bible prose","Private note prose","example"):
            self.assertNotIn(secret,raw)

    def test_wrong_source_host_or_tag_is_rejected(self):
        opts=dict(expected_sha256=sha256(XML).hexdigest(),
                  host="Gen.1.1",note_index=1,local_tag="m")
        for changed in (
            dict(expected_sha256="0"*64),
            dict(host="Exod.1.1"),
            dict(note_index=0),
            dict(note_index=True),
            dict(local_tag="mismatch"),
            dict(local_tag="../m"),
        ):
            with self.subTest(changed=changed),self.assertRaises(SourceMarkupShapeError):
                inspect_markup(XML,**dict(opts,**changed))


if __name__=="__main__":
    unittest.main()
