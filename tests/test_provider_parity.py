"""Offline regression tests for the declared Bible/Bible Resources source boundary."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_provider_parity import compare, declared_providers, expected_inventory, literal_constant
from check_updates import check


BIBLE_PROVIDERS = """
from dataclasses import dataclass
@dataclass(frozen=True)
class Provider:
    id: str
    name: str
    url: str
    catalogue_url: str
    packages_url: str

CROSSWIRE = Provider('crosswire','CrossWire','https://www.crosswire.org/ftpmirror/pub/sword/',
  'https://www.crosswire.org/ftpmirror/pub/sword/raw/mods.d.tar.gz',
  'https://www.crosswire.org/ftpmirror/pub/sword/packages/rawzip/')
EXTRA = Provider('andbible-extra','AndBible Extra (Xiphos)','https://andbible.github.io/andbible-extra/',
  'https://andbible.github.io/andbible-extra/mods.d.tar.gz','https://andbible.github.io/andbible-extra/zip/')
ANDBIBLE = Provider('andbible','AndBible','https://andbible.github.io/data/andbible/',
  'https://andbible.github.io/data/andbible/mods.d.tar.gz',
  'https://andbible.github.io/data/andbible/zip/')
STEP = Provider('step','STEP Bible (Tyndale)','https://public.modules.stepbible.org/',
  'https://public.modules.stepbible.org/catalog/mods.d.tar.gz',
  'https://public.modules.stepbible.org/packages/')
EBIBLE = Provider('ebible','eBible','https://ebible.org/sword/',
  'https://ebible.org/sword/mods.d.tar.gz','https://ebible.org/sword/zip/')
YOUVERSION = Provider('youversion','YouVersion / Bible.com','https://www.bible.com/',
  'https://bible.youversionapi.com/3.1/configuration.json','')
BIBLE_RESOURCES = Provider('bible-resources','Bible Resources',
  'https://icfmp.github.io/Bible-Resources/',
  'https://icfmp.github.io/Bible-Resources/catalog/v1/catalog.json',
  'https://icfmp.github.io/Bible-Resources/sword/packages/')
