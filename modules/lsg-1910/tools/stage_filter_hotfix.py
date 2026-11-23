#!/usr/bin/env python3
"""Stage LSG 1.0.1 SWORD configuration-only hotfix; never publish by itself."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha1,sha256
import json,sys,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"scripts"))
from stable_sword_refs import module_payload_digest,proof_errors
from build import build
from validate import validate
from catalogue_release_coverage import coverage
from publish_reviewed_release import approved_release
from release_preflight import inspect_approved_releases

SOURCE="1eb474496bef0388da403528ea080da489d8b4d980d4b11397ffd8cfe2398a4d"
USFX="fe059525d3167c70c22777e6cb6d578eb1e63095904f61fed0a857c4f643ac0e"
OLD_ZIP="cc3b57ab0b61476a77b42fa19004956085d7608a974724c770cc2211adc67499"
OLD_CONF="377d95ece763b8f53c1199e9d13970210a394acc898a96f307d066cd56266965"
TAG="lsg-1.0.1"
VERSION="1.0.1"

def sha(path):return sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text(encoding="utf-8"))
def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def replace_one(text,old,new):
    if text.count(old)!=1:raise SystemExit("Ambiguous/missing historical source field: "+old)
    return text.replace(old,new,1)

def main():
    module=ROOT/"modules/lsg-1910"
    payload=module/"payload"
    conf=payload/"mods.d/brlsg1910.conf"
    editorial=ROOT/"sources/cleaned/bibles/fr/lsg-1910/editorial"
    osis=editorial.parent/"lsg-1910.osis.xml"
    metadata_path=module/"metadata.json"
    compat_path=module/"SWORD_COMPATIBILITY.json"
    old_plan_path=ROOT/"config/release-plans/lsg-1.0.0.json"
    old_import_path=ROOT/"config/catalogue-import-lsg-1.0.0.json"
    old_plan=load(old_plan_path)
    original_import=load(old_import_path)
    metadata=load(metadata_path)
    compat=load(compat_path)
    if (sha(osis)!=SOURCE or sha(ROOT/"sources/original/bibles/fr/lsg-1910/fraLSG_usfx.zip")!=USFX
        or sha(conf)!=OLD_CONF or metadata["version"]!="1.0.0"
        or old_plan["tag"]!="lsg-1.0.0" or old_plan["package_sha256"]!=OLD_ZIP
        or original_import["release_zip_sha256"]!=OLD_ZIP
        or compat["source_osis_sha256"]!=SOURCE
        or compat["module_payload_sha256"]!=module_payload_digest(module)):
        raise SystemExit("Published 1.0.0 exact source and package baseline mismatch")

    binaries={key:val for key,val in original_import["files"].items()
              if key.startswith("modules/texts/ztext/brlsg1910/")}
    if len(binaries)!=6 or any(sha(payload/key)!=val for key,val in binaries.items()):
        raise SystemExit("Unexpected native SWORD binary baseline")
    original_conf=conf.read_text(encoding="utf-8")
    fixed=replace_one(original_conf,"GlobalOptionFilter=OSISXRefs",
                      "GlobalOptionFilter=OSISScripref")
    fixed=replace_one(fixed,"Version=1.0.0","Version=1.0.1")
    fixed=replace_one(fixed,"reviewed Bible Resources 1.0.0 candidate",
                      "Bible Resources 1.0.1 SWORD cross-reference filter hotfix")
    conf.write_text(fixed,encoding="utf-8")
    metadata["version"]=VERSION
    metadata["quality"]["reviewed_by"]="Bible Resources project owner — SWORD config-only 1.0.1 fix requested 2026-11-23"
    save(metadata_path,metadata)
    compat["module_payload_sha256"]=module_payload_digest(module)
    save(compat_path,compat)
    errors=proof_errors(module,"Segond",SOURCE)
    if errors:raise SystemExit("Stable SWORD source/index validation failed: "+"; ".join(errors[:8]))

    manifest_path=editorial.parent/"CLEANUP_MANIFEST.json"
    manifest=load(manifest_path)
    if manifest["cleaned_osis_sha256"]!=SOURCE:raise SystemExit("Cleaned master changed")
    manifest["published_release_provenance"]="config/catalogue-import-lsg-1.0.1.json"
    manifest["status"]="reviewed_lsg_1_0_1_configuration_only_hotfix"
    save(manifest_path,manifest)

    card_path=editorial/"profiles/fr-segond-1910.md"
    card=card_path.read_text(encoding="utf-8")
    for before,after in [
        ("**Version Bible Resources :** 1.0.0","**Version Bible Resources :** 1.0.1"),
        ("| Version | 1.0.0 |","| Version | 1.0.1 |"),
        ("**Édition numérique :** Bible Resources 1.0.0, novembre 2026.",
         "**Édition numérique :** Bible Resources 1.0.1, novembre 2026.")
    ]:card=replace_one(card,before,after)
    card_path.write_text(card,encoding="utf-8")
    ppath=module/"profiles/fr.json"
    profile=load(ppath)
    profile["module_version"]=VERSION
    profile["revision"]="2026-11-23.2"
    profile["approval_url"]="https://github.com/icfmp/Bible-Resources/pull/548"
    profile["evidence_urls"]["curated_release"]="https://github.com/icfmp/Bible-Resources/releases/tag/"+TAG
    blob=card_path.read_bytes()
    profile["source_git_blob_sha1"]=sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()
    save(ppath,profile)

    historical_plan=editorial/"releases/LSG-1.0.0-RELEASE-PLAN.json"
    if historical_plan.exists():raise SystemExit("Historical release plan already archived")
    historical_plan.write_bytes(old_plan_path.read_bytes())
    old_plan_path.unlink()

    notes=editorial/"releases/LSG-1.0.1.md"
    notes.write_text(
        "# Louis Segond 1910 — Bible Resources 1.0.1\n\n"
        "## Cross-reference rendering hotfix\n\n"
        "Restores the registered libSWORD configuration filter OSISScripref "
        "instead of the invalid OSISXRefs introduced in 1.0.0. The normal "
        "cross-references-disabled mode no longer leaks literal reference XML "
        "into plain Bible reading. The exact 1.0.0 Bible OSIS source, all "
        "six native zText binary members, all 31,170 source verse IDs, "
        "31,169 native verse bodies and all 9,751 notes are unchanged.\n\n"
        "**Known limitation:** when a reader explicitly turns ON the SWORD "
        "Cross-references global option, libSWORD stripText can still expose "
        "note-internal XML reference markup. The standard OFF/default mode "
        "is tested through every native verse; this patch does not claim "
        "full XML-free stripText under an explicit ON setting. The Bible "
        "application source code is not modified.\n\n"
        "This release retains all 1.0.0 editorial improvements, 12 reviewed "
        "citation corrections, 3 introduction decisions, 9,440 linked "
        "reference notes, and the documented Marc 10.53 Segond native "
        "index limitation. No source-absent verse has been introduced. "
        "See the unchanged 1.0.0 release notes for original source/rights.\n\n"
        "All previous public release assets and hashes remain immutable.\n",
        encoding="utf-8")
    ep=module/"EDITORIAL.md"
    record=ep.read_text(encoding="utf-8")
    if not record.startswith("# Louis Segond 1910 — Bible Resources 1.0.0"):
        raise SystemExit("Historical editorial record identity mismatch")
    ep.write_text(
        "# Louis Segond 1910 — Bible Resources 1.0.1\n\n"
        "Module configuration-only hotfix: replace OSISXRefs with the "
        "registered OSISScripref filter. Native binary data and reviewed "
        "Bible source are byte-identical to v1.0.0. Plain-text cross-"
        "reference On rendering remains a known upstream limitation. "
        "Old tagged releases are not rewritten.\n\n"
        "## Historical 1.0.0 editorial record\n\n"+record,encoding="utf-8")
    if sha(osis)!=SOURCE or any(sha(payload/k)!=v for k,v in binaries.items()):
        raise SystemExit("A native binary or source text was changed")

    catalogue_path=ROOT/"catalog/v1/catalog.json"
    previous_catalogue=catalogue_path.read_bytes()
    catalogue_path.unlink()
    try:
        _,problems=validate(ROOT)
        if problems:raise SystemExit("Source and rights validation failed: "+"; ".join(problems[:10]))
        with tempfile.TemporaryDirectory(prefix="lsg-1.0.1-hotfix-") as temp:
            dist=Path(temp)/"dist"
            build(root=ROOT,output=dist)
            zip_path=dist/"sword/packages/BRLSG1910.zip"
            package_hash=sha(zip_path)
            package_size=zip_path.stat().st_size
            members={p.relative_to(payload).as_posix():sha(p)
                     for p in sorted(payload.rglob("*")) if p.is_file()}
            if set(members)!=set(original_import["files"]):
                raise SystemExit("SWORD hotfix package member set changed")
            differing=[k for k in members if members[k]!=original_import["files"][k]]
            if differing!=["mods.d/brlsg1910.conf"]:
                raise SystemExit("More than the SWORD configuration changed: "+str(differing))
            new_import=deepcopy(original_import)
            new_import["release_tag"]=TAG
            new_import["release_zip_sha256"]=package_hash
            new_import["files"]=members
            new_import["provenance"]["historical_1_0_0_zip_sha256"]=OLD_ZIP
            new_import["editorial_approval"]["scope"]=(
                "Owner-requested OSISScripref configuration-only 1.0.1 fix "
                "of SWORD cross-reference default-off rendering, preserving "
                "all source and native binary bytes.")
            save(ROOT/"config/catalogue-import-lsg-1.0.1.json",new_import)
            plan=deepcopy(old_plan)
            plan.update({
                "tag":TAG,"version":VERSION,"title":"Louis Segond 1910 — 1.0.1",
                "zip_name":"BRLSG1910-1.0.1.zip",
                "package_sha256":package_hash,"package_size_bytes":package_size,
                "notes_path":"sources/cleaned/bibles/fr/lsg-1910/editorial/releases/LSG-1.0.1.md"})
            plan["authorization"]["evidence_url"]="https://github.com/icfmp/Bible-Resources/pull/548"
            plan["authorization"]["decision"]=(
                "Owner-requested 1.0.1 config-only OSISScripref filter "
                "correction, source/native bytes unchanged, default-off "
                "stripText verified, explicit-on limitation disclosed.")
            save(ROOT/"config/release-plans/lsg-1.0.1.json",plan)
            catalogue_path.write_bytes((dist/"catalog/v1/catalog.json").read_bytes())
            checked=coverage(ROOT,built=dist)
            if not any(p["tag"]==TAG for _,p in checked["planned"]):
                raise SystemExit("New release not covered by exact public catalogue")
            verified=approved_release(ROOT,ROOT/"config/release-plans/lsg-1.0.1.json",dist)
            if sha(verified["package"])!=package_hash:
                raise SystemExit("Final deterministic ZIP does not match release")
            inspect_approved_releases(ROOT,("lsg-1910",))
            print(json.dumps({
                "status":"staged_unpublished_1_0_1",
                "source_sha256":SOURCE,"package_sha256":package_hash,
                "package_size_bytes":package_size,
                "only_changed_member":"mods.d/brlsg1910.conf",
                "six_binary_members_unchanged":True,"publication_completed":False
            },sort_keys=True))
    except BaseException:
        if not catalogue_path.exists():catalogue_path.write_bytes(previous_catalogue)
        raise
    return 0

if __name__=="__main__":
    raise SystemExit(main())
