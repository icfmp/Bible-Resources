"""Verify pinned authorial-OSIS rebuilds distributed as native SWORD commentaries.

This source-neutral release binding checks the authenticated historical authoring
source contract, full native attestation metadata and every retained binary
member. Full textual and reader parity is performed by separately identified
source/native workflows: a metadata receipt is never a substitute for that audit.
"""
from pathlib import Path
from hashlib import sha256
import json
import re

from reviewed_compiled_commentary_rebuild import (
    commentary_payload_paths, checked_commentary_payload_files)


def _verify_revision(module_dir, root, metadata, conf, r, original, proof, artifact, load):
    """Verify a later, exact attribute-only authorial-OSIS maintenance release."""
    from lxml import etree
    from hashlib import sha256
    def digest(data):
        return sha256(data).hexdigest()
    def file_sha(path):
        if path.is_symlink() or not path.is_file():
            raise ValueError("Unsafe revision evidence path")
        return digest(path.read_bytes())
    language = metadata["language"]
    if not re.fullmatch(r"[a-z]{2,3}", language) or not re.fullmatch(r"[a-z0-9-]+", module_dir.name):
        raise ValueError("Unsafe revision identity")
    rev = r["revision"]
    previous_version = rev["previous_version"]
    if not all(re.fullmatch(r"\d+\.\d+\.\d+", v) for v in (previous_version, metadata["version"])) or tuple(map(int,previous_version.split("."))) >= tuple(map(int,metadata["version"].split("."))):
        raise ValueError("Invalid previous revision version")
    edition = root / "sources/cleaned/commentaries" / language / module_dir.name
    old = edition / "editorial/evidence" / ("release-" + previous_version)
    previous = load(old/"review-manifest.json")
    prior_cleanup = load(old/"CLEANUP_MANIFEST.json")
    if file_sha(old/"review-manifest.json") != rev["previous_review_sha256"] or previous["version"] != previous_version or previous["status"] != "owner_authorized_for_release":
        raise ValueError("Previous review identity mismatch")
    for key in ("module_id","sword_id","versification","driver","block_type","original_manifest","original_module_id","original_version","original_archive_sha256","original_authoring_commit","original_authoring_osis_sha256","source_commentary_bodies","source_commentary_word_tokens","introduction_native_entries","opaque_top_native_entries","reviewed_reference_target_repairs"):
        if r[key] != previous[key]:
            raise ValueError("Changed original source contract: " + key)
    if file_sha(old/"CLEANUP_MANIFEST.json") != rev["previous_cleanup_sha256"] or prior_cleanup["approved_cleaned_sha256"] != rev["previous_source_sha256"]:
        raise ValueError("Previous source identity mismatch")
    current = edition / rev["source_name"]
    if current.parent != edition or not re.fullmatch(r"[a-z0-9-]+\.osis\.xml",current.name) or current.is_symlink() or current.stat().st_size > 128*1024*1024:
        raise ValueError("Unsafe canonical source")
    raw = current.read_bytes()
    if digest(raw) != rev["candidate_source_sha256"]:
        raise ValueError("Canonical source hash mismatch")
    cleanup = load(edition/"CLEANUP_MANIFEST.json")
    if cleanup["approved_cleaned_sha256"] != digest(raw) or cleanup["source_original_sha256"] != r["original_authoring_osis_sha256"]:
        raise ValueError("Cleanup provenance mismatch")
    evidence_dir = edition / "editorial/evidence" / ("release-" + metadata["version"])
    receipt_path = evidence_dir/"incremental-native-reader.json"
    ev = load(receipt_path)
    if file_sha(receipt_path) != rev["evidence_sha256"] or ev["previous_source_sha256"] != rev["previous_source_sha256"] or ev["candidate_source_sha256"] != digest(raw):
        raise ValueError("Incremental evidence identity mismatch")
    for name in ("source_reversible","all_prior_native_keys_accounted_for","all_other_native_markup_and_text_exact","all_prior_native_link_edges_unchanged","opaque_top_equal","official_schema_validated","reader_checks_passed"):
        if ev[name] is not True:
            raise ValueError("Incomplete native/reader evidence: "+name)
    if ev["brnp_findings"] != 0 or ev["missing_keys"] != []:
        raise ValueError("Unresolved candidate validation")
    expected_hashes = artifact["member_sha256"]
    if ev["payload_sha256"] != expected_hashes or ev["candidate_native_sha256"] != rev["candidate_native_sha256"] or ev["previous_native_sha256"] != rev["previous_native_sha256"]:
        raise ValueError("Native evidence differs from payload or review")
    stages = ev["source_attribute_stages"]
    if not isinstance(stages,list) or not 1 <= len(stages) <= 10:
        raise ValueError("Invalid attribute ledger")
    aliases = []
    for stage in reversed(stages):
        if digest(raw) != stage["output_sha256"]:
            raise ValueError("Invalid attribute-stage output")
        edits = stage["edits"]
        if not 1 <= len(edits) <= 500 or stage["attribute"] not in ("osisRef","osisID"):
            raise ValueError("Invalid attribute edits")
        last = len(raw)
        for edit in reversed(edits):
            offset = edit["output_offset"]
            before, after = edit["before"].encode(), edit["after"].encode()
            if type(offset) is not int or offset < 0 or offset+len(after)>last or raw[offset:offset+len(after)] != after:
                raise ValueError("Unreplayable or overlapping attribute edit")
            prefix = stage["attribute"].encode()+b'="'
            if raw[offset-len(prefix):offset] != prefix or raw[offset+len(after):offset+len(after)+1] != b'"':
                raise ValueError("Edit is not an exact XML attribute value")
            if stage["attribute"] == "osisRef":
                if before.strip()!=after or before==after:
                    raise ValueError("Non-whitespace cross-reference correction")
            else:
                ids=before.decode().split()
                alias=edit["alias"]
                if not ids or ids[0]!=edit["master"] or after.decode().split()!=[alias,*ids] or alias in ids:
                    raise ValueError("Invalid scope alias")
                aliases.append([alias,ids[0]])
            raw=raw[:offset]+before+raw[offset+len(after):]
            last=offset
        if digest(raw)!=stage["input_sha256"]:
            raise ValueError("Attribute ledger does not reverse exactly")
    if digest(raw)!=rev["previous_source_sha256"] or sorted(aliases)!=sorted(ev["aliases"]) or len({a[0] for a in aliases})!=len(aliases):
        raise ValueError("Previous source reconstruction or alias scope mismatch")
    if r["numbered_native_entries"]!=previous["numbered_native_entries"]+len(aliases) or sorted(ev["extra_keys"])!=sorted([["K",a[0]] for a in aliases]):
        raise ValueError("Native entry counts do not reconcile")
    # Both source files are strict XML and every node's text/tail/tag and all
    # non-target attributes remain exact. The exact byte-ledger also protects
    # comments, original formatting and attribute serialization.
    parser=lambda:etree.XMLParser(resolve_entities=False,load_dtd=False,no_network=True)
    prev=etree.fromstring(raw,parser())
    curr=etree.parse(str(current),parser()).getroot()
    ns="{http://www.bibletechnologies.net/2003/OSIS/namespace}"
    for a,b in zip(prev.iter(),curr.iter(),strict=True):
        if a.tag!=b.tag or a.text!=b.text or a.tail!=b.tail:
            raise ValueError("Source content or structure changed")
        if a.attrib!=b.attrib:
            x,y=dict(a.attrib),dict(b.attrib)
            attr="osisRef" if a.tag==ns+"reference" else "osisID" if a.tag==ns+"verse" else None
            if attr is None or attr not in x or attr not in y:
                raise ValueError("Unexpected edited node")
            old_value,new_value=x.pop(attr),y.pop(attr)
            if x!=y or (attr=="osisRef" and old_value.strip()!=new_value) or (attr=="osisID" and [new_value.split()[0],old_value.split()[0]] not in aliases):
                raise ValueError("Unreviewed source attribute change")
    if proof.get("schema_version")!=2 or proof.get("revision")!=rev or proof.get("candidate_native_corpus_sha256")!=rev["candidate_native_sha256"] or proof.get("candidate_source_sha256")!=rev["candidate_source_sha256"]:
        raise ValueError("Incomplete revision source validation")
    if artifact.get("schema_version")!=2 or artifact.get("revision")!=rev or artifact.get("full_native_corpus_readback_equal") is not True or artifact.get("source_binary_payload_byte_identical") is not False or artifact.get("six_compiled_data_members_byte_identical_to_review_artifact") is not True:
        raise ValueError("Incomplete revised artifact binding")
    for k,v in {"source_workflow_run":r["candidate_artifact_source_run"],"artifact_id":r["candidate_artifact_id"],"review_zip_sha256":r["candidate_artifact_sha256"],"review_zip_bytes":r["candidate_artifact_bytes"],"original_authoring_osis_sha256":r["original_authoring_osis_sha256"]}.items():
        if artifact.get(k)!=v:
            raise ValueError("Artifact identity mismatch")
    previous_conf = ev["previous_conf"]
    final_conf = (module_dir/"payload/mods.d"/(metadata["sword_id"].lower()+".conf")).read_bytes()
    old_conf=previous_conf.encode()
    if digest(old_conf)!=load(old/"RELEASE_ARTIFACT_PROOF.json")["member_sha256"]["mods.d/"+metadata["sword_id"].lower()+".conf"]:
        raise ValueError("Prior config hash mismatch")
    # The only permitted revision metadata differences are the version and
    # display description. All driver, rights, path and provenance bytes stay.
    def strip_display(data):
        return b"\n".join(l for l in data.split(b"\n") if not l.startswith((b"Version=",b"Description=")))
    if strip_display(old_conf)!=strip_display(final_conf):
        raise ValueError("Unreviewed native config change")