DEFAULT_PROVIDERS = (CROSSWIRE, EXTRA, ANDBIBLE, STEP, EBIBLE, YOUVERSION)
PROVIDERS = (*DEFAULT_PROVIDERS, BIBLE_RESOURCES)
"""
REFERENCE = """
SOURCE_URL = 'https://www.openbible.info/labs/cross-references/'
DOWNLOAD_URL = 'https://a.openbible.info/data/cross-references.zip'
"""
TOPIC = """
SOURCE_URL='https://www.openbible.info/topics/'
DOWNLOAD_URL='https://a.openbible.info/data/topic-scores.zip'
"""


class ProviderParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((ROOT / "config/upstreams.json").read_text(encoding="utf-8"))
        cls.sources = {"bible/providers.py": BIBLE_PROVIDERS,
                       "bible/reference_data.py": REFERENCE,
                       "bible/topic_data.py": TOPIC}

    def test_complete_registered_inventory(self):
        report = compare(self.config, self.sources)
        self.assertEqual(report["status"], "in_sync", report["errors"])
        self.assertEqual(len(report["bible_sword_providers"]), 5)
        self.assertEqual(len(report["bible_external_sources"]), 4)

    def test_missing_sword_provider_is_detected(self):
        config = deepcopy(self.config)
        config["providers"] = [p for p in config["providers"] if p["id"] != "step"]
        report = compare(config, self.sources)
        self.assertIn("SWORD: Bible declares missing source step", report["errors"])

    def test_new_bible_provider_is_detected(self):
        sources = dict(self.sources)
        sources["bible/providers.py"] = sources["bible/providers.py"].replace(
            "PROVIDERS = (*DEFAULT_PROVIDERS, BIBLE_RESOURCES)", "NEW = Provider('new','New','https://new.test/', 'https://new.test/mods.d.tar.gz','https://new.test/zip/')\nPROVIDERS = (*DEFAULT_PROVIDERS, BIBLE_RESOURCES, NEW)"
        )
        report = compare(self.config, sources)
        self.assertIn("SWORD: Bible declares missing source new", report["errors"])

    def test_wrong_package_endpoint_is_detected(self):
        config = deepcopy(self.config)
        config["providers"][2]["packages_url"] = "https://example.test/zip/"
        report = compare(config, self.sources)
        self.assertIn("SWORD: andbible.packages_url differs from Bible", report["errors"])

    def test_wrong_step_catalogue_directory_is_detected(self):
        config = deepcopy(self.config)
        item = next(p for p in config["providers"] if p["id"] == "step")
        item["base_url"] = "https://public.modules.stepbible.org/"
        report = compare(config, self.sources)
        self.assertIn("SWORD: step.base_url differs from Bible", report["errors"])

    def test_missing_openbible_dataset_is_detected(self):
        config = deepcopy(self.config)
        config["external_sources"] = [p for p in config["external_sources"]
                                      if p["id"] != "openbible-topics"]
        report = compare(config, self.sources)
        self.assertIn("external: Bible declares missing source openbible-topics", report["errors"])

    def test_provider_source_is_inspected_not_executed(self):
        source = BIBLE_PROVIDERS + "\nraise Exception('Should never run')\n"
        self.assertEqual(len(declared_providers(source)), 7)

    def test_literal_starred_provider_aliases_and_safe_rejection(self):
        declared = declared_providers(BIBLE_PROVIDERS)
        self.assertEqual(len(declared), 7)
        self.assertEqual(declared[-1]["id"], "bible-resources")
        self.assertEqual(
            declared[-1]["catalogue_url"],
            "https://icfmp.github.io/Bible-Resources/catalog/v1/catalog.json"
        )
        for replacement in (
            "(*DEFAULT_PROVIDERS, dynamic_provider())",
            "(*DEFAULT_PROVIDERS, BIBLE_RESOURCES, BIBLE_RESOURCES)",
            "(*INVALID_PROVIDER_LIST, BIBLE_RESOURCES)",
        ):
            source = BIBLE_PROVIDERS.replace(
                "(*DEFAULT_PROVIDERS, BIBLE_RESOURCES)", replacement
            )
            with self.subTest(expression=replacement), self.assertRaises(ValueError):
                declared_providers(source)

    def test_own_curated_catalogue_is_not_a_stock_sword_upstream(self):
        config = deepcopy(self.config)
        own = next(p for p in config["external_sources"]
                   if p["id"] == "bible-resources")
        self.assertEqual(own["kind"], "curated_catalogue")
        report = compare(config, self.sources)
        self.assertEqual(report["status"], "in_sync", report["errors"])
        own["catalogue_url"] = "https://example.invalid/catalog.json"
        report = compare(config, self.sources)
        self.assertIn("external: bible-resources.catalogue_url differs from Bible",
                      report["errors"])

    def test_literal_dataset_urls(self):
        self.assertEqual(literal_constant(REFERENCE, "DOWNLOAD_URL"),
                         "https://a.openbible.info/data/cross-references.zip")

    def test_external_sources_are_not_fetched_as_sword(self):
        providers = [{"id": "crosswire", "enabled": True, "base_url": "https://test.invalid/"}]
        result = check(providers, [], {}, external_sources=self.config["external_sources"],
                       fetch_catalog=lambda _: {}, fetch_conf=lambda *_: {})
        self.assertEqual(result["providers"]["crosswire"]["status"], "ok")
        self.assertEqual(result["external_sources"]["youversion"]["status"], "inventory_only")
        self.assertEqual(result["external_sources"]["openbible-topics"]["kind"], "dataset")

    def test_provider_registry_classification(self):
        sword, external = expected_inventory(self.sources)
        self.assertEqual(set(sword), {"crosswire", "andbible-extra", "andbible", "step", "ebible"})
        self.assertEqual(set(external), {"youversion", "openbible-cross-references", "openbible-topics", "bible-resources"})


if __name__ == "__main__":
    unittest.main()
