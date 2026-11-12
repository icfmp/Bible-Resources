"""Synthetic regression of reversible, plan-driven non-clickable note labels."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from source_osis_inventory import OSIS, _source_tree
from repair_osis_source_bytes import patch_exact_original
from repair_osis_unlinked_reference_labels import (
    render_absent_references_plain, UnlinkedLabelError,
)
from test_repair_osis_source_bytes import SOURCE, plans


def private_input():
    links, inline = plans()
    prepared, _ = patch_exact_original(SOURCE, links, inline)
    return links, prepared


class UnlinkedReferenceLabelTest(unittest.TestCase):
    def test_only_explicit_absent_verse_wrapper_becomes_unlinked_segment(self):
        plan, prepared = private_input()
        final, receipt = render_absent_references_plain(SOURCE, prepared, plan)
        self.assertNotEqual(final, prepared)
        self.assertIn(
            b'<seg type="x-unlinked-reference">intentionally absent</seg>',
            final,
        )
        self.assertIn(b"Keep   exact poetic serialization\n", final)
        self.assertEqual(
            "".join(_source_tree(SOURCE).itertext()),
            "".join(_source_tree(final).itertext()),
        )
        tree = _source_tree(final)
        references = list(tree.iter(OSIS + "reference"))
        segments = list(tree.iter(OSIS + "seg"))
        self.assertEqual([ref.get("osisRef") for ref in references], ["Exod.2.1"])
        self.assertEqual(len(segments), 3)  # 2 preexisting measures, 1 plain label
        self.assertEqual(receipt["explicit_plain_label_count"], 1)
        self.assertTrue(receipt["unrelated_original_bytes_identical"])
        self.assertFalse(receipt["independent_reader_plain_style_verified"])
        self.assertFalse(receipt["editorial_or_release_approved"])

    def test_wrong_source_or_unapproved_wrapper_cannot_be_reinterpreted(self):
        plan, prepared = private_input()
        with self.assertRaises(UnlinkedLabelError):
            render_absent_references_plain(SOURCE + b"x", prepared, plan)
        with self.assertRaises(UnlinkedLabelError):
            render_absent_references_plain(
                SOURCE, prepared.replace(b"<reference>intentionally absent</reference>",
                                         b"<reference osisRef='Gen.1.2'>intentionally absent</reference>"),
                plan,
            )
        with self.assertRaises(UnlinkedLabelError):
            render_absent_references_plain(
                SOURCE, prepared.replace(b"intentionally absent", b"silently changed"),
                plan,
            )

    def test_changes_are_stably_reproducible_but_not_idempotently_applicable(self):
        plan, prepared = private_input()
        first, receipt = render_absent_references_plain(SOURCE, prepared, plan)
        second, receipt2 = render_absent_references_plain(SOURCE, prepared, plan)
        self.assertEqual(first, second)
        self.assertEqual(receipt["new_research_candidate_sha256"],
                         receipt2["new_research_candidate_sha256"])
        with self.assertRaises(UnlinkedLabelError):
            render_absent_references_plain(SOURCE, first, plan)


if __name__ == "__main__":
    unittest.main()
