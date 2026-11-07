"""Offline, deterministic source-priority and edition-identity tests.

Never access the network or download copyrighted resource content.
"""
from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_updates import parse_conf
from select_sources import select_sources, scan


def provider(pid, enabled=True):
    return {"id": pid, "name": pid, "kind": "sword", "enabled": enabled}


PROVIDERS = [provider("crosswire"), provider("ebible"), provider("step"),
             provider("andbible"), provider("andbible-extra")]
PRIORITY = {"schema_version": 1,
            "priority": [p["id"] for p in PROVIDERS]}
EMPTY_REGISTRY = {"schema_version": 1, "editions": []}


def conf(module_id, title="The Bible", lang="en", category="bible", version="1.0",
         versification="KJV"):
    return {"module_id": module_id, "description": title, "language": lang,
            "category": category, "version": version, "versification": versification,
            "conf_sha256": "a" * 64}


def inventory(**providers):
    return {pid: {item["module_id"].casefold(): item for item in values}
            for pid, values in providers.items()}


def registry(*editions):
    return {"schema_version": 1, "editions": list(editions)}


def verified(*aliases, edition_id="kjv-1769-en", category="bible", language="en"):
    return {
        "edition_id": edition_id,
        "category": category,
        "language": language,
        "verified_by": "reviewer",
        "evidence_url": "https://example.org/edition-evidence",
        "sources": [{"provider": pid, "module_id": mid} for pid, mid in aliases],
    }


