#!/usr/bin/env python3
"""Stage exact source-audited Darby 0.1.1 in a PR. Never publish or overwrite old releases."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
from zipfile import ZipFile

from build import build
from stable_sword_refs import module_payload_digest
from validate import validate

OLD="5910669e5eeb85d2ba06a4602918ce71d6773f36d64502bbdf7f96fff0585f15"
NEW="631f97956ba1b83def91fdba84f83ff9dcb0486a4097e5102a9b3a937f0abba6"
ORIGINAL="2204629e3efb3024dceb392780ef5e61f4296ea832c90e3dd2a5c3224179c1d3"
CORRECTED="35eb23c62eefdcda9a94d6a493df0bf32d5af1bc6ccc2132e495091d7771406d"
APPROVAL="https://github.com/icfmp/Bible-Resources/issues/241#issuecomment-6875143143"
TAG="darby-jnd-2024-0.1.1"
MEMBERS={"mods.d/brjnd2024.conf"} | {
    f"modules/texts/ztext/brjnd2024/{side}.{ext}"
    for side in ("ot","nt") for ext in ("bzs","bzv","bzz")
}

def hash_bytes(raw): return sha256(raw).hexdigest()

def read(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size>4_000_000:
        raise ValueError("Unsafe/missing staged file "+str(path))
    result=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result,dict): raise ValueError("Expected JSON object")
    return result

def write(path,value):
    if path.is_symlink(): raise ValueError("Refusing symlink")
    path.write_text(json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

def require(predicate,message):
    if not predicate: raise ValueError(message)

def stage(root,archive,metadata_path,audit_path,dist):
    root=root.resolve()
    module=root/"modules/darby-jnd-2024"
    auth=read(root/"config/darby-0.1.1-release-authorization.json")
    require(auth=={
        "schema_version":1,"status":"owner_authorized_for_stable_0_1_1_after_exact_source_and_reader_checks",
        "module_id":"BRJND2024","version":"0.1.1","release_tag":TAG,
        "source_osis_sha256":ORIGINAL,"compiler_input_osis_sha256":CORRECTED,
        "private_final_zip_sha256":NEW,"prior_immutable_release_zip_sha256":OLD,
        "owner_approval_url":APPROVAL,"preserve_previous_release_assets":True,"published":False,
    },"Exact owner authorization missing")
    metadata=read(metadata_path)
    audit=read(audit_path)
    require(hash_bytes(audit_path.read_bytes())==metadata.get("full_source_native_audit_sha256"),
            "Full native audit receipt is not the recorded bytes")
    expected={
        "status":"reproducible_private_final_module_id_0_1_1_preflight_verified",
        "private_final_candidate_sword_zip_sha256":NEW,
        "old_immutable_release_zip_sha256":OLD,
        "old_publisher_source_sha256":ORIGINAL,
        "new_compiler_source_osis_sha256":CORRECTED,
        "independently_inspected_final_module_id":"BRJND2024",
        "final_conf_version":"0.1.1",
        "source_verse_keys":31166,"source_note_count":6340,
        "native_verse_index_verified":True,
        "all_521_division_metadata_source_native_pairs_verified":True,
        "binary_data_unchanged_during_identity_promotion":True,
        "original_publisher_source_unchanged":True,
        "old_0_1_0_release_untouched":True,
        "published":False,
        "owner_release_approval":False
    }
    require(all(metadata.get(k)==v for k,v in expected.items()),
            "Exact reviewed native preflight differs")
    require(audit.get("status")=="repaired_osis_to_native_sword_full_text_notes_research_passed"
            and audit.get("publisher_original_sha256")==ORIGINAL
            and audit.get("private_compiled_osis_sha256")==CORRECTED
            and audit.get("source_key_count")==31166
            and audit.get("source_note_count")==6340
            and audit.get("official_osis_xsd_conforming") is True
            and audit.get("original_unedited_osis_bytes_preserved") is True
            and audit.get("original_notes_unchanged_except_approved_navigation_targets") is True,
            "Original BPC full-corpus source or schema was not verified")
    markers=audit.get("research_full_source_native_editorial_division_metadata") or {}
    require(markers.get("source_marker_count")==521
            and markers.get("native_marker_count")==521
            and markers.get("source_and_native_all_marker_types_levels_and_host_verses_equal") is True
            and markers.get("all_displayable_marker_attributes_absent") is True,
            "All source editorial markers must remain as native nondisplay metadata")
    counts=(audit.get("native_result") or {}).get("source_to_compiled_counts") or {}
    require(all(counts.get(k)==v for k,v in {
        "numbered_verse_nonspace_main_text_equal":31166,
        "note_body_equal_after_whitespace_folding":6340,
        "note_original_caller_label_equal":6340,
        "note_nonspace_anchor_equal":6340,
        "note_explicit_target_sequence_equal":6340}.items()),"Native text/note parity failed")
    require(archive.name=="BRJND2024-0.1.1.zip"
            and not archive.is_symlink() and archive.is_file()
            and hash_bytes(archive.read_bytes())==NEW,
            "Final private ZIP not identical to accepted Xiphos/AndBible candidate")
    with ZipFile(archive) as z:
        names=z.namelist()
        require(len(names)==7 and set(names)==MEMBERS and z.testzip() is None,
                "Invalid final SWORD ZIP inventory")
        payload={name:z.read(name) for name in MEMBERS}
    require(payload["mods.d/brjnd2024.conf"]==(root/"config/darby-0.1.1.conf").read_bytes(),
            "Final SWORD conf not exactly the reviewed 0.1.1 metadata")
    native_hashes=metadata.get("six_ztext_member_hashes")
    require(isinstance(native_hashes,dict)
            and set(native_hashes)==MEMBERS-{"mods.d/brjnd2024.conf"}
            and all(hash_bytes(payload[k])==v for k,v in native_hashes.items()),
            "Six SWORD native data members differ from accepted audit")
    old=read(module/"RELEASE_PROVENANCE.json")
    manifest=read(module/"metadata.json")
    require(manifest.get("version")=="0.1.0" and manifest.get("sword_id")=="BRJND2024"
            and old.get("release_tag")=="darby-jnd-2024-0.1.0"
            and old.get("release_zip_sha256")==OLD
            and old.get("original_publisher_osis_sha256")==ORIGINAL,
            "Cannot overwrite unverified or different previous module")
    previous=old.get("complete_release_member_sha256")
    require(isinstance(previous,dict) and set(previous)==MEMBERS,
            "Original seven file hashes missing")
    for n,h in previous.items():
        old_member=module/"payload"/n
        require(not old_member.is_symlink() and old_member.is_file()
                and hash_bytes(old_member.read_bytes())==h,"Old 0.1.0 payload drift detected")
    for n,raw in payload.items():
        target=module/"payload"/n
        require(target.is_file() and not target.is_symlink(),"Unknown target payload file")
        target.write_bytes(raw)
    audit_sha=hash_bytes(audit_path.read_bytes())
    manifest["version"]="0.1.1"
    manifest["quality"]["reviewed_by"]="Bible Resources project owner, release #241 (2026-11-14)"
    write(module/"metadata.json",manifest)
    proof=read(module/"SOURCE_VALIDATION.json")
    proof["source_sha256"]=CORRECTED
    proof["provenance_audit_sha256"]=audit_sha
    proof["note"]="Publisher original immutable; technical overlay passed pinned OSIS schema."
    write(module/"SOURCE_VALIDATION.json",proof)
    sword=read(module/"SWORD_COMPATIBILITY.json")
    sword["source_osis_sha256"]=CORRECTED
    sword["module_payload_sha256"]=module_payload_digest(module)
    sword["reviewed_by"]="Bible Resources project owner, release #241 (2026-11-14)"
    sword["new_exact_final_id_native_receipt_sha256"]=hash_bytes(metadata_path.read_bytes())
    write(module/"SWORD_COMPATIBILITY.json",sword)
    norm=read(module/"NORMALIZATION_REPORT.json")
    norm["output_sha256"]=CORRECTED
    norm["provenance_audit_sha256"]=audit_sha
    norm["operations"] += [
        {"kind":"preserve_original_subject_division_signs_as_nondisplay_metadata","count":521},
        {"kind":"remove_verified_xml_formatting_indentation_spans","count":4690}]
    norm["review_asserted_by_plan"]="Bible Resources project owner, issue #241 (2026-11-14)"
    norm["plan_sha256"]=hash_bytes(json.dumps({
        "old_plan":norm["plan_sha256"],"operations":norm["operations"],
        "original":ORIGINAL,"corrected":CORRECTED,"authorization":APPROVAL},
        sort_keys=True).encode("utf-8"))
    norm["diff_sha256"]=hash_bytes(json.dumps({
        "markers":audit.get("research_division_overlay_receipt",{}),
        "spaces":audit.get("research_paragraph_whitespace_overlay_receipt",{})},
        sort_keys=True).encode("utf-8"))
    write(module/"NORMALIZATION_REPORT.json",norm)
    differences=read(module/"NORMALIZATION_DIFF_MANIFEST.json")
    differences["final_corrected_osis_sha256"]=CORRECTED
    differences["source_attested_audit_sha256"]=audit_sha
    differences["original_all_authorial_characters_unchanged"]=False
    differences["original_division_marks_preserved_reversibly_as_metadata"]=521
    differences["original_textcritical_star_preserved_inline"]=1
    differences["source_formatting_indent_spans_removed"]=4690
    differences["prose_and_punctuation_unchanged_except_nondisplay_division_signs"]=True
    write(module/"NORMALIZATION_DIFF_MANIFEST.json",differences)
    editorial=module/"EDITORIAL.md"
    editorial.write_text(editorial.read_text(encoding="utf-8")
        +"\n## Maintenance update 0.1.1 — 2026-11-14\n\n"
        +"Owner release authorization: "+APPROVAL+". Original BPC OSIS untouched. "
        +"All 31,166 verses and 6,340 notes preserved. All 521 original subject/stanza "
        +"division stars now represented in reversible, nondisplayed OSIS metadata; "
        +"one textual-critical star stays inline. 4,690 machine XML indentation spans "
        +"removed without changing textual words or poetic formatting. "
        +"Source/native and Xiphos/AndBible QA is in docs/evidence/darby-2024-0.1.1-final-reader-qa.md. "
        +"The original tagged 0.1.0 GitHub release remains immutable and available for rollback.\n",
        encoding="utf-8")
    write(module/"SOURCE_AUDIT.json",audit)
    modules,errors=validate(root)
    require(not errors,"Staged provenance validation failed: "+"; ".join(errors[:10]))
    require(not dist.exists() and not dist.is_symlink() and dist.parent.is_dir(),
            "Unsafe canonical build output directory")
    build(root=root,output=dist,base_url="https://icfmp.github.io/Bible-Resources/")
    catalog=read(dist/"catalog/v1/catalog.json")
    entries=[x for x in catalog["modules"] if x["sword_id"]=="BRJND2024"]
    require(len(entries)==1 and entries[0]["version"]=="0.1.1",
            "Wrong published catalogue version")
    prior_catalog=read(root/"catalog/v1/catalog.json")
    require([e for e in prior_catalog["modules"] if e["sword_id"]!="BRJND2024"]
            ==[e for e in catalog["modules"] if e["sword_id"]!="BRJND2024"],
            "Unrelated catalogued resources changed")
    built_zip=dist/"sword/packages/BRJND2024.zip"
    canonical_hash=hash_bytes(built_zip.read_bytes())
    require(entries[0]["download"]["sha256"]==canonical_hash,
            "Generated canonical SWORD ZIP and catalogue checksum disagree")
    shutil.copyfile(dist/"catalog/v1/catalog.json",root/"catalog/v1/catalog.json")
    write(module/"RELEASE_PROVENANCE.json",{
        "status":"source_and_native_attested_release_candidate",
        "published":False,
        "release_tag":TAG,
        "release_zip_sha256":canonical_hash,
        "release_zip_bytes":built_zip.stat().st_size,
        "complete_release_member_sha256":dict(sorted(
            (n,hash_bytes(raw)) for n,raw in payload.items())),
        "original_publisher_osis_sha256":ORIGINAL,
        "corrected_candidate_osis_sha256":CORRECTED,
        "full_native_audit_sha256":audit_sha,
        "final_private_zip_sha256":NEW,
        "six_ztext_payload_files_byte_identical_to_full_native_audit":True,
        "promoted_and_public_zip_member_bytes_identical":True,
        "public_zip_format":"canonical_Bible_Resources_catalogue_build",
        "prior_immutable_release_tag":"darby-jnd-2024-0.1.0",
        "prior_immutable_release_zip_sha256":OLD,
        "owner_publication_authorization_url":APPROVAL,
        "full_source_verse_count":31166,"full_source_note_count":6340,
        "original_editorial_division_metadata_count":521,
    })
    _,errors=validate(root)
    require(not errors,"Final 0.1.1 validation failed: "+"; ".join(errors[:10]))
    return {"status":"0_1_1_staged_for_protected_review_not_published",
            "private_zip_sha256":NEW,"canonical_release_zip_sha256":canonical_hash,
            "canonical_release_zip_bytes":built_zip.stat().st_size}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument("--private-final-zip",required=True,type=Path)
    p.add_argument("--private-receipt",required=True,type=Path)
    p.add_argument("--native-audit",required=True,type=Path)
    p.add_argument("--canonical-dist",required=True,type=Path)
    p.add_argument("--receipt",required=True,type=Path)
    a=p.parse_args()
    result=stage(a.repo,a.private_final_zip,a.private_receipt,a.native_audit,a.canonical_dist)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("Private exact final 0.1.1 ZIP staged; canonical public checksum:",result["canonical_release_zip_sha256"])
    print("NOT YET PUBLISHED; awaiting protected PR and real public download verification")

if __name__=="__main__":
    main()
