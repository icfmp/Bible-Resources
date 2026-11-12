"""Synthetic regression checks for research-only OSIS technical link repair."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys
import unittest

from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from repair_osis_note_links import LinkRepairError, propose
from source_osis_inventory import OSIS, _source_tree

SOURCE = b"""<?xml version="1.0" encoding="UTF-8"?>
<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace">
 <osisText osisIDWork="Synthetic">
 <div type="book" osisID="Gen"><chapter osisID="Gen.1">
 <verse osisID="Gen.1.1" sID="Gen.1.1"/>First &amp; faithful
 <note n="a" type="explanation">Compare <reference osisRef="Gen.9.1">Exodus 2.1</reference>;
 textual variant <reference osisRef="Gen.1.2">v.2 omitted</reference>.
 No text or line breaks may disappear.</note>
 <verse eID="Gen.1.1"/>
 <verse osisID="Gen.1.3" sID="Gen.1.3"/>Third.<verse eID="Gen.1.3"/>
 </chapter></div>
 <div type="book" osisID="Exod"><chapter osisID="Exod.2">
 <verse osisID="Exod.2.1" sID="Exod.2.1"/>Second.<verse eID="Exod.2.1"/>
 </chapter></div>
 </osisText></osis>"""


def plan(src=SOURCE):
    return {
        "schema_version": 1, "purpose": "research_only_not_approved",
        "resource_id": "synthetic-test",
        "source_sha256": sha256(src).hexdigest(),
        "edits": [
            {"note_host": "Gen.1.1", "note_index": 1,
             "old_target": "Gen.9.1", "new_target": "Exod.2.1",
             "action": "replace_target",
             "reason": "The printed note says Exodus but links to Genesis nine",
             "evidence_url": "https://example.org/test-evidence"},
            {"note_host": "Gen.1.1", "note_index": 1,
             "old_target": "Gen.1.2", "new_target": None,
             "action": "disable_absent_target",
             "reason": "This note explains an intentionally omitted verse",
             "evidence_url": "https://example.org/test-evidence"},
        ],
    }


class TestSourceBoundTechnicalLinkRepair(unittest.TestCase):
    def test_two_technical_changes_only_preserve_every_text_character(self):
        output, report = propose(SOURCE, plan())
        orig = _source_tree(SOURCE)
        result = _source_tree(output)
        self.assertEqual("".join(orig.itertext()), "".join(result.itertext()))
        self.assertEqual(len(list(orig.iter())), len(list(result.iter())))
        notes = list(result.iter(OSIS + "note"))
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0].get("n"), "a")
        links = list(notes[0].iter(OSIS + "reference"))
        self.assertEqual([x.get("osisRef") for x in links], ["Exod.2.1", None])
        self.assertEqual(report["change_count"], 2)
        self.assertTrue(report["all_original_text_and_whitespace_characters_preserved"])
        self.assertFalse(report["editorial_or_release_approved"])
        self.assertFalse(report["real_reader_navigation_tested"])
        self.assertIn(b'osisRef="Gen.9.1"', SOURCE)

    def test_original_sha_and_approval_status_must_match(self):
        for mutated in (
            SOURCE + b"x",
            SOURCE.replace(b"faithful", b"altered"),
        ):
            with self.subTest(mutated=mutated[:10]), self.assertRaises(LinkRepairError):
                propose(mutated, plan())
        bad = plan()
        bad["purpose"] = "approved_for_publication"
        with self.assertRaises(LinkRepairError):
            propose(SOURCE, bad)
        bad = plan()
        bad["edits"] = []
        with self.assertRaises(LinkRepairError):
            propose(SOURCE, bad)

    def test_wrong_note_host_ordinal_original_or_new_target_rejected(self):
        for field, value in (
            ("note_host", "Gen.1.3"), ("note_index", 2),
            ("old_target", "Gen.99.1"), ("new_target", "Exod.2.99"),
        ):
            bad = plan()
            bad["edits"][0][field] = value
            with self.subTest(field=field), self.assertRaises(LinkRepairError):
                propose(SOURCE, bad)

    def test_cannot_deactivate_existing_destination(self):
        src = SOURCE.replace(b'osisRef="Gen.9.1"', b'osisRef="Exod.2.1"')
        bad = plan(src)
        bad["edits"][0]["old_target"] = "Exod.2.1"
        bad["edits"][0]["new_target"] = None
        bad["edits"][0]["action"] = "disable_absent_target"
        with self.assertRaises(LinkRepairError):
            propose(src, bad)

    def test_ambiguous_same_reference_in_same_note_rejected(self):
        src = SOURCE.replace(b'osisRef="Gen.1.2"', b'osisRef="Gen.9.1"')
        bad = plan(src)
        bad["edits"] = bad["edits"][:1]
        with self.assertRaises(LinkRepairError):
            propose(src, bad)

    def test_duplicate_edits_and_invalid_types_rejected(self):
        import copy
        bad = plan()
        bad["edits"].append(copy.deepcopy(bad["edits"][0]))
        with self.assertRaises(LinkRepairError):
            propose(SOURCE, bad)
        bad = plan()
        bad["edits"][0]["note_index"] = True
        with self.assertRaises(LinkRepairError):
            propose(SOURCE, bad)
        bad = plan()
        bad["approved"] = True
        with self.assertRaises(LinkRepairError):
            propose(SOURCE, bad)


if __name__ == "__main__":
    unittest.main()
