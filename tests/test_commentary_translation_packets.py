import sys
from pathlib import Path
import unittest
import tempfile
from types import SimpleNamespace
from hashlib import sha256

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_translation_packets import chapters, audit_text, signature, sync_body, assemble
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

    def test_assemble_requires_complete_coverage_and_preserves_template_header(self):
        source = b'<osis xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace"><osisText xml:lang="en"><chapter osisID="Gen.1"><p>Hello.</p></chapter></osisText></osis>'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            modern = root / "source.xml"
            modern.write_bytes(source)
            template = root / "template.xml"
            template.write_bytes(source.replace(b'xml:lang="en"', b'xml:lang="fr"'))
            fragments = root / "fragments"
            fragments.mkdir()
            output = root / "candidate.xml"
            args = SimpleNamespace(modern=modern, modern_sha=sha256(source).hexdigest(),
                                   template=template, language="fr",
                                   manuscripts=fragments, output=output)
            with self.assertRaises(ValueError):
                assemble(args)
            self.assertFalse(output.exists())
            (fragments / "Gen.1.xml").write_text('<chapter xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace" osisID="Gen.1"><p>Bonjour.</p></chapter>')
            assemble(args)
            self.assertIn(b"Bonjour.", output.read_bytes())
            self.assertIn(b'xml:lang="fr"', output.read_bytes())
            with self.assertRaises(FileExistsError):
                assemble(args)
