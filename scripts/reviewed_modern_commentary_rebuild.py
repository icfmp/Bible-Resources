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



def verify_header_only_revision(directory, root, metadata, plan, proof, artifact):
    """Bind a reversible OSIS work-header repair to the prior approved source.

    The historical modernization and binary attestations remain unchanged.
    Only the order of complete header metadata elements and the explicitly
    listed distribution configuration fields may change.
    """
    from lxml import etree
    revision = plan["header_revision"]
    if proof.get("header_revision") != revision or artifact.get("header_revision") != revision:
        raise ValueError("Header revision binding differs")
    previous = revision["previous_version"]
    current = metadata["version"]
    if not all(isinstance(v, str) and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", v) for v in (previous,current)) or tuple(map(int,previous.split("."))) >= tuple(map(int,current.split("."))):
        raise ValueError("Invalid header revision version sequence")
    ident = metadata["id"]
    language = metadata["language"]
    if not re.fullmatch(r"[a-z0-9-]+",ident) or not re.fullmatch(r"[a-z]{2,3}",language):
        raise ValueError("Unsafe revision identity")
    edition = root/"sources/cleaned/commentaries"/language/ident
    archive = edition/"editorial/evidence"/("release-"+previous)
    def pinned(name, field):
        path = archive/name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 1_000_000:
            raise ValueError("Prior release evidence missing")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != revision[field]:
            raise ValueError("Prior release evidence hash differs: "+name)
        return raw
    old_plan = json.loads(pinned("review-manifest.json","previous_review_sha256"))
    old_proof = json.loads(pinned("SOURCE_VALIDATION.json","previous_proof_sha256"))
    old_artifact = json.loads(pinned("RELEASE_ARTIFACT_PROOF.json","previous_artifact_sha256"))
    old_meta = json.loads(pinned("metadata.json","previous_metadata_sha256"))
    old_conf = pinned("module.conf","previous_conf_sha256")
    receipt_name = revision["receipt_name"]
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]+\.json",receipt_name):
        raise ValueError("Unsafe header revision evidence path")
    receipt_path = edition/"editorial/evidence"/receipt_name
    if receipt_path.is_symlink() or not receipt_path.is_file() or receipt_path.stat().st_size > 1_000_000:
        raise ValueError("Missing revision evidence")
    receipt_raw = receipt_path.read_bytes()
    if hashlib.sha256(receipt_raw).hexdigest() != revision["receipt_sha256"]:
        raise ValueError("Header revision evidence checksum differs")
    results = json.loads(receipt_raw)["results"]
    ledger = results["MODERN_HEADER_TRIAL"]
    native = results["MODERN_HEADER_NATIVE_TRIAL"]
    if (ledger["source_sha256"] != old_plan["source_approved_osis_sha256"]
            or ledger["candidate_sha256"] != revision["candidate_source_sha256"]
            or ledger["official_schema_validated"] is not True
            or ledger["source_reversible"] is not True
            or ledger["body_byte_identical"] is not True
            or ledger["brnp"]["finding_count"] != 0
            or native["all_raw_equal"] is not True or native["links_equal"] is not True
            or any(native[k] != [] for k in ("changed_keys","extra_keys","missing_keys"))):
        raise ValueError("Missing exact source/native revision evidence")
    source = edition/(ident+".osis.xml")
    if source.is_symlink() or not source.is_file() or source.stat().st_size > 128*1024*1024:
        raise ValueError("Missing corrected canonical source")
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ledger["candidate_sha256"]:
        raise ValueError("Corrected canonical source SHA256 differs")
    offset = ledger["offset"]
    before, after = ledger["before"].encode(), ledger["after"].encode()
    if (type(offset) is not int or offset < 0 or len(before) != len(after)
            or raw[offset:offset+len(after)] != after or offset+len(after)>raw.index(b"</header>")):
        raise ValueError("Header correction is not localized to metadata")
    restored = raw[:offset]+before+raw[offset+len(after):]
    if hashlib.sha256(restored).hexdigest()!=ledger["source_sha256"]:
        raise ValueError("Header reversal does not recover approved source")
    ns = "{http://www.bibletechnologies.net/2003/OSIS/namespace}"
    parser = etree.XMLParser(resolve_entities=False,no_network=True,load_dtd=False)
    a,b=(etree.fromstring(value,parser) for value in (restored,raw))
    def split_header(tree):
        text=tree.find(ns+"osisText")
        header=text.find(ns+"header")
        if header is None or len(header)!=1 or header[0].tag!=ns+"work":
            raise ValueError("Unsupported work-header shape")
        work=header[0]
        children=sorted(etree.tostring(e) for e in work)
        for e in list(work):work.remove(e)
        return children,etree.tostring(tree)
    if split_header(a)!=split_header(b):
        raise ValueError("Header repair changes metadata content or authorial body")
    # Historical exact approval remains pinned. Only release metadata may vary.
    if plan != dict(old_plan,version=current,header_revision=revision):
        raise ValueError("Historical editorial review changed")
    if proof != dict(old_proof,curated_version=current,header_revision=revision):
        raise ValueError("Historical source proof changed")
    old_title=old_meta["title"]["en"]
    new_title=revision["new_display_name"]
    if not isinstance(new_title,str) or not new_title.strip() or any(c in new_title for c in "\r\n"):
        raise ValueError("Unsafe display name")
    new_meta=dict(old_meta,version=current,title=dict(old_meta["title"],en=new_title))
    if metadata != new_meta:
        raise ValueError("Unrelated metadata changed")
    conf_name="mods.d/"+metadata["sword_id"].lower()+".conf"
    if hashlib.sha256(old_conf).hexdigest()!=old_artifact["payload_sha256"][conf_name]:
        raise ValueError("Previous native configuration differs")
    expected=old_conf
    source_url="https://github.com/icfmp/Bible-Resources/blob/main/sources/cleaned/commentaries/"+language+"/"+ident+"/"+ident+".osis.xml"
    for before,after in (
        (("Version="+previous+"\n").encode(),("Version="+current+"\n").encode()),
        (("Description="+old_title+"\n").encode(),("Description="+new_title+"\n").encode()),
        (("TextSource="+revision["old_text_source"]+"\n").encode(),("TextSource="+source_url+"\n").encode()),
    ):
        if expected.count(before)!=1:
            raise ValueError("Ambiguous configuration change")
        expected=expected.replace(before,after,1)
    conf_path=directory/"payload"/conf_name
    if conf_path.is_symlink() or conf_path.read_bytes()!=expected:
        raise ValueError("Configuration changed beyond authorized metadata")
    expected_artifact=dict(old_artifact,header_revision=revision,payload_sha256=dict(old_artifact["payload_sha256"]))
    expected_artifact["payload_sha256"][conf_name]=hashlib.sha256(expected).hexdigest()
    if artifact!=expected_artifact:
        raise ValueError("Historical native binary proof changed")


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
        plan = load(root / "config/commentary-rebuilds" / (ident + ".json"))
        proof = load(directory / "SOURCE_VALIDATION.json")
        artifact = load(directory / "RELEASE_ARTIFACT_PROOF.json")
        if "header_revision" in plan:
            verify_header_only_revision(directory,root,metadata,plan,proof,artifact)
        decisions = load(root / "sources/cleaned/commentaries/en/hmcc-modern/"
                         "editorial/evidence/OWNER_EDITORIAL_DECISIONS_2026-11-19.json")
        if (plan.get("schema_version") != 1
                or plan.get("status") != "owner_authorized_for_release"
                or plan.get("module_id") != ident
                or plan.get("sword_id") != metadata["sword_id"]
                or plan.get("version") != metadata["version"]
                or plan.get("source_module") != "MHCC 0.1.1"
                or plan.get("original_native_sha256") !=
                    decisions.get("source_native_corpus_sha256")
                or not sha(plan.get("source_approved_osis_sha256"))
                or plan.get("source_decisions") !=
                    "sources/cleaned/commentaries/en/hmcc-modern/editorial/evidence/OWNER_EDITORIAL_DECISIONS_2026-11-19.json"
                or plan.get("approved_link_cases") != 15
                or plan.get("approved_link_destinations") != 28
                or plan.get("historical_authorial_restorations") != 2
                or plan.get("release_id") != "HMCCModern"
                or metadata["quality"]["edition"] != "reader_optimized"):
            raise ValueError("Source/edition, counted corrections or release identity changed")
        links = decisions.get("link_cases")
        if (not isinstance(links, list) or len(links) != 15
                or sum(len(v["approved_derived_destinations"]) for v in links) != 28
                or len(decisions.get("ccel_only_sections", [])) != 2):
            raise ValueError("Owner-reviewed source decisions no longer match")
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
            "approved_link_cases": 15,
            "approved_link_destinations": 28,
            "historical_authorial_restorations": 2,
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
