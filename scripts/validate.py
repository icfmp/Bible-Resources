#!/usr/bin/env python3
"""Validate metadata, rights and safe SWORD payload structure. Fail closed."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import sys
import re
from jsonschema import Draft202012Validator, FormatChecker
from stable_sword_refs import proof_errors as stable_sword_proof_errors
from published_reference_audit import archived_release_errors

ROOT = Path(__file__).resolve().parents[1]
DRIVERS = {"RawText","zText","RawCom","RawCom4","zCom","zCom4","RawLD","RawLD4","zLD","RawGenBook"}
ALLOWED = {"bible":{"RawText","zText"},"commentary":{"RawCom","RawCom4","zCom","zCom4"},
           "dictionary":{"RawLD","RawLD4","zLD"},"general_book":{"RawGenBook"}}

def parse_conf(path):
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    values = {}; section = None
    for line in lines:
        line=line.strip()
        if not line or line.startswith(("#",";")): continue
        if line.startswith("[") and line.endswith("]"):
            if section is not None: raise ValueError("multiple SWORD sections")
            section=line[1:-1]
        elif "=" in line and section is not None:
            k,v=line.split("=",1)
            values.setdefault(k.strip(),v.strip())
        else: raise ValueError("malformed SWORD configuration")
    if not section: raise ValueError("missing SWORD module identifier")
    return section,values

def source_gate_errors(directory, source_type, root, category=None):
    """Published modules require reviewed schema provenance, not an unchecked audit."""
    errors = []
    policy_path = root / "config/osis-policy.json"
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"{policy_path}:1: [SOURCE_POLICY_MISSING] {exc}"]
    pinned = policy.get("schema_sha256")
    if policy.get("schema_status") != "reviewed" or not isinstance(pinned, str) or not re.fullmatch("[a-f0-9]{64}", pinned):
        errors.append(f"{policy_path}:1: [SCHEMA_NOT_REVIEWED] Official OSIS schema must be pinned and reviewed before approval")
    if source_type != "OSIS":
        errors.append(f"{directory}/payload/mods.d:1: [UNSUPPORTED_SOURCE_FORMAT] No approved structural validator for SourceType={source_type!r}; use the official standard's validated importer")
    proof_path = directory / "SOURCE_VALIDATION.json"
    try:
        proof = json.loads(proof_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return errors + [f"{proof_path}:1: [SOURCE_VALIDATION_MISSING] {exc}"]
    if not isinstance(proof, dict):
        return errors + [f"{proof_path}:1: [SOURCE_VALIDATION_INVALID] Expected a JSON object"]
    expected_policy_hash = hashlib.sha256(
        json.dumps(policy, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    if proof.get("status") != "validated" or proof.get("no_transformation_performed") is not True:
        errors.append(f"{proof_path}:1: [SOURCE_VALIDATION_INVALID] Source validation did not pass")
    if proof.get("schema_sha256") != pinned or proof.get("policy_sha256") != expected_policy_hash:
        errors.append(f"{proof_path}:1: [SOURCE_VALIDATION_STALE] Proof does not match current reviewed schema and policy")
    if not isinstance(proof.get("source_sha256"), str) or not re.fullmatch("[a-f0-9]{64}", proof["source_sha256"]):
        errors.append(f"{proof_path}:1: [SOURCE_VALIDATION_INVALID] Missing original source digest")

    if category == "commentary":
        commentary_policy_path = root / "config/commentary-policy.json"
        try:
            commentary_policy = json.loads(commentary_policy_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"{commentary_policy_path}:1: [COMMENTARY_POLICY_MISSING] {exc}")
        else:
            digest = hashlib.sha256(
                json.dumps(commentary_policy, sort_keys=True, ensure_ascii=False).encode("utf-8")
            ).hexdigest()
            if commentary_policy.get("schema_version") != 1:
                errors.append(f"{commentary_policy_path}:1: [COMMENTARY_POLICY_INVALID] Unknown commentary policy version")
            if proof.get("source_kind") != "commentary":
                errors.append(f"{proof_path}:1: [COMMENTARY_PROOF_MISSING] Generic OSIS proof does not validate a commentary's annotated references")
            if proof.get("commentary_policy_sha256") != digest:
                errors.append(f"{proof_path}:1: [COMMENTARY_PROOF_STALE] Missing or stale commentary-specific review")
            if type(proof.get("annotation_count")) is not int or proof["annotation_count"] < 1:
                errors.append(f"{proof_path}:1: [COMMENTARY_PROOF_INVALID] No reviewed commentary entries")
            if not isinstance(proof.get("annotation_reference_sha256"), str) or not re.fullmatch(
                    "[a-f0-9]{64}", proof["annotation_reference_sha256"]):
                errors.append(f"{proof_path}:1: [COMMENTARY_PROOF_INVALID] Missing reference mapping checksum")
    elif category == "bible" and proof.get("source_kind") not in (None, "bible"):
        errors.append(f"{proof_path}:1: [BIBLE_PROOF_MISMATCH] Commentary proof cannot validate a Bible text")
    return errors


def normalization_report_errors(directory, edition, category, pinned_schema):
    """Publishing guard for a declared, reviewed source-layout transformation.

    These reports remain reviewer assertions, not cryptographic attestations
    of remote source identity. The release auditor verifies original archives.
    """
    errors=[]
    path=directory/"NORMALIZATION_REPORT.json"
    if not path.exists() and edition=="faithful":
        return errors  # Exact-source faithful edition, no transformation claimed.
    if not path.is_file() or path.is_symlink() or path.stat().st_size>1024*1024:
        return [f"{path}: [NORMALIZATION_REPORT_MISSING] Reviewed structural edit proof required"]
    try:
        proof=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,ValueError,UnicodeError) as exc:
        return [f"{path}: [NORMALIZATION_REPORT_INVALID] {exc}"]
    if not isinstance(proof,dict):
        return [f"{path}: [NORMALIZATION_REPORT_INVALID] Expected JSON object"]
    required={
        "status":"structural_edit_verified_not_published",
        "edition":edition,"kind":category,
        "full_text_exactly_preserved":True,
        "inline_semantic_tags_preserved":True,
        "original_source_unchanged":True,
        "schema_sha256":pinned_schema,
    }
    for key,value in required.items():
        if proof.get(key)!=value:
            errors.append(f"{path}: [NORMALIZATION_PROOF_MISMATCH] {key} does not match reviewed source proof")
    for key in ("source_sha256","output_sha256","plan_sha256","diff_sha256"):
        if not isinstance(proof.get(key),str) or not re.fullmatch("[a-f0-9]{64}",proof[key]):
            errors.append(f"{path}: [NORMALIZATION_PROOF_INVALID] Missing {key} checksum")
    if not isinstance(proof.get("operations"),list) or not proof["operations"]:
        errors.append(f"{path}: [NORMALIZATION_PROOF_INVALID] No reviewed edits")
    if not isinstance(proof.get("review_asserted_by_plan"),str) or len(proof["review_asserted_by_plan"].strip())<2:
        errors.append(f"{path}: [NORMALIZATION_PROOF_INVALID] Missing editorial sign-off assertion")
    validation=directory/"SOURCE_VALIDATION.json"
    try:
        source_proof=json.loads(validation.read_text(encoding="utf-8"))
    except (OSError,ValueError,UnicodeError) as exc:
        errors.append(f"{path}: [NORMALIZATION_PROOF_MISSING_OUTPUT] {exc}")
    else:
        if (not isinstance(source_proof,dict) or
                proof.get("output_sha256")!=source_proof.get("source_sha256")):
            errors.append(f"{path}: [NORMALIZATION_OUTPUT_MISMATCH] Normalized output checksum differs from OSIS source validation")
    return errors


def validate(root=ROOT):
    errors=[]; modules=[]; seen=set(); edition_variants=set(); edition_details={}
    schema=json.loads((root/"schemas/module.schema.json").read_text(encoding="utf-8"))
    validator=Draft202012Validator(schema,format_checker=FormatChecker())
    for d in sorted((root/"modules").iterdir()):
        if d.name.startswith("."): continue
        if d.is_symlink() or not d.is_dir():
            errors.append(f"{d.name}: not a real module directory"); continue
        try: m=json.loads((d/"metadata.json").read_text(encoding="utf-8"))
        except Exception as e: errors.append(f"{d.name}: unreadable metadata: {e}");continue
        issues=list(validator.iter_errors(m))
        if issues:
            errors.extend(f"{d.name}: {e.message}" for e in issues);continue
        if m["id"] != d.name: errors.append(f"{d.name}: folder / id mismatch")
        if m["sword_id"].casefold() in seen: errors.append(f"{d.name}: duplicate SWORD id")
        seen.add(m["sword_id"].casefold())
        modules.append((d,m))
        for upstream in m.get("upstreams", []):
            accepted = {c["url"] for c in upstream.get("contributions", [])
                        if c["state"] in {"accepted", "released"}}
            recorded = set()
            for review in upstream.get("reconciliations", []):
                revision = (review["upstream_version"], review["upstream_conf_sha256"])
                if revision in recorded:
                    errors.append(f"{d.name}: duplicate reconciliation for upstream revision {revision[0]}")
                recorded.add(revision)
                if review["contribution_url"] not in accepted:
                    errors.append(f"{d.name}: reconciliation must cite an accepted/released contribution from the same upstream")
                if review["reviewed_by"].strip().upper() == "PENDING":
                    errors.append(f"{d.name}: upstream reconciliation requires a real reviewer")
        payload=d/"payload"
        approved=m["quality"]["status"]=="approved"
        if approved:
            canonical=m.get("canonical_edition_id")
            if canonical:
                identity=(m["category"],m["language"])
                previous=edition_details.setdefault(canonical,identity)
                if previous!=identity:
                    errors.append(f"{d.name}: canonical edition identity conflicts with a different category/language")
                variant=(canonical,m["quality"]["edition"])
                if variant in edition_variants:
                    errors.append(f"{d.name}: duplicate curated edition variant {canonical}/{variant[1]}; only one module per edition and variant")
                edition_variants.add(variant)
        if not approved:
            if payload.exists(): errors.append(f"{d.name}: unapproved payload must not be committed")
            continue
        rights=m["rights"]
        if not rights["redistribution_allowed"] or rights["reviewed_by"].upper()=="PENDING":
            errors.append(f"{d.name}: redistribution not approved")
        if m["quality"]["reviewed_by"].upper()=="PENDING":
            errors.append(f"{d.name}: editorial review missing")
        if m["quality"]["edition"]=="reader_optimized" and not rights["derivatives_allowed"]:
            errors.append(f"{d.name}: derivative rights missing")
        if m["category"] in ("bible","commentary"):
            policy=json.loads((root/"config/osis-policy.json").read_text(encoding="utf-8"))
            errors.extend(normalization_report_errors(
                d,m["quality"]["edition"],m["category"],policy.get("schema_sha256")))
        if "example." in rights["evidence_url"]:
            errors.append(f"{d.name}: example is not a rights authorization")
        if not (d/"EDITORIAL.md").is_file(): errors.append(f"{d.name}: editorial changelog required")
        if payload.is_symlink() or not payload.is_dir():
            errors.append(f"{d.name}: no safe payload");continue
        confs=list((payload/"mods.d").glob("*.conf"))
        if len(confs)!=1: errors.append(f"{d.name}: exactly one .conf expected");continue
        for p in payload.rglob("*"):
            if p.is_symlink(): errors.append(f"{d.name}: payload symlink forbidden")
            if p.is_file() and p.stat().st_mode & 0o111:
                errors.append(f"{d.name}: executable payload forbidden")
        try: section,conf=parse_conf(confs[0])
        except (OSError,ValueError,UnicodeError) as e:
            errors.append(f"{d.name}: bad configuration: {e}");continue
        if section != m["sword_id"]: errors.append(f"{d.name}: module name mismatch")
        if confs[0].name != section.lower()+".conf": errors.append(f"{d.name}: .conf filename mismatch")
        driver=conf.get("ModDrv")
        if driver not in DRIVERS or driver not in ALLOWED.get(m["category"],set()):
            errors.append(f"{d.name}: unsupported or mismatched driver")
        if conf.get("Encoding")!="UTF-8": errors.append(f"{d.name}: UTF-8 required")
        errors.extend(source_gate_errors(d, conf.get("SourceType"), root, m["category"]))
        if m["category"] == "bible":
            strategy = m.get("index_audit", {})
            try:
                source_proof = json.loads(
                    (d / "SOURCE_VALIDATION.json").read_text(encoding="utf-8"))
                validated_sha = source_proof["source_sha256"]
                if strategy.get("mode") == "stock_reader_keys":
                    errors.extend(stable_sword_proof_errors(
                        d, m["versification"], validated_sha))
                elif strategy.get("mode") == "published_source_audit":
                    errors.extend(archived_release_errors(
                        d, root, strategy["manifest"], m, validated_sha))
                else:
                    errors.append(f"{d.name}: [SWORD_INDEX_PROOF_MISSING] "
                                  "Approved Bible requires an index proof mode")
            except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
                errors.append(f"{d.name}: [SWORD_INDEX_PROOF_INVALID] {exc}")
        if conf.get("Lang")!=m["language"]: errors.append(f"{d.name}: language mismatch")
        if m["category"] in ("bible","commentary") and conf.get("Versification")!=m.get("versification"):
            errors.append(f"{d.name}: versification mismatch")
        for field in ("SourceType","DistributionLicense","TextSource","Version","Description","DataPath"):
            if not conf.get(field):errors.append(f"{d.name}: missing {field}")
        if conf.get("Version") != m["version"]:
            errors.append(
                f"{d.name}: SWORD .conf Version {conf.get('Version')!r} "
                f"does not match curated metadata version {m['version']!r}; "
                "catalogue updates must never advertise a different installed version"
            )
        data=conf.get("DataPath","")
        rel=data[2:] if data.startswith("./") else ""
        pure=PurePosixPath(rel)
        if not rel.startswith("modules/") or pure.is_absolute() or ".." in pure.parts:
            errors.append(f"{d.name}: invalid DataPath")
        else:
            target=(payload/rel).resolve(); base=(payload/"modules").resolve()
            if not target.is_relative_to(base): errors.append(f"{d.name}: escaping DataPath")
            elif not target.exists() and not list(target.parent.glob(target.name+"*")):
                errors.append(f"{d.name}: no SWORD data")
    return modules, errors

def main():
    modules, errors=validate()
    for e in errors: print("ERROR",e,file=sys.stderr)
    if errors:return 1
    print(f"Validated {len(modules)} entries; approved {sum(m['quality']['status']=='approved' for _,m in modules)}")
    return 0

if __name__=="__main__":raise SystemExit(main())
