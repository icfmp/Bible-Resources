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


class PrivateCommentaryZipRehearsalTests(unittest.TestCase):
    """Entirely invented content; never a public source or release fixture."""

    def setUp(self):
        from tempfile import TemporaryDirectory
        from reviewed_compiled_commentary_rebuild import zcom_member_suffixes
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.root = self.base / "private-original-installed"
        self.out = self.base / "private-rehearsal"
        self.root.mkdir()
        self.out.mkdir()
        original = CommentaryFinalDateAndSourceAttributionTests()
        original.setUp()
        self.conf = (original.private.replace(
            b"BlockType=CHAPTER\n", b"CompressType=ZIP\nBlockType=CHAPTER\n"
        ))
        target = self.root / "mods.d/curated.conf"
        target.parent.mkdir(parents=True)
        target.write_bytes(self.conf)
        for name in zcom_member_suffixes("CHAPTER"):
            item = self.root / "modules/comments/zcom/curated" / name
            item.parent.mkdir(parents=True, exist_ok=True)
            item.write_bytes(("Invented native content " + name).encode("ascii"))
        self.kw = dict(
            module_id="Curated", expected_version="0.1.1",
            source_provider="Invented Source Archive",
            original_sword_version_date="2021-02-14",
            hypothetical_revision_day="2026-11-15",
            revision_summary="Index navigation and one documented source citation correction",
        )

    def rehearse(self, folder=None, **updates):
        from commentary_public_metadata_preflight import (
            rehearse_private_versioned_commentary_package,
        )
        return rehearse_private_versioned_commentary_package(
            self.root, folder or self.out, **{**self.kw, **updates}
        )

    def test_deterministic_reinstalled_zip_changes_only_two_conf_fields(self):
        import hashlib
        import zipfile
        result = self.rehearse()
        again = self.base / "independent-run"
        again.mkdir()
        copy = self.rehearse(again)
        self.assertEqual(result["zip_sha256"], copy["zip_sha256"])
        self.assertEqual(result["zip_member_count"], 7)
        self.assertEqual(result["status"],
                         "PRIVATE_FULL_CONF_AND_SWORD_ZCOM_ZIP_REHEARSAL_NOT_RELEASE")
        self.assertEqual(result["compiled_block_type"], "CHAPTER")
        self.assertTrue(result["all_six_native_compiled_members_preserved"])
        self.assertTrue(result["only_about_and_sword_version_date_changed"])
        self.assertFalse(result["owner_release_authorized"])
        self.assertFalse(result["artifact_published_or_uploaded"])
        self.assertFalse(result["actual_release_date_selected"])
        self.assertNotIn("Invented native content", str(result))
        package = self.out / "PRIVATE-REHEARSAL-DO-NOT-RELEASE.zip"
        self.assertEqual(hashlib.sha256(package.read_bytes()).hexdigest(),
                         result["zip_sha256"])
        with zipfile.ZipFile(package) as z:
            self.assertTrue(all(info.compress_type == zipfile.ZIP_DEFLATED
                                for info in z.infolist()))
            self.assertEqual(len(z.namelist()), 7)
            self.assertEqual(len(set(z.namelist())), 7)
            name = "mods.d/curated.conf"
            self.assertEqual(z.read(name), (
                self.out / "private-rehearsed-install" / name
            ).read_bytes())
            self.assertIn(b"SwordVersionDate=2026-11-15", z.read(name))
            self.assertIn(b"Original upstream Invented Source Archive About", z.read(name))
            self.assertIn(b"DistributionLicense=Public Domain", z.read(name))
            self.assertNotEqual(z.read(name), self.conf)
            for file in z.namelist():
                if file == name:
                    continue
                self.assertEqual(z.read(file), (self.root / file).read_bytes())

    def test_existing_private_output_cannot_be_overwritten(self):
        self.rehearse()
        with self.assertRaises(ValueError):
            self.rehearse()

    def test_extra_missing_empty_or_symlinked_native_member_rejected(self):
        folder = self.root / "modules/comments/zcom/curated"
        missing = folder / "ot.czv"
        content = missing.read_bytes()
        missing.unlink()
        with self.assertRaises(ValueError):
            self.rehearse()
        missing.write_bytes(content)
        extra = folder / "random"
        extra.write_bytes(b"invented")
        with self.assertRaises(ValueError):
            self.rehearse()
        extra.unlink()
        missing.write_bytes(b"")
        with self.assertRaises(ValueError):
            self.rehearse()
        missing.unlink()
        missing.symlink_to(folder / "ot.czs")
        with self.assertRaises(ValueError):
            self.rehearse()

    def test_incorrect_compilation_descriptor_is_rejected(self):
        conf = self.root / "mods.d/curated.conf"
        for before, after in (
            (b"BlockType=CHAPTER", b"BlockType=BOOK"),
            (b"CompressType=ZIP", b"CompressType=UNKNOWN"),
            (b"Version=0.1.1", b"Version=0.1.0"),
            (b"DataPath=./modules/comments/zcom/curated/",
             b"DataPath=../../wrong"),
        ):
            with self.subTest(before=before):
                conf.write_bytes(self.conf.replace(before, after))
                with self.assertRaises(ValueError):
                    self.rehearse()
        conf.write_bytes(self.conf)

    def test_test_day_is_never_approved_release_date(self):
        with self.assertRaises(ValueError):
            self.rehearse(hypothetical_revision_day="2020-01-01")
        with self.assertRaises(ValueError):
            self.rehearse(hypothetical_revision_day="invalid")


if __name__ == "__main__":
    unittest.main()
