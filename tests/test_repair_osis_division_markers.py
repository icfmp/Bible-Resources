"""Reversible editorial division metadata, without silent Scripture editing."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from repair_osis_division_markers import patch_divisions, DivisionRepairError
from publisher_osis_usfx_parity import original_osis_verses_and_notes
from source_osis_inventory import OSIS, _source_tree

SOURCE = b"""<?xml version='1.0' encoding='utf-8'?>
<osis xmlns='http://www.bibletechnologies.net/2003/OSIS/namespace'>
<osisText><div type='book' osisID='Gen'><chapter osisID='Gen.1'>
<p><verse osisID='Gen.1.1' sID='Gen.1.1'/>
    *A subject break<note n='a'>Unchanged.</note><verse eID='Gen.1.1'/></p>
<p><verse osisID='Gen.1.2' sID='Gen.1.2'/>
     **A major break<verse eID='Gen.1.2'/></p>
<lg><l><verse osisID='Gen.1.3' sID='Gen.1.3'/>
      *A poetic break<verse eID='Gen.1.3'/></l></lg>
<p><verse osisID='Gen.1.4' sID='Gen.1.4'/>
      *[Uncertain wording]<verse eID='Gen.1.4'/></p>
<p><verse osisID='Gen.1.5' sID='Gen.1.5'/>
      *Dieu is a lexical marker<verse eID='Gen.1.5'/></p>
<lg><l><verse osisID='Gen.1.6' sID='Gen.1.6'/>\n      <hi type='italic'>*Wrapped poetic division</hi><verse eID='Gen.1.6'/></l></lg>\n<p><verse osisID='Gen.1.7' sID='Gen.1.7'/>\n      ***Level three break<verse eID='Gen.1.7'/></p>\n</chapter></div></osisText></osis>
"""


def repair(source=SOURCE):
    return patch_divisions(source, expected_sha256=sha256(source).hexdigest())


class TestDivisionMarkerRemediation(unittest.TestCase):
    def test_reencode_sections_and_stanzas_keep_lexical_symbols(self):
        corrected, receipt = repair()
        self.assertEqual(receipt["converted_markers_by_kind"], {
            "paragraph": 2, "paragraph_level_3": 1, "poetry": 2,
        })
        self.assertEqual(receipt["protected_unchanged_marker_counts"], {
            "protected_textual_symbol": 2,
        })
        self.assertEqual(corrected.count(b'<milestone type="x-subject-division"'), 2)
        self.assertEqual(corrected.count(b'<milestone type="x-stanza-division"'), 2)
        self.assertEqual(corrected.count(b'<milestone type="x-major-subject-division"'), 1)
        self.assertIn(b"*[Uncertain wording]", corrected)
        self.assertIn(b"*Dieu is a lexical marker", corrected)
        self.assertTrue(receipt["all_original_notes_and_machine_targets_preserved"])
        self.assertFalse(receipt["native_sword_readback_verified"])
        self.assertFalse(receipt["release_authorized"])
        first, _, _ = original_osis_verses_and_notes(corrected)
        self.assertFalse(first["Gen.1.1"].lstrip().startswith("*"))
        self.assertFalse(first["Gen.1.2"].lstrip().startswith("*"))
        self.assertFalse(first["Gen.1.3"].lstrip().startswith("*"))
        self.assertTrue(first["Gen.1.4"].lstrip().startswith("*"))
        self.assertFalse(first["Gen.1.6"].lstrip().startswith("*"))
        tags = list(_source_tree(corrected).iter(OSIS + "milestone"))
        self.assertEqual([n.get("subType") for n in tags], [
            "x-original-ascii-star-1", "x-original-ascii-star-2",
            "x-original-ascii-star-1", "x-original-ascii-star-1",
            "x-original-ascii-star-3",
        ])
        self.assertTrue(all(n.get("marker") is None for n in tags))
        self.assertEqual(sum(int(n.get("subType").rsplit("-",1)[1]) for n in tags), 8)

    def test_exact_source_sha_is_mandatory(self):
        with self.assertRaises(DivisionRepairError):
            patch_divisions(SOURCE, expected_sha256="0" * 64)

    def test_unknown_leading_star_outside_paragraph_or_poetry_fails(self):
        changed = SOURCE.replace(
            b"<p><verse osisID='Gen.1.2'", b"<div><verse osisID='Gen.1.2'",
        ).replace(b"<verse eID='Gen.1.2'/></p>",
                  b"<verse eID='Gen.1.2'/></div>")
        with self.assertRaises(DivisionRepairError):
            repair(changed)

    def test_wrong_lexical_position_is_not_edited(self):
        changed = SOURCE.replace(b"    *A subject break", b"    A *subject break")
        corrected, receipt = repair(changed)
        self.assertEqual(receipt["converted_markers_by_kind"], {
            "paragraph": 1, "paragraph_level_3": 1, "poetry": 2,
        })
        self.assertIn(b"A *subject break", corrected)


if __name__ == "__main__":
    unittest.main()
