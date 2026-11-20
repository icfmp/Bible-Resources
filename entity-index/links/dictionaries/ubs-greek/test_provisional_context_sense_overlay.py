#!/usr/bin/env python3
"""Only uniquely source-attested Greek UBS lexical sense may be staged provisionally."""
import runpy,unittest
from pathlib import Path
MOD=runpy.run_path(str(Path(__file__).with_name("build_provisional_context_sense_overlay.py")))

class SourceProvisionalGreekTests(unittest.TestCase):
    def test_original_word_id_counts_are_exhaustive(self):
        self.assertEqual(MOD["TOTAL"],137741)
        self.assertEqual(MOD["UNIQUE"],122504)
        self.assertEqual(MOD["UNRESOLVED"],15237)
    def test_source_lexid_provisional_status_explicit(self):
        import inspect
        source=inspect.getsource(MOD["make"])
        self.assertIn("NOT_contextually_verified",source)
        self.assertIn("verse_context_semantically_verified",source)
        self.assertIn("public_release_approved",source)
        self.assertIn("source_macula_ubs_ln_overlap",source)
        self.assertIn("dict(outcomes)!=audit",source)
    def test_read_only_no_lexical_definition_copying(self):
        import inspect
        source=inspect.getsource(MOD["make"])
        self.assertNotIn("DefinitionShort",source)
        self.assertNotIn("DefinitionLong",source)
        self.assertIn("meaning_edits_or_textual_translations",source)
if __name__=="__main__":unittest.main()
