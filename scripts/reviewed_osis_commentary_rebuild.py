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
        if (r.get("schema_version")!=1 or r.get("status")!="owner_authorized_for_release"
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
        if proof.get("schema_version")!=1 or any(proof.get(k)!=v for k,v in expected.items()):
            raise ValueError("Source/native evidence differs from reviewed plan")
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
        added=b"TextSource=https://gitlab.com/crosswire-bible-society/mhc\\n"
        # A single source URL may be added, never alter the attested original config.
        # Its expected value comes from the original official authoring repository.
        original_url=commit["repository_url"].encode("utf-8")
        added=b"TextSource="+original_url+b"\\n"
        if final_conf.count(added)!=1 or sha256(final_conf.replace(added,b"")).hexdigest()!=original_conf_sha:
            raise ValueError("Metadata edit is not exactly source-reversible")
        if (conf.get("ModDrv") not in ("zCom","zCom4")
                or conf.get("BlockType") not in ("BOOK","CHAPTER","VERSE")):
            raise ValueError("Unsupported commentary driver or compression layout")
        block={"BOOK":"b","CHAPTER":"c","VERSE":"v"}[conf["BlockType"]]
        extension = block+"z"
        directory = "zcom" if conf["ModDrv"]=="zCom" else "zcom4"
        folder=metadata["sword_id"].lower()
        members={"mods.d/"+folder+".conf"}
        members.update("modules/comments/"+directory+"/"+folder+"/"+part+"."+extension+suffix
                       for part in ("nt","ot") for suffix in ("s","v","z"))
        expected_hashes=artifact.get("member_sha256")
        if not isinstance(expected_hashes,dict) or set(expected_hashes)!=members:
            raise ValueError("Incomplete SWORD member inventory")
        payload=module_dir/"payload"
        files={}
        for file in payload.rglob("*"):
            if file.is_symlink():
                raise ValueError("Symlink in published native package")
            if file.is_file():
                files[file.relative_to(payload).as_posix()]=file
        if set(files)!=members:
            raise ValueError("Package membership differs from audited source")
        for relative,file in files.items():
            digest=expected_hashes[relative]
            if not isinstance(digest,str) or len(digest)!=64 or sha256(file.read_bytes()).hexdigest()!=digest:
                raise ValueError("Native payload mismatch: "+relative)
    except (KeyError,ValueError,TypeError,OSError,UnicodeError,AttributeError) as e:
        return [pfx+str(e)]
    return []
