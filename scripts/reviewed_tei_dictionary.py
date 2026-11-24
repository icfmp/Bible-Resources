#!/usr/bin/env python3
"""Validate reviewed, source-bound TEI dictionary payload and full native receipts."""
from hashlib import sha256
import json
from pathlib import Path
import re

SHA = re.compile(r"[0-9a-f]{64}\Z")


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read_json(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000:
        raise ValueError("Missing or unsafe dictionary evidence")
    result = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError("Expected a JSON evidence object")
    return result


def require(condition, message):
    if not condition:
        raise ValueError(message)


def valid_sha(value):
    return isinstance(value, str) and SHA.fullmatch(value) is not None


def dictionary_proof_errors(directory, root, metadata, conf):
    """Check exact receipts and immutable native members, not just a schema label."""
    try:
        require(metadata["category"] == "dictionary" and conf.get("SourceType") == "TEI"
                and conf.get("ModDrv") == "zLD" and conf.get("CompressType") == "ZIP",
                "Unsupported TEI dictionary driver/format")
        proof = read_json(directory / "SOURCE_VALIDATION.json")
        policy = read_json(root / "config/tei-policy.json")
        require(proof["schema_version"] == policy["schema_version"] == 1
                and proof["status"] == "validated"
                and proof["source_kind"] == "dictionary"
                and proof["sword_id"] == metadata["sword_id"]
                and proof["version"] == metadata["version"]
                and proof["canonical_edition_id"] == metadata["canonical_edition_id"],
                "Dictionary proof identity mismatch")
        source = proof["source_sha256"]
        adapter = proof["adapter_sha256"]
        original = proof["original_archive_sha256"]
        require(all(valid_sha(v) for v in (source, adapter, original)),
                "Missing exact source/adapter/original SHA-256")
        upstream = proof["upstream_release"]
        require(upstream["url"] == metadata["origin"]["url"]
                and upstream["url"].startswith("https://github.com/")
                and upstream["verified_public"] is True
                and upstream["draft"] is False and upstream["prerelease"] is False
                and valid_sha(upstream["package_sha256"])
                and valid_sha(upstream["source_archive_sha256"])
                and type(upstream["package_size_bytes"]) is int
                and upstream["package_size_bytes"] > 0,
                "Unreviewed published dictionary archive")
        schema = proof["schema_validation"]
        require(schema["schema_version"] == 1
                and schema["source_sha256"] == source
                and schema["standard"] == policy["standard"] == "TEI P5"
                and schema["version"] == policy["version"]
                and all(valid_sha(policy[k]) and schema[k] == policy[k]
                        for k in ("rng_sha256", "schematron_sha256"))
                and all(schema[k] is True for k in
                        ("relax_ng_passed", "schematron_passed",
                         "relax_ng_negative_control_rejected",
                         "schematron_negative_control_rejected")),
                "Missing exact official TEI schema proof")
        pos = schema["schematron_positive_counts"]
        neg = schema["schematron_negative_counts"]
        require(pos["active_patterns"] > 0 and pos["fired_rules"] > 0
                and pos["failed_assertions"] == pos["successful_reports"] == 0
                and neg["failed_assertions"] + neg["successful_reports"] > 0,
                "TEI Schematron evidence did not pass")
        native = proof["native_roundtrip"]
        count = proof["entry_count"]
        require(type(count) is int and count > 0
                and native["schema_version"] == 1
                and native["expected_tei_sha256"] == adapter
                and valid_sha(native["native_imp_sha256"])
                and native["expected_keys"] == native["native_keys"] == count
                and native["native_roundtrip_verified"] is True
                and all(type(native[k]) is int and native[k] == 0 for k in
                        ("missing_key_count", "unexpected_key_count", "malformed_count",
                         "unicode_text_mismatch_count", "xml_structure_mismatch_count")),
                "Incomplete native dictionary key/text/XML parity")
        require(isinstance(proof["evidence_url"], str)
                and proof["evidence_url"].startswith("https://github.com/")
                and isinstance(proof["reader_evidence_url"], str)
                and proof["reader_evidence_url"].startswith("https://github.com/"),
                "Missing independent reader evidence")
        samples = proof["reader_samples"]
        require(isinstance(samples, dict) and len(samples) >= 2
                and metadata["quality"]["smoke_key"] in samples
                and all(isinstance(v, dict) and type(v.get("bytes")) is int
                        and v["bytes"] > 0 and valid_sha(v.get("sha256"))
                        for v in samples.values()),
                "Incomplete native reader sample receipt")
        members = proof["payload_members"]
        payload = directory / "payload"
        paths = {p.relative_to(payload).as_posix(): p for p in payload.rglob("*")
                 if p.is_file()}
        require(isinstance(members, dict) and set(paths) == set(members),
                "Dictionary native payload inventory changed")
        data_path = conf.get("DataPath", "")
        require(data_path.startswith("./modules/lexdict/") and
                ".." not in Path(data_path).parts and "\\" not in data_path,
                "Unsafe dictionary data path")
        prefix = data_path[2:]
        conf_path = "mods.d/" + metadata["sword_id"].lower() + ".conf"
        require(set(paths) == {conf_path} | {prefix + ext for ext in
                (".dat", ".idx", ".zdt", ".zdx")},
                "Unexpected zLD payload members")
        for name, path in paths.items():
            entry = members[name]
            require(not path.is_symlink() and valid_sha(entry["sha256"])
                    and type(entry["size_bytes"]) is int
                    and path.stat().st_size == entry["size_bytes"]
                    and digest(path) == entry["sha256"],
                    "Dictionary native member fingerprint mismatch: " + name)
        return []
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        return [f"{directory}: [TEI_DICTIONARY_PROOF_INVALID] {exc}"]
