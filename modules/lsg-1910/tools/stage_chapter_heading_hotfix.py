#!/usr/bin/env python3
"""Stage the validated LSG 1.0.2 chapter-heading candidate in a PR only.

The original publisher source and all past GitHub assets remain immutable.
This module-local replay script requires exact source, complete native text/
note fidelity and official section-heading tests before touching the branch.
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

OLD="1eb474496bef0388da403528ea080da489d8b4d980d4b11397ffd8cfe2398a4d"
NEW="c95c02c40de173b3ccdb396e62e917b96f90b12c8aebc82e1f3c7264c4f26c24"
USFX="fe059525d3167c70c22777e6cb6d578eb1e63095904f61fed0a857c4f643ac0e"
OLD_ZIP="c7b7471cba433abf99c84c1a6968a7a07a1d1cb5d021ca3bf6fdb86f6f6adf63"
TAG="lsg-1.0.2"
VERSION="1.0.2"
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
    candidate=Path("/tmp/lsg-preverse-section-candidate.osis.xml")
    test_payload=Path("/tmp/lsg-chapter-heading-sword/payload")
    receipt=Path("/tmp/lsg-preverse-section-receipt.json")
    native_report=Path("/tmp/lsg-heading-native-receipt.json")
    old_plan_path=ROOT/"config/release-plans/lsg-1.0.1.json"
    old_import_path=ROOT/"config/catalogue-import-lsg-1.0.1.json"
    plan=load(old_plan_path)
    imp=load(old_import_path)
    metadata=load(module/"metadata.json")
    compat=load(module/"SWORD_COMPATIBILITY.json")
    cleanup=load(folder/"CLEANUP_MANIFEST.json")
    source_proof=load(module/"SOURCE_VALIDATION.json")
    norm=load(module/"NORMALIZATION_REPORT.json")
    report=load(receipt)
    native=load(native_report)
    if not (sha(master)==OLD and sha(candidate)==NEW and
      sha(ROOT/"sources/original/bibles/fr/lsg-1910/fraLSG_usfx.zip")==USFX and
      cleanup["cleaned_osis_sha256"]==OLD and metadata["version"]=="1.0.1" and
      compat["source_osis_sha256"]==OLD and
      compat["module_payload_sha256"]==module_payload_digest(module) and
      source_proof["source_sha256"]==OLD and norm["output_sha256"]==OLD and
      plan["tag"]=="lsg-1.0.1" and plan["package_sha256"]==OLD_ZIP and
      imp["release_zip_sha256"]==OLD_ZIP and
      report["original_sha256"]==OLD and report["candidate_sha256"]==NEW and
      report["typed_chapter_first_titles"]==803 and
      report["source_bytes_restorable"] is True and
      native["candidate_sha256"]==NEW and native["source_keys"]==31170 and
      native["native_keys"]==31169 and
      native["chapter_first_headings_now_in_first_verse"]==803 and
      native["scripture_text_mismatches"]==0 and native["note_mismatches"]==0):
        raise SystemExit("Unverified source, old module, or native verse/heading evidence")

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
        one(one(old_conf,"Version=1.0.1","Version=1.0.2"),
            "Bible Resources 1.0.1 SWORD cross-reference filter hotfix",
            "Bible Resources 1.0.2 restored authorial chapter-first headings"),
        encoding="utf-8")

    cleanup.update({
       "previous_approved_cleaned_osis_sha256":OLD,
       "cleaned_osis_sha256":NEW,"final_candidate_osis_sha256":NEW,
       "cleaned_osis_bytes":master.stat().st_size,
       "published_release_provenance":"config/catalogue-import-lsg-1.0.2.json",
       "section_title_overlay_receipt_sha256":sha(receipt),
       "status":"reversible_authorial_chapter_first_headings_pending_publication"})
    save(folder/"CLEANUP_MANIFEST.json",cleanup)
    source_proof["source_sha256"]=NEW
    source_proof["provenance_audit_sha256"]=sha(native_report)
    source_proof["note"]=("Official OSIS validated: 803 existing heading metadata "
      "types specified; all 31,169 native verse texts and 9,751 notes preserved")
    save(module/"SOURCE_VALIDATION.json",source_proof)
    norm["output_sha256"]=NEW
    norm["diff_sha256"]=sha(native_report)
    norm["plan_sha256"]=sha(receipt)
    norm["operations"].append({
        "operation":"annotate_untyped_first_section_headings",
        "count":803,"old_sha256":OLD,"new_sha256":NEW,
        "only_title_type_attributes_added":True})
    norm["review_asserted_by_plan"]="Owner-reported missing chapter-first headings; independently validated source/native candidate PR #551"
    save(module/"NORMALIZATION_REPORT.json",norm)
    compat["source_osis_sha256"]=NEW
    compat["module_payload_sha256"]=module_payload_digest(module)
    compat["full_readback_evidence_sha256"]=sha(native_report)
    compat["text_notes_markup_and_visuals_verified"]=False
    compat["source_to_native_full_body_mismatch_count"]=0
    compat["source_to_native_note_mismatch_count"]=0
    compat["reviewed_by"]="Owner-reported missing headings; 803 exact first-verse titles independently verified PR #551"
    save(module/"SWORD_COMPATIBILITY.json",compat)
    errors=proof_errors(module,"Segond",NEW)
    if errors:raise SystemExit("Stock SWORD native proof failed: "+"; ".join(errors[:8]))

    metadata["version"]=VERSION
    metadata["quality"]["reviewed_by"]="Bible Resources owner — missing chapter-start headings reported; source/native candidate verified PR #551"
    save(module/"metadata.json",metadata)
    profile_source=editorial/"profiles/fr-segond-1910.md"
    card=profile_source.read_text(encoding="utf-8")
    for a,b in (
      ("**Version Bible Resources :** 1.0.1","**Version Bible Resources :** 1.0.2"),
      ("| Version | 1.0.1 |","| Version | 1.0.2 |"),
      ("**Édition numérique :** Bible Resources 1.0.1, novembre 2026.",
       "**Édition numérique :** Bible Resources 1.0.2, novembre 2026.")):
        card=one(card,a,b)
    profile_source.write_text(card,encoding="utf-8")
    profile=load(module/"profiles/fr.json")
    profile["module_version"]=VERSION
    profile["revision"]="2026-11-23.3"
    profile["approval_url"]="https://github.com/icfmp/Bible-Resources/pull/551"
    profile["evidence_urls"]["curated_release"]="https://github.com/icfmp/Bible-Resources/releases/tag/"+TAG
    buf=profile_source.read_bytes()
    profile["source_git_blob_sha1"]=sha1(b"blob "+str(len(buf)).encode()+b"\0"+buf).hexdigest()
    save(module/"profiles/fr.json",profile)

    editorial_file=module/"EDITORIAL.md"
    history=editorial_file.read_text(encoding="utf-8")
    if not history.startswith("# Louis Segond 1910 — Bible Resources 1.0.1"):
        raise SystemExit("Historical editorial record changed")
    editorial_file.write_text(
      "# Louis Segond 1910 — Bible Resources 1.0.2 (unpublished candidate)\n\n"
      "Existing original section headings now carry the OSIS-valid "
      "x-section type where they immediately follow a chapter opening. "
      "Exactly 803 unchanged titles are now part of native verse 1 entries. "
      "All original Scripture, publisher notes and citations are identical. "
      "The known Segond index exception for Mark 10:53 is retained.\n\n"
      "## Earlier approved 1.0.1 editorial record\n\n"+history,encoding="utf-8")

    old_notes=editorial/"releases/LSG-1.0.1.md"
    if not old_notes.is_file():raise SystemExit("Historic 1.0.1 notes missing")
    notes=editorial/"releases/LSG-1.0.2.md"
    if notes.exists():raise SystemExit("Unexpected existing 1.0.2 release notes")
    notes.write_text(
      "# Louis Segond 1910 — Bible Resources 1.0.2\n\n"
      "This update restores **803 original chapter-opening section headings** "
      "to numbered verse 1 entries of the SWORD module, including "
      "Rom 1 « Adresse et salutation » and Rom 2 « Les païens ». "
      "Each source-authored title is marked with OSIS-valid "
      "type=x-section, enabling the standard compiler to store it as a "
      "pre-verse heading instead of inaccessible chapter-intro material. "
      "No title words, verses, notes, cross-references or original source "
      "material were added or removed.\n\n"
      "Full native SWORD comparison: original 31,170 numbered verse IDs "
      "retained, 31,169 populated native Scripture texts and 9,751 notes "
      "unchanged; all 803 headings found at their authorial first verse. "
      "Xiphos is the owner's provisional reference reader; a screenshot "
      "from Bible prompted this correction but the app itself was untouched.\n\n"
      "Known limitations are unchanged: the stock Segond versification "
      "merges original Mark 10:53 into the Mark 10:52 native slot; explicitly "
      "enabling SWORD cross-references can expose note XML in some plain-text "
      "clients (issue #549). The previous 0.1.0, 1.0.0 and 1.0.1 release "
      "assets remain immutable; eBible fraLSG is public domain.\n",
      encoding="utf-8")

    historic=editorial/"releases/LSG-1.0.1-RELEASE-PLAN.json"
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
        with tempfile.TemporaryDirectory(prefix="lsg-1.0.2-preview-") as directory:
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
            newimp["provenance"]["historical_1_0_1_zip_sha256"]=OLD_ZIP
            newimp["provenance"]["first_heading_receipt_sha256"]=sha(receipt)
            newimp["provenance"]["full_native_heading_audit_sha256"]=sha(native_report)
            newimp["editorial_approval"]["scope"]=(
                "Reported and source-verified missing chapter-first headings; "
                "803 existing title types corrected for source-faithful SWORD "
                "rendering. Final public release remains a separate approval.")
            save(ROOT/"config/catalogue-import-lsg-1.0.2.json",newimp)
            newplan=deepcopy(plan)
            newplan.update({
                "tag":TAG,"version":VERSION,"title":"Louis Segond 1910 — 1.0.2",
                "zip_name":"BRLSG1910-1.0.2.zip",
                "package_sha256":zip_sha,"package_size_bytes":zip_bytes,
                "notes_path":"sources/cleaned/bibles/fr/lsg-1910/editorial/releases/LSG-1.0.2.md"})
            newplan["authorization"]["evidence_url"]="https://github.com/icfmp/Bible-Resources/pull/551"
            newplan["authorization"]["reviewed_by"]="Bible Resources owner — missing chapter-first headings issue #550; publication approval still distinct"
            newplan["authorization"]["decision"]=(
                "Source-attested OSIS section-heading markup repair, "
                "803 unchanged titles re-associated to verse one; all Scripture "
                "and notes preserved in independent native SWORD testing")
            save(ROOT/"config/release-plans/lsg-1.0.2.json",newplan)
            catalogue.write_bytes((dist/"catalog/v1/catalog.json").read_bytes())
            result=coverage(ROOT,built=dist)
            if not any(row["tag"]==TAG for _,row in result["planned"]):
                raise SystemExit("New exact 1.0.2 publication route absent")
            approved=approved_release(ROOT,ROOT/"config/release-plans/lsg-1.0.2.json",dist)
            if sha(approved["package"])!=zip_sha:
                raise SystemExit("Approved package has different ZIP bytes")
            inspect_approved_releases(ROOT,("lsg-1910",))
            print(json.dumps({
                "status":"unpublished_v1_0_2_release_branch_candidate",
                "source_sha256":NEW,"zip_sha256":zip_sha,
                "zip_size_bytes":zip_bytes,"headings_native_verse_one":803,
                "text_unchanged":True,"notes_unchanged":True,
                "previous_release_immutable":True,"public_release_created":False},
                sort_keys=True))
    except BaseException:
        if not catalogue.exists():catalogue.write_bytes(old_catalogue)
        raise
    return 0

if __name__=="__main__":
    raise SystemExit(main())
