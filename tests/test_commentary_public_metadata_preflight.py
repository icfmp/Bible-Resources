"""Invented-only fail-closed review of draft public SWORD commentary metadata."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from commentary_public_metadata_preflight import (
    prepare_provisional_public_commentary_conf,
)


class CommentaryFinalDateAndSourceAttributionTests(unittest.TestCase):
    def setUp(self):
        self.private = (
            b"## Original source comment untouched\n[Curated]\n"
            b"Description=Invented public commentary\n"
            b"DataPath=./modules/comments/zcom/curated/\n"
            b"ModDrv=zCom\nSourceType=OSIS\nVersification=KJV\n"
            b"BlockType=CHAPTER\nVersion=0.1.1\n"
            b"SwordVersionDate=2021-02-14\n"
            b"About=Upstream source printing claim that curators have not verified\\par "
            b"An original attribution with old punctuation!\n"
            b"History_0.1.1=Corrected one documented citation and navigation\n"
            b"DistributionLicense=Public Domain\n"
            b"TextSource=https://example.invalid/source\n"
            b"InstallSize=1234\n"
        )
        self.args = dict(
            expected_module_id="Curated",
            expected_module_version="0.1.1",
            source_provider="Invented Source Archive",
            original_sword_version_date="2021-02-14",
            proposed_public_revision_day="2026-11-15",
            revision_summary="Index navigation and one documented source citation correction",
        )

    def test_only_explicit_about_and_date_change_original_attributes_verbatim(self):
        proposed, receipt = prepare_provisional_public_commentary_conf(
            self.private, **self.args)
        self.assertIn(b"SwordVersionDate=2026-11-15\n", proposed)
        self.assertIn(b"Original upstream Invented Source Archive About (verbatim):", proposed)
        self.assertIn(b"source printing claim that curators have not verified", proposed)
        self.assertIn(b"DistributionLicense=Public Domain\n", proposed)
        self.assertIn(b"TextSource=https://example.invalid/source\n", proposed)
        self.assertIn(b"History_0.1.1=Corrected one documented citation", proposed)
        self.assertTrue(receipt["original_upstream_about_verbatim_preserved_with_explicit_attribution"])
        self.assertEqual(receipt["exact_changed_fields"], ["About", "SwordVersionDate"])
        self.assertTrue(receipt["all_other_fields_comments_license_textsource_and_history_exact"])
        self.assertTrue(receipt["proposed_day_must_match_actual_approved_release_day"])
        self.assertFalse(receipt["publication_authorized"])
        self.assertFalse(receipt["public_asset_generated"])
        self.assertNotEqual(receipt["original_private_conf_sha256"], receipt["proposed_public_conf_sha256"])
        self.assertNotIn("printing claim", str(receipt))

    def test_reject_stale_invalid_date_unsafe_description_or_missing_provenance(self):
        bad_args = (
            {"proposed_public_revision_day":"2021-02-14"},
            {"proposed_public_revision_day":"2020-01-01"},
            {"proposed_public_revision_day":"2026-02-30"},
            {"proposed_public_revision_day":"2026-11-15\nDistributionLicense=CC0"},
            {"source_provider":"Invalid\nRights=CC0"},
            {"revision_summary":"Bad\nVersion=999"},
        )
        for delta in bad_args:
            with self.subTest(delta=delta):
                with self.assertRaises(ValueError):
                    prepare_provisional_public_commentary_conf(
                        self.private, **{**self.args, **delta})
        for damaged in (
            self.private.replace(b"About=", b"AltAbout="),
            self.private.replace(b"Version=0.1.1", b"Version=0.1.0"),
            self.private.replace(b"ModDrv=zCom", b"ModDrv=RawText"),
            self.private.replace(b"DistributionLicense=Public Domain\n", b""),
            self.private.replace(b"SwordVersionDate=2021-02-14\n", b""),
            self.private + b"About=Forged duplicate claim\n",
        ):
            with self.subTest(damaged=damaged[-80:]):
                with self.assertRaises(ValueError):
                    prepare_provisional_public_commentary_conf(
                        damaged, **self.args)

    def test_upstream_about_not_silently_rewritten_in_candidate(self):
        original = self.private.replace(
            b"source printing claim", b"dated source edition with uncertain authorship")
        candidate, _ = prepare_provisional_public_commentary_conf(
            original, **self.args)
        self.assertIn(b"dated source edition with uncertain authorship", candidate)
        self.assertNotIn(b"source printing claim", candidate)
        self.assertEqual(candidate.count(b"About="), 1) # only one actual SWORD field; the quoted value stays intact


if __name__ == "__main__":
    unittest.main()