def reviewed_osis_commentary_errors(module_dir, root, metadata, conf):
    pfx = f"{module_dir.name}: [OSIS_REBUILD_PROOF_INVALID] "
    try:
        def load(path):
            if path.is_symlink() or not path.is_file() or path.stat().st_size>1_000_000:
                raise ValueError("Missing, unsafe, or oversized source attestation")
            return json.loads(path.read_text(encoding="utf-8"))
        index=metadata.get("index_audit",{})
        path=index.get("manifest")
        if index.get("mode")!="reviewed_osis_commentary_rebuild" or not isinstance(path,str) or path!=f"config/commentary-rebuilds/{module_dir.name}.json":
            raise ValueError("Unexpected per-edition review manifest")
        r=load(root/path)
        original_path=r.get("original_manifest")
        if (not isinstance(original_path,str) or not original_path.startswith("config/commentary-intake/")
                or ".." in Path(original_path).parts or not original_path.endswith(".json")):
            raise ValueError("Unsafe original source declaration")
        original=load(root/original_path)
        proof=load(module_dir/"SOURCE_VALIDATION.json")
        artifact=load(module_dir/"RELEASE_ARTIFACT_PROOF.json")
        commit=original["commentary_source"]["original_authoring_osis"]
        rights=metadata["rights"]
        auth=r.get("authorization",{})
        if (r.get("schema_version") not in (1,2) or r.get("status")!="owner_authorized_for_release"
                or r.get("module_id")!=metadata["id"] or r.get("sword_id")!=metadata["sword_id"]
                or r.get("version")!=metadata["version"] or r.get("versification")!=metadata["versification"]
                or r.get("driver")!=conf.get("ModDrv") or r.get("block_type")!=conf.get("BlockType")
                or r.get("original_module_id")!=original["module_id"]
                or r.get("original_version")!=original["version"]
                or r.get("original_archive_sha256")!=original["archive_sha256"]
                or r.get("original_authoring_commit")!=commit["observed_upstream_commit_sha"]
                or r.get("original_authoring_osis_sha256")!=commit["authoring_osis_sha256"]
                or original["source_page_url"]!=metadata["origin"]["url"]
                or metadata["sword_id"]!=original["module_id"]
                or conf.get("Version")!=metadata["version"]
                or conf.get("Versification")!=metadata["versification"]
                or conf.get("SourceType")!="OSIS"
                or conf.get("DistributionLicense")!=rights["license"]
                or not rights.get("redistribution_allowed") or not rights.get("derivatives_allowed")
                or metadata["quality"]["status"]!="approved"):
            raise ValueError("Review, source, version, license or SWORD identity mismatch")
        if (auth.get("approved_by")!="Bible Resources project owner"
                or not isinstance(auth.get("scope"),str) or len(auth["scope"])<40
                or not isinstance(auth.get("evidence_url"),str) or re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/[1-9][0-9]*",auth["evidence_url"]) is None):
            raise ValueError("Missing explicit editorial authorization")
        expected={
            "original_authoring_osis_sha256":r["original_authoring_osis_sha256"],
            "original_compiled_zip_sha256":r["original_archive_sha256"],
            "release_artifact_sha256":r["candidate_artifact_sha256"],
            "source_attestation_run":r["native_evidence_url"],
            "original_commentary_bodies":r["source_commentary_bodies"],
            "original_commentary_word_tokens":r["source_commentary_word_tokens"],
            "numbered_native_entries":r["numbered_native_entries"],
            "introduction_entries":r["introduction_native_entries"],
            "opaque_top_entries":r["opaque_top_native_entries"],
            "reviewed_cross_reference_target_repairs":r["reviewed_reference_target_repairs"],
            "status":"validated","source_kind":"reviewed_osis_commentary_rebuild",
            "review_manifest":path,"curated_module_id":metadata["sword_id"],
            "curated_version":metadata["version"],"full_native_corpus_readback_equal":True}
        if proof.get("schema_version")!=r["schema_version"] or any(proof.get(k)!=v for k,v in expected.items()):
            raise ValueError("Source/native evidence differs from reviewed plan")
        if r["schema_version"]==2:
            _verify_revision(module_dir, root, metadata, conf, r, original, proof, artifact, load)
        else:
            if (artifact.get("schema_version")!=1 or artifact.get("source_workflow_run")!=r["candidate_artifact_source_run"]
                    or artifact.get("artifact_id")!=r["candidate_artifact_id"]
                    or artifact.get("review_zip_sha256")!=r["candidate_artifact_sha256"]
                    or artifact.get("review_zip_bytes")!=r["candidate_artifact_bytes"]
                    or artifact.get("original_authoring_osis_sha256")!=r["original_authoring_osis_sha256"]
                    or artifact.get("source_binary_payload_byte_identical") is not False
                    or artifact.get("six_compiled_data_members_byte_identical_to_review_artifact") is not True
                    or artifact.get("full_native_corpus_readback_equal") is not True):
                raise ValueError("Authenticated artifact identity or native proof differs")
            edit=artifact.get("metadata_only_conf_delta",{})
            original_conf_sha=artifact.get("original_review_member_conf_sha256")
            if (not isinstance(original_conf_sha,str) or len(original_conf_sha)!=64
                    or edit.get("operation")!="add TextSource entry following SourceType=OSIS"
                    or edit.get("original_conf_sha256")!=original_conf_sha):
                raise ValueError("Missing exact reversible metadata-only .conf edit")
            final_conf=(module_dir/"payload"/"mods.d"/(metadata["sword_id"].lower()+".conf")).read_bytes()
            # A single source URL may be added, never alter the attested original config.
            # Its expected value comes from the original official authoring repository.
            original_url=commit["repository_url"].encode("utf-8")
            added=b"TextSource="+original_url+b"\n"
            if final_conf.count(added)!=1 or sha256(final_conf.replace(added,b"")).hexdigest()!=original_conf_sha:
                raise ValueError("Metadata edit is not exactly source-reversible")
        if (conf.get("ModDrv") not in ("zCom","zCom4")
                or conf.get("BlockType") not in ("BOOK","CHAPTER","VERSE")):
            raise ValueError("Unsupported commentary driver or compression layout")
        members = commentary_payload_paths(
            metadata["sword_id"], conf["BlockType"], conf["ModDrv"])
        expected_hashes = artifact.get("member_sha256")
        if not isinstance(expected_hashes, dict) or set(expected_hashes) != members:
            raise ValueError("Incomplete SWORD member inventory")
        files = checked_commentary_payload_files(
            module_dir / "payload", metadata["sword_id"],
            conf["BlockType"], conf["ModDrv"])
        for relative,file in files.items():
            digest=expected_hashes[relative]
            if not isinstance(digest,str) or len(digest)!=64 or sha256(file.read_bytes()).hexdigest()!=digest:
                raise ValueError("Native payload mismatch: "+relative)
    except (KeyError,ValueError,TypeError,OSError,UnicodeError,AttributeError) as e:
        return [pfx+str(e)]
    return []
