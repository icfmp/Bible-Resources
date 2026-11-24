#!/usr/bin/env python3
"""Stage the validated LSG 1.0.3 empty-paragraph candidate in a PR only.

The original publisher source and all past GitHub assets remain immutable.
This module-local replay script requires exact source, complete native text/
note fidelity and real Xiphos checks before touching the branch.
"""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha1,sha256
from pathlib import Path
import json,shutil,sys,tempfile

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"scripts"))
from stable_sword_refs import module_payload_digest,proof_errors
from validate import validate
from build import build
from catalogue_release_coverage import coverage
from publish_reviewed_release import approved_release
from release_preflight import inspect_approved_releases

OLD="2b8342a67d8e97b433670450fe9dd9e58917a7fcfc0cb4d321882ca8219dc3bd"
NEW="cf867c35a55208726f5e0d57c15555b2947f6e799ecbc1996204e5120f3235f0"
USFX="fe059525d3167c70c22777e6cb6d578eb1e63095904f61fed0a857c4f643ac0e"
OLD_ZIP="547d5b953c3a3720bf21bed0e48d515e1d9c581dc419bd4b0af5593286180f01"
TAG="lsg-1.0.3"
VERSION="1.0.3"
NATIVE="modules/texts/ztext/brlsg1910"

def sha(p):return sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding="utf-8"))
def save(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
def one(s,a,b):
    if s.count(a)!=1:raise SystemExit("Unexpected historical version field: "+a)
    return s.replace(a,b,1)

def main():
    module=ROOT/"modules/lsg-1910"
    payload=module/"payload"
    conf=payload/"mods.d/brlsg1910.conf"
    folder=ROOT/"sources/cleaned/bibles/fr/lsg-1910"
    editorial=folder/"editorial"
    master=folder/"lsg-1910.osis.xml"
    candidate=Path("/tmp/lsg-1.0.3-candidate.osis.xml")
    test_payload=Path("/tmp/paragraph-native/payload")
    receipt=Path("/tmp/empty-paragraph-review/overlay.json")
    native_report=Path("/tmp/empty-paragraph-review/native.json")
    old_plan_path=ROOT/"config/release-plans/lsg-1.0.2.json"
    old_import_path=ROOT/"config/catalogue-import-lsg-1.0.2.json"
    plan=load(old_plan_path)
    imp=load(old_import_path)
    metadata=load(module/"metadata.json")
    compat=load(module/"SWORD_COMPATIBILITY.json")
    cleanup=load(folder/"CLEANUP_MANIFEST.json")
    source_proof=load(module/"SOURCE_VALIDATION.json")
    norm=load(module/"NORMALIZATION_REPORT.json")
    report=load(receipt)
    native=load(native_report)
    gui=load(Path("/tmp/empty-paragraph-review/xiphos.json"))
    gates = {
      "old_approved_master_sha256": sha(master)==OLD,
      "new_candidate_sha256": sha(candidate)==NEW,
      "publisher_USFX_sha256": sha(ROOT/"sources/original/bibles/fr/lsg-1910/fraLSG_usfx.zip")==USFX,
      "old_cleanup_source_sha256": cleanup["cleaned_osis_sha256"]==OLD,
      "old_metadata_version": metadata["version"]=="1.0.2",
      "old_SWORD_proof_source_sha256": compat["source_osis_sha256"]==OLD,
      "old_SWORD_payload_sha256": compat["module_payload_sha256"]==module_payload_digest(module),
      "old_validation_source_sha256": source_proof["source_sha256"]==OLD,
      "old_normalization_output_sha256": norm["output_sha256"]==OLD,
      "old_release_tag": plan["tag"]=="lsg-1.0.2",
      "old_release_plan_zip_sha256": plan["package_sha256"]==OLD_ZIP,
      "old_catalogue_import_zip_sha256": imp["release_zip_sha256"]==OLD_ZIP,
      "overlay_source_sha256": report["source_sha256"]==OLD,
      "overlay_candidate_sha256": report["candidate_sha256"]==NEW,
      "overlay_count": report["removed_redundant_empty_paragraphs"]==8,
      "overlay_reversible": report["exact_inverse_verified"] is True,
      "overlay_no_other_changes": report["no_other_xml_changes"] is True,
      "native_receipt_candidate_sha256": native["source_osis_sha256"]==NEW,
      "native_receipt_source_count": native["original_authorial_verse_count"]==31170,
      "native_content_parity": native["numbered_slot_text_and_note_parity_verified"] is True,
      "native_structure_parity": native["source_native_body_boundary_positions"]["all_book_body_nonspace_and_boundary_events_equal"] is True,
      "native_target_parity": native["explicit_note_target_index_addressability"]["all_original_explicit_targets_index_addressable"] is True,
      "gui_source": gui["source_sha256"]==NEW,
      "gui_reading_witnesses": gui["all_eight_title_and_verse_witnesses"] is True,
      "gui_content_comparison": len(gui["comparisons"])==8 and all(v["nonspace_clipboard_equal"] for v in gui["comparisons"].values()),
      "native_member_hashes": all(sha(test_payload/name)==digest for name,digest in native["candidate_payload_member_sha256"].items()),
    }
    failures = [name for name, ok in gates.items() if not ok]
    if failures:
        raise SystemExit("Pinned LSG staging acceptance gates failed: "+", ".join(failures))

    old_data={name:val for name,val in imp["files"].items()
              if name.startswith(NATIVE+"/")}
    original_dir=payload/NATIVE
    updated_dir=test_payload/NATIVE
    if (len(old_data)!=6 or
        {p.name for p in updated_dir.iterdir() if p.is_file()}!=
        {Path(name).name for name in old_data} or
        any(sha(payload/name)!=val for name,val in old_data.items())):
        raise SystemExit("Unexpected old/new compressed SWORD module member identities")
    for name in sorted(old_data):
        shutil.copyfile(updated_dir/Path(name).name,payload/name)
    master.write_bytes(candidate.read_bytes())
    if sha(master)!=NEW:raise SystemExit("Staged source identity changed")
    old_conf=conf.read_text(encoding="utf-8")
    if ("GlobalOptionFilter=OSISScripref" not in old_conf or
        "GlobalOptionFilter=OSISHeadings" not in old_conf or
        "GlobalOptionFilter=OSISXRefs" in old_conf):
        raise SystemExit("SWORD filter regression")
    conf.write_text(
        one(one(old_conf,"Version=1.0.2","Version=1.0.3"),
            "Bible Resources 1.0.2 restored authorial chapter-first headings",
            "Bible Resources 1.0.3 removed eight redundant empty paragraphs"),
        encoding="utf-8")

    cleanup.update({
       "previous_approved_cleaned_osis_sha256":OLD,
       "cleaned_osis_sha256":NEW,"final_candidate_osis_sha256":NEW,
       "cleaned_osis_bytes":master.stat().st_size,
       "published_release_provenance":"config/catalogue-import-lsg-1.0.3.json",
       "empty_paragraph_overlay_receipt_sha256":sha(receipt),
       "status":"reversible_redundant_empty_paragraph_cleanup_pending_publication"})
    save(folder/"CLEANUP_MANIFEST.json",cleanup)
    source_proof["source_sha256"]=NEW
    source_proof["provenance_audit_sha256"]=sha(native_report)
    source_proof["note"]=("Official OSIS validated; eight redundant empty paragraphs removed; all 31,169 native texts, 9,751 notes, 4,542 titles and 3,228 remaining paragraph spans verified")
    save(module/"SOURCE_VALIDATION.json",source_proof)
    norm["output_sha256"]=NEW
    norm["diff_sha256"]=sha(native_report)
    norm["plan_sha256"]=sha(receipt)
    norm["operations"].append({
        "operation":"remove_reviewed_redundant_empty_paragraphs",
        "count":8,"old_sha256":OLD,"new_sha256":NEW,
        "exact_inverse_verified":True})
    norm["review_asserted_by_plan"]="Owner-requested empty paragraph cleanup #565; independent native and GUI checks"
    save(module/"NORMALIZATION_REPORT.json",norm)
    compat["source_osis_sha256"]=NEW
    compat["module_payload_sha256"]=module_payload_digest(module)
    compat["full_readback_evidence_sha256"]=sha(native_report)
    compat["text_notes_markup_and_visuals_verified"]=False
    compat["source_to_native_full_body_mismatch_count"]=0
    compat["source_to_native_note_mismatch_count"]=0
    compat["reviewed_by"]="Source-attested redundant paragraph cleanup #565; full structural comparison"
    save(module/"SWORD_COMPATIBILITY.json",compat)
    errors=proof_errors(module,"Segond",NEW)
    if errors:raise SystemExit("Stock SWORD native proof failed: "+"; ".join(errors[:8]))

    metadata["version"]=VERSION
    metadata["quality"]["reviewed_by"]="Bible Resources owner — requested redundant paragraph cleanup #565; independent native and GUI checks"
    save(module/"metadata.json",metadata)
    profile_source=editorial/"profiles/fr-segond-1910.md"
    card=profile_source.read_text(encoding="utf-8")
    for a,b in (
      ("**Version Bible Resources :** 1.0.2","**Version Bible Resources :** 1.0.3"),
      ("| Version | 1.0.2 |","| Version | 1.0.3 |"),
      ("**Édition numérique :** Bible Resources 1.0.2, novembre 2026.",
       "**Édition numérique :** Bible Resources 1.0.3, novembre 2026.")):
        card=one(card,a,b)
    profile_source.write_text(card,encoding="utf-8")
    profile=load(module/"profiles/fr.json")
    profile["module_version"]=VERSION
    profile["revision"]="2026-11-24.1"
    profile["approval_url"]="https://github.com/icfmp/Bible-Resources/issues/565"
    profile["evidence_urls"]["curated_release"]="https://github.com/icfmp/Bible-Resources/releases/tag/"+TAG
    buf=profile_source.read_bytes()
    profile["source_git_blob_sha1"]=sha1(b"blob "+str(len(buf)).encode()+b"\0"+buf).hexdigest()
    save(module/"profiles/fr.json",profile)

    editorial_file=module/"EDITORIAL.md"
    history=editorial_file.read_text(encoding="utf-8")
    editorial_file.write_text(
      "# Louis Segond 1910 — Bible Resources 1.0.3 (unpublished candidate)\n\n"
      "Eight redundant, bare empty paragraphs removed after source USFM review. "
      "All source words, notes, titles, inline annotations and remaining paragraph "
      "and poetry positions preserved. Original publisher files remain immutable.\n\n"
      "## Earlier approved 1.0.2 editorial record\n\n"+history,encoding="utf-8")
    notes=editorial/"releases/LSG-1.0.3.md"
    if notes.exists():raise SystemExit("Unexpected existing release notes")
    notes.write_text(
      "# Louis Segond 1910 — Bible Resources 1.0.3\n\n"
      "Remove eight redundant empty paragraphs before Luke 6:20 and Rev 2:1, 2:8, "
      "2:12, 2:18, 3:1, 3:7 and 3:14, after exact original USFM review. "
      "The preceding titles and actual following paragraphs remain unchanged. "
      "All other source bytes are preserved; exact inverse verified.\n\n"
      "Independent native comparison: 31,170 original verse IDs, 31,169 native "
      "slots, 9,751 notes, 4,542 titles, 3,228 paragraphs, 23,991 poetry lines "
      "and 1,014 line groups. Existing reviewed Mark 10:53 merge unchanged. "
      "All eight sites checked in real Xiphos; pixel-level whitespace not certified. "
      "Optional filter rendering issue #549 remains separate.\n\n"
      "Evidence: #565 and source-bound receipts in editorial/releases. "
      "Previous releases and original publisher archives remain immutable.\n", encoding="utf-8")
    for name,file in (("OVERLAY",receipt),("NATIVE",native_report),("XIPHOS",Path("/tmp/empty-paragraph-review/xiphos.json")),
                      ("SCHEMA",Path("/tmp/empty-paragraph-review/schema.json"))):
        target=editorial/"releases"/("LSG-1.0.3-"+name+".json")
        if target.exists():raise SystemExit("Unexpected existing receipt")
        shutil.copyfile(file,target)

    historic=editorial/"releases/LSG-1.0.2-RELEASE-PLAN.json"
    if historic.exists():raise SystemExit("Historic plan already archived")
    historic.write_bytes(old_plan_path.read_bytes())
    old_plan_path.unlink()
    if any(sha(payload/name)!=sha(updated_dir/Path(name).name)
           for name in old_data):
        raise SystemExit("New compiled SWORD bytes changed after validation")

    catalogue=ROOT/"catalog/v1/catalog.json"
    old_catalogue=catalogue.read_bytes()
    catalogue.unlink()
    try:
        _,problems=validate(ROOT)
        if problems:
            raise SystemExit("Current source/rights/native validation failed: "+"; ".join(problems[:10]))
        with tempfile.TemporaryDirectory(prefix="lsg-1.0.3-preview-") as directory:
            dist=Path(directory)/"dist"
            build(root=ROOT,output=dist)
            zipfile=dist/"sword/packages/BRLSG1910.zip"
            zip_sha=sha(zipfile)
            zip_bytes=zipfile.stat().st_size
            files={p.relative_to(payload).as_posix():sha(p)
                   for p in sorted(payload.rglob("*")) if p.is_file()}
            if set(files)!=set(imp["files"]):
                raise SystemExit("Unexpected binary member structure")
            newimp=deepcopy(imp)
            newimp["release_tag"]=TAG
            newimp["release_zip_sha256"]=zip_sha
            newimp["files"]=files
            newimp["provenance"]["previous_approved_osis_sha256"]=OLD
            newimp["provenance"]["reviewed_candidate_osis_sha256"]=NEW
            newimp["provenance"]["historical_1_0_2_zip_sha256"]=OLD_ZIP
            newimp["provenance"]["empty_paragraph_receipt_sha256"]=sha(receipt)
            newimp["provenance"]["full_native_paragraph_audit_sha256"]=sha(native_report)
            newimp["editorial_approval"]["scope"]=(
                "Reported and source-verified missing chapter-first headings; "
                "803 existing title types corrected for source-faithful SWORD "
                "rendering. Final public release remains a separate approval.")
            save(ROOT/"config/catalogue-import-lsg-1.0.3.json",newimp)
            newplan=deepcopy(plan)
            newplan.update({
                "tag":TAG,"version":VERSION,"title":"Louis Segond 1910 — 1.0.3",
                "zip_name":"BRLSG1910-1.0.3.zip",
                "package_sha256":zip_sha,"package_size_bytes":zip_bytes,
                "notes_path":"sources/cleaned/bibles/fr/lsg-1910/editorial/releases/LSG-1.0.3.md"})
            newplan["authorization"]["evidence_url"]="https://github.com/icfmp/Bible-Resources/issues/565"
            newplan["authorization"]["reviewed_by"]="Bible Resources owner — requested redundant paragraph correction #565; publication approval still distinct"
            newplan["authorization"]["decision"]=(
                "Source-attested OSIS section-heading markup repair, "
                "803 unchanged titles re-associated to verse one; all Scripture "
                "and notes preserved in independent native SWORD testing")
            save(ROOT/"config/release-plans/lsg-1.0.3.json",newplan)
            catalogue.write_bytes((dist/"catalog/v1/catalog.json").read_bytes())
            result=coverage(ROOT,built=dist)
            if not any(row["tag"]==TAG for _,row in result["planned"]):
                raise SystemExit("New exact 1.0.3 publication route absent")
            approved=approved_release(ROOT,ROOT/"config/release-plans/lsg-1.0.3.json",dist)
            if sha(approved["package"])!=zip_sha:
                raise SystemExit("Approved package has different ZIP bytes")
            inspect_approved_releases(ROOT,("lsg-1910",))
            print(json.dumps({
                "status":"unpublished_v1_0_3_release_branch_candidate",
                "source_sha256":NEW,"zip_sha256":zip_sha,
                "zip_size_bytes":zip_bytes,"empty_paragraphs_removed":8,
                "text_unchanged":True,"notes_unchanged":True,
                "previous_release_immutable":True,"public_release_created":False},
                sort_keys=True))
    except BaseException:
        if not catalogue.exists():catalogue.write_bytes(old_catalogue)
        raise
    return 0

if __name__=="__main__":
    raise SystemExit(main())
