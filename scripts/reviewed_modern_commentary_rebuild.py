"""Review a modern-English derivative of an attested historical SWORD commentary.

This is not a stock-byte or a source-identical OSIS validation route.
The distinct modern manuscripts and approved editorial overlay must be tracked
separately.  Native payload members are bound to a previous successful
compiled/editorial reader build, and publication metadata is explicitly
reviewed.  The signed-off CI record remains a prerequisite, not a substitute
for inspecting the original source and the human publication decision.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from reviewed_compiled_commentary_rebuild import (zcom_payload_paths,
                                                checked_zcom_payload_files)

SHA = re.compile(r"[0-9a-f]{64}\Z")

# Historical owner-reviewed evidence is independently pinned here. Editing
# two mutable JSON manifests together must NOT silently authorize a new set of
# manuscript corrections or a different release plan. A new edition requires
# separate editorial approval and an explicit reviewed pin change.
REVIEWED_MODERN_WITNESSES = {
    "hmcc-modern": {
        "plan_sha256": "9a705aeae3ef4765b9a965ce13ac7e2531d48b7e8e25af83258d316ac09ee958",
        "decisions_path": (
            "work/hmcc-modern/production/"
            "OWNER_EDITORIAL_DECISIONS_2026-11-19.json"
        ),
        "decisions_sha256": "b828124fcfb9825bdcb581e79d9edf9579fdac27f441199c12a309fda21a3101",
    },
}


def _checked_json(path: Path, expected_sha256: str) -> dict:
    """Verify exact bytes before consuming owner-reviewed editorial evidence."""
    if (path.is_symlink() or not path.is_file()
            or path.stat().st_size > 1_000_000):
        raise ValueError("Missing or unsafe pinned evidence JSON")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("Pinned editorial evidence SHA256 differs")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Pinned editorial evidence is not an object")
    return value





def reviewed_modern_commentary_errors(directory: Path, root: Path,
                                     metadata: dict, conf: dict) -> list[str]:
    prefix = f"{directory.name}: [MODERN_COMMENTARY_PROOF_INVALID] "
    try:
        def load(path: Path) -> dict:
            if (path.is_symlink() or not path.is_file()
                    or path.stat().st_size > 1_000_000):
                raise ValueError("Missing or unsafe source-evidence JSON")
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError("Source-evidence JSON must be an object")
            return value

        def sha(value: object) -> bool:
            return isinstance(value, str) and SHA.fullmatch(value) is not None

        ident = metadata["id"]
        if metadata.get("index_audit") != {
            "mode": "reviewed_modern_commentary_rebuild",
            "manifest": f"config/commentary-rebuilds/{ident}.json",
        }:
            raise ValueError("Missing source-bound modern commentary review route")
        witness = REVIEWED_MODERN_WITNESSES.get(ident)
        if witness is None:
            raise ValueError("Unreviewed modern commentary edition")
        plan = _checked_json(root / "config/commentary-rebuilds" /
                             (ident + ".json"), witness["plan_sha256"])
        proof = load(directory / "SOURCE_VALIDATION.json")
        artifact = load(directory / "RELEASE_ARTIFACT_PROOF.json")
        decisions = _checked_json(root / witness["decisions_path"],
                                  witness["decisions_sha256"])
        links = decisions.get("link_cases")
        sections = decisions.get("ccel_only_sections")
        if (not isinstance(links, list) or not isinstance(sections, list)
                or any(not isinstance(case, dict)
                       or not isinstance(case.get("approved_derived_destinations"), list)
                       for case in links)):
            raise ValueError("Malformed pinned source editorial decision counts")
        link_cases = len(links)
        link_destinations = sum(len(case["approved_derived_destinations"])
                                for case in links)
        historical_restorations = len(sections)
        if (plan.get("schema_version") != 1
                or plan.get("status") != "owner_authorized_for_release"
                or plan.get("module_id") != ident
                or plan.get("sword_id") != metadata["sword_id"]
                or plan.get("version") != metadata["version"]
                or plan.get("source_module") != "MHCC 0.1.1"
                or plan.get("original_native_sha256") !=
                    decisions.get("source_native_corpus_sha256")
                or not sha(plan.get("source_approved_osis_sha256"))
                or plan.get("source_decisions") != witness["decisions_path"]
                or plan.get("approved_link_cases") != link_cases
                or plan.get("approved_link_destinations") != link_destinations
                or plan.get("historical_authorial_restorations") != historical_restorations
                or plan.get("release_id") != "HMCCModern"
                or metadata["quality"]["edition"] != "reader_optimized"):
            raise ValueError("Source/edition, counted corrections or release identity changed")
        auth = plan.get("authorization", {})
        if (auth.get("approved_by") != "Bible Resources project owner"
                or auth.get("approval_url") !=
                    "https://github.com/icfmp/Bible-Resources/pull/272"
                or not isinstance(auth.get("decision"), str)
                or len(auth["decision"]) < 50):
            raise ValueError("No edition-specific owner publication instruction")
        rights = metadata["rights"]
        if (rights.get("license") != conf.get("DistributionLicense")
                or not rights.get("redistribution_allowed")
                or not rights.get("derivatives_allowed")
                or plan.get("underlying_public_domain_source") !=
                    "CrossWire MHCC 2.0 — Public Domain / Copy Freely"
                or plan.get("derivative_rights_status") !=
                    "owner_authorized_distribution_no_relicensing_of_underlying_source"
                or conf.get("SourceType") != "OSIS"
                or conf.get("ModDrv") != "zCom"
                or conf.get("BlockType") != "CHAPTER"
                or conf.get("Versification") != "KJV"
                or conf.get("Encoding") != "UTF-8"
                or conf.get("Version") != metadata["version"]):
            raise ValueError("Edition-specific rights, format or native metadata mismatch")
        expected = {
            "status": "validated",
            "source_kind": "reviewed_modern_commentary_rebuild",
            "curated_module_id": metadata["sword_id"],
            "curated_version": metadata["version"],
            "original_native_sha256": plan["original_native_sha256"],
            "source_approved_osis_sha256": plan["source_approved_osis_sha256"],
            "source_reader_run_url": plan["source_reader_run_url"],
            "approved_link_cases": link_cases,
            "approved_link_destinations": link_destinations,
            "historical_authorial_restorations": historical_restorations,
            "compiled_zcom_members_identical_to_accepted_QA": True,
            "original_source_unchanged": True,
            "modern_manuscripts_unchanged": True,
        }
        if proof.get("schema_version") != 1 or any(
                proof.get(k) != v for k, v in expected.items()):
            raise ValueError("Reviewed source-to-binary attestation differs")
        if (artifact.get("schema_version") != 1
                or artifact.get("source_artifact_id") !=
                    plan["source_artifact_id"]
                or artifact.get("source_run_id") != plan["source_run_id"]
                or artifact.get("source_archive_sha256") !=
                    plan["source_archive_sha256"]
                or artifact.get("source_archive_size_bytes") !=
                    plan["source_archive_size_bytes"]
                or artifact.get("source_approved_osis_sha256") !=
                    plan["source_approved_osis_sha256"]
                or not sha(artifact.get("source_archive_sha256"))
                or artifact.get("source_binary_data_identical") is not True):
            raise ValueError("Exact approved QA artifact not bound to final binary")
        expected_members = artifact.get("payload_sha256")
        folder = metadata["sword_id"].lower()
        members = zcom_payload_paths(metadata["sword_id"], conf["BlockType"])
        if not isinstance(expected_members, dict) or set(expected_members) != members:
            raise ValueError("Expected seven native zCom payload members missing")
        actual = checked_zcom_payload_files(
            directory / "payload", metadata["sword_id"], conf["BlockType"])
        for name in sorted(members):
            digest = expected_members[name]
            if not sha(digest) or hashlib.sha256(actual[name].read_bytes()).hexdigest() != digest:
                raise ValueError("Compiled member SHA256 differs: " + name)
        source_members = artifact.get("original_QA_six_data_member_sha256")
        if not isinstance(source_members, dict) or len(source_members) != 6:
            raise ValueError("Missing six independent source binary member hashes")
        for name in members - {"mods.d/" + folder + ".conf"}:
            if source_members.get(name) != expected_members[name]:
                raise ValueError("Modern approved source binary not preserved")
    except (KeyError, ValueError, TypeError, OSError, AttributeError) as exc:
        return [prefix + str(exc)]
    return []
