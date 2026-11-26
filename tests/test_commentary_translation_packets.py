import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_translation_packets import chapters, audit_text, signature, sync_body
from source_osis_inventory import _source_tree


class TranslationPacketsTest(unittest.TestCase):
    def test_chapter_container_and_milestones(self):
        root = _source_tree(b'<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace"><osisText><div type="chapter" osisID="Gen.1"><chapter osisID="Gen.1" sID="Gen.1"/><p>A <hi>B</hi> C.</p><chapter eID="Gen.1"/></div></osisText></osis>')
        chapter = chapters(root)["Gen.1"]
        self.assertIn("A B C.", audit_text(chapter))
        self.assertEqual(signature(chapter)[0], chapter.tag)

    def test_sync_preserves_release_gates_and_rejects_regression(self):
        body = "- [ ] release\n### Genesis\n- [ ] 1 — Translation\n- [ ] 1 — Editorial audit\n"
        progress = {"total_chapters": 1, "completed": [["Genesis", 1, "Translation"]]}
        updated = sync_body(body, progress)
        self.assertEqual(updated, body.replace("[ ] 1 — Translation", "[x] 1 — Translation"))
        with self.assertRaises(ValueError):
            sync_body(updated, {"total_chapters": 1, "completed": []})

    def test_audit_requires_translation(self):
        with self.assertRaises(ValueError):
            sync_body("", {"total_chapters": 1, "completed": [["Genesis", 1, "Editorial audit"]]})