class SourcePriorityTests(unittest.TestCase):
    def select(self, catalogs, aliases=None, statuses=None, providers=None):
        return select_sources(
            providers or PROVIDERS, catalogs,
            aliases if aliases is not None else EMPTY_REGISTRY,
            PRIORITY, statuses,
        )

    def test_real_policy_and_registry_have_valid_shape(self):
        config = json.loads((ROOT / "config/source-priority.json").read_text())
        sources = json.loads((ROOT / "config/upstreams.json").read_text())
        identities = json.loads((ROOT / "config/edition-identities.json").read_text())
        output = select_sources(sources["providers"], {}, identities, config,
                                {pid: "unavailable" for pid in config["priority"]})
        self.assertFalse(output["complete"])
        self.assertEqual(config["priority"], [p["id"] for p in PROVIDERS])

    def test_verified_same_edition_prefers_crosswire_over_ebible(self):
        catalogs = inventory(crosswire=[conf("KJV")], ebible=[conf("KJV", version="3.0")])
        identity = registry(verified(("crosswire", "KJV"), ("ebible", "KJV")))
        result = self.select(catalogs, identity, {pid: "ok" for pid in PRIORITY["priority"]})
        self.assertEqual(result["selected"][0]["source"]["provider"], "crosswire")
        self.assertEqual(result["skipped_lower_priority"][0]["source"]["provider"], "ebible")
        self.assertTrue(result["complete"])

    def test_prefer_provider_rank_not_version_number(self):
        catalog = inventory(ebible=[conf("A", version="99.0")],
                            step=[conf("B", version="1.0")])
        identity = registry(verified(("ebible", "A"), ("step", "B")))
        statuses = {pid: "ok" for pid in PRIORITY["priority"]}
        result = self.select(catalog, identity, statuses)
        self.assertEqual(result["selected"][0]["source"]["provider"], "ebible")

    def test_unverified_same_id_is_blocked_not_silently_deduplicated(self):
        catalog = inventory(crosswire=[conf("KJV")], step=[conf("KJV")])
        result = self.select(catalog, statuses={pid: "ok" for pid in PRIORITY["priority"]})
        self.assertEqual(result["selected"], [])
        self.assertEqual(result["counts"]["blocked_groups"], 2)
        self.assertTrue(all("same_module_id_unverified" in r["reasons"]
                            for r in result["blocked"]))
        self.assertFalse(result["complete"])

    def test_title_match_different_ids_needs_review(self):
        catalog = inventory(crosswire=[conf("KJV")], step=[conf("KJVDifferentName")])
        result = self.select(catalog, statuses={pid: "ok" for pid in PRIORITY["priority"]})
        self.assertFalse(result["selected"])
        self.assertTrue(all("same_title_identity_review" in x["reasons"]
                            for x in result["blocked"]))

    def test_different_edition_and_language_remain_distinct(self):
        catalog = inventory(crosswire=[conf("KJV", title="King James", lang="en")],
                            ebible=[conf("KJVA", title="King James 1611", lang="en"),
                                    conf("Martin", title="King James", lang="fr")])
        result = self.select(catalog, statuses={pid: "ok" for pid in PRIORITY["priority"]})
        self.assertEqual(len(result["selected"]), 3)
        self.assertFalse(result["blocked"])

    def test_verified_distinct_editions_can_share_display_title(self):
        catalog = inventory(crosswire=[conf("A", title="Same title")],
                            ebible=[conf("B", title="Same title")],
                            step=[conf("C", title="Same title")],
                            andbible=[conf("D", title="Same title")])
        identities = registry(
            verified(("crosswire", "A"), ("step", "C"), edition_id="edition-one"),
            verified(("ebible", "B"), ("andbible", "D"), edition_id="edition-two"),
        )
        result = self.select(catalog, identities, {pid: "ok" for pid in PRIORITY["priority"]})
        self.assertEqual(len(result["selected"]), 2)
        self.assertEqual(len(result["skipped_lower_priority"]), 2)
        self.assertEqual(len(result["blocked"]), 0)

    def test_lower_used_if_higher_confirmed_absent(self):
        catalog = inventory(crosswire=[], ebible=[conf("A")])
        identities = registry(verified(("crosswire", "A"), ("ebible", "A")))
        result = self.select(catalog, identities, {pid: "ok" for pid in PRIORITY["priority"]})
        self.assertEqual(result["selected"][0]["source"]["provider"], "ebible")

    def test_unavailable_higher_blocks_lower_instead_of_fallback(self):
        catalog = inventory(ebible=[conf("A")])
        statuses = {pid: "ok" for pid in PRIORITY["priority"]}
        statuses["crosswire"] = "unavailable"
        result = self.select(catalog, statuses=statuses)
        self.assertEqual(len(result["selected"]), 0)
        self.assertIn("higher_priority_catalog_unavailable", result["blocked"][0]["reasons"])

    def test_unavailable_lower_does_not_undo_preferred_crosswire_selection(self):
        catalog = inventory(crosswire=[conf("A")])
        statuses = {pid: "ok" for pid in PRIORITY["priority"]}
        statuses["andbible-extra"] = "unavailable"
        result = self.select(catalog, statuses=statuses)
        self.assertEqual(len(result["selected"]), 1)
        self.assertFalse(result["complete"])
        self.assertEqual(result["unavailable_providers"], ["andbible-extra"])

    def test_disabled_provider_is_excluded(self):
        sources = [dict(p, enabled=False) if p["id"] == "crosswire" else p for p in PROVIDERS]
        catalog = inventory(ebible=[conf("A")])
        statuses = {pid: "ok" for pid in PRIORITY["priority"]}
        statuses["crosswire"] = "disabled"
        result = self.select(catalog, statuses=statuses, providers=sources)
        self.assertEqual(result["selected"][0]["source"]["provider"], "ebible")

    def test_verified_identity_conflicting_language_blocks(self):
        catalog = inventory(crosswire=[conf("A", lang="fr")],
                            ebible=[conf("B", lang="en")])
        identities = registry(verified(("crosswire", "A"), ("ebible", "B")))
        result = self.select(catalog, identities, {pid: "ok" for pid in PRIORITY["priority"]})
        self.assertIn("verified_identity_metadata_mismatch", result["blocked"][0]["reasons"])

    def test_reviewer_cannot_reuse_one_alias_in_two_editions(self):
        identity = registry(
            verified(("crosswire", "A"), ("ebible", "B"), edition_id="edition-one"),
            verified(("crosswire", "A"), ("step", "C"), edition_id="edition-two"),
        )
        with self.assertRaisesRegex(ValueError, "conflicting source alias"):
            self.select({}, identity)

    def test_pending_verification_does_not_authorize_de_duplication(self):
        identity = verified(("crosswire", "A"), ("ebible", "B"))
        identity["verified_by"] = "PENDING"
        with self.assertRaisesRegex(ValueError, "verified reviewer"):
            self.select({}, registry(identity))

    def test_provider_priority_must_include_all_sword_sources(self):
        incorrect = {"schema_version": 1, "priority": ["crosswire", "ebible"]}
        with self.assertRaisesRegex(ValueError, "priority"):
            select_sources(PROVIDERS, {}, EMPTY_REGISTRY, incorrect)

    def test_unknown_driver_blocked(self):
        item = conf("X", category="unknown")
        result = self.select(inventory(crosswire=[item]),
                             statuses={pid: "ok" for pid in PRIORITY["priority"]})
        self.assertIn("unsupported_module_category", result["blocked"][0]["reasons"])

    def test_scan_does_not_fetch_any_module_text(self):
        def fake_fetch(p):
            if p["id"] == "crosswire":
                return {"kjv": conf("KJV")}
            return {}
        result = scan(PROVIDERS, EMPTY_REGISTRY, PRIORITY, fetch_catalog=fake_fetch)
        self.assertEqual(len(result["selected"]), 1)
        self.assertTrue(result["complete"])
        self.assertIn("No", result["note"])

    def test_no_candidates_with_unavailable_provider_is_incomplete(self):
        statuses = {pid: "ok" for pid in PRIORITY["priority"]}
        statuses["ebible"] = "unavailable"
        result = self.select({}, statuses=statuses)
        self.assertFalse(result["complete"])

    def test_metadata_parser_exposes_source_fields_but_not_content(self):
        data = (b"[MHCC]\nModDrv=zCom\nDescription=Matthew Henry Concise Commentary\n"
                b"Lang=en\nVersification=KJV\nSourceType=OSIS\n"
                b"TextSource=An example edition\nDistributionLicense=Public Domain\nVersion=1.5\n")
        item = parse_conf(data)
        self.assertEqual(item["category"], "commentary")
        self.assertEqual(item["description"], "Matthew Henry Concise Commentary")
        self.assertEqual(item["text_source"], "An example edition")
        self.assertEqual(item["source_type"], "OSIS")

    def test_id_match_with_different_kinds_is_a_collision_not_a_duplicate(self):
        catalog = inventory(crosswire=[conf("SAME", category="bible", title="Bible")],
                            ebible=[conf("SAME", category="commentary", title="Commentary")])
        result = self.select(catalog, statuses={pid: "ok" for pid in PRIORITY["priority"]})
        self.assertEqual(len(result["blocked"]), 2)
        self.assertFalse(result["skipped_lower_priority"])


if __name__ == "__main__":
    unittest.main()
