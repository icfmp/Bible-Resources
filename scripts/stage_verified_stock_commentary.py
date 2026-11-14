#!/usr/bin/env python3
"""Stage a previously reviewed original zCom stock witness for release.

This is a GENERIC adaptor for byte-preserved existing SWORD commentaries,
not an OSIS/ThML importer. It must never make a source/edition correction.
The existing private candidate pipeline independently verifies the exact
upstream archive, six compressed source members, every native K/I/TOP key
and genuine diatheke readbacks *before* materialization. Then we change
only the curated Version line in the already verified candidate .conf.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import tempfile

from commentary_stock_candidate import make_private_candidate
from pilot_preflight import PilotError

SHA = re.compile(r"[a-f0-9]{64}\Z")
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?\Z")
SUFFIXES = ("nt.bzs", "nt.bzv", "nt.bzz", "ot.bzs", "ot.bzv", "ot.bzz")


def reviewed_curated_version(conf: bytes, *, source_version: str,
                           curated_version: str) -> bytes:
    """Only change the SWORD Version line; all other source metadata stays."""
    if (not isinstance(source_version, str) or not source_version
            or not isinstance(curated_version, str)
            or not VERSION.fullmatch(curated_version)
            or len(conf) > 16000):
        raise PilotError("Unreviewed original or curated commentary version")
    original = b"Version=" + source_version.encode("ascii")
    changed = b"Version=" + curated_version.encode("ascii")
    lines = conf.splitlines(keepends=True)
    positions = [i for i, line in enumerate(lines)
                 if line.rstrip(b"\r\n") == original]
    if len(positions) != 1 or sum(
            line.startswith(b"Version=") for line in lines) != 1:
        raise PilotError("Original SWORD Version metadata is not uniquely attested")
    line = lines[positions[0]]
    ending = line[len(line.rstrip(b"\r\n")):]
    lines[positions[0]] = changed + ending
    result = b"".join(lines)
    if result != conf.replace(original + ending, changed + ending, 1):
        raise PilotError("Curated Version changed unrelated upstream metadata")
    return result


def stage(resource_id: str, *, module_dir: Path, native_raw_binary: Path) -> dict:
    """Require reviewed source metadata and SHA parity before writing payload.

    Caller performs the independent final repository validation and public
    release. The source archive is ephemeral; only the metadata-only proof
    and the reviewed SWORD module files are staged.
    """
    if not (module_dir.is_dir() and not module_dir.is_symlink()
            and (module_dir / "metadata.json").is_file()
            and native_raw_binary.is_file() and not native_raw_binary.is_symlink()
            and not (module_dir / "payload").exists()
            and not (module_dir / "SOURCE_VALIDATION.json").exists()):
        raise PilotError("Refusing unreviewed, existing or incomplete release destination")
    m = json.loads((module_dir / "metadata.json").read_text(encoding="utf-8"))
    if (m.get("category") != "commentary"
            or m.get("index_audit") != {"mode": "stock_reader_keys"}
            or m.get("quality", {}).get("status") != "approved"
            or m.get("quality", {}).get("edition") != "faithful"
            or m.get("rights", {}).get("license") != "Public Domain"
            or m.get("rights", {}).get("redistribution_allowed") is not True
            or m.get("rights", {}).get("derivatives_allowed") is not True
            or not VERSION.fullmatch(m.get("version", ""))
            or not m.get("sword_id", "").isalnum()):
        raise PilotError("Compiled stock commentary lacks approved metadata/rights")
    metadata_sword_id = m["sword_id"]
    with tempfile.TemporaryDirectory(prefix="verified-stock-commentary-") as tmp:
        work = Path(tmp)
        captured = work / "captured"
        captured.mkdir()
        def capture_verified_candidate(original: Path, candidate: Path, manifest: dict) -> dict:
            """Copy only after complete source/candidate parity, still privately."""
            original_id = manifest["module_id"]
            if original_id == metadata_sword_id:
                raise PilotError("Curated ID must not replace upstream source")
            source_rel = Path("modules/comments/zcom") / metadata_sword_id.lower()
            expected = {Path("mods.d") / (metadata_sword_id.lower() + ".conf")}
            expected |= {source_rel / suffix for suffix in SUFFIXES}
            real_files = {p.relative_to(candidate) for p in candidate.rglob("*") if p.is_file()}
            if real_files != expected or any(p.is_symlink() for p in candidate.rglob("*")):
                raise PilotError("Original reviewed zCom candidate contains unexpected members")
            for rel in sorted(expected):
                destination = captured / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(candidate / rel, destination)
            return {"source_compiled_only": True, "published": False}
        receipt = make_private_candidate(
            resource_id, native_raw_binary=native_raw_binary,
            candidate_id=metadata_sword_id,
            on_verified_private_candidate=capture_verified_candidate,
        )
        if (receipt["resource_id"] != resource_id
                or receipt["all_original_SWORD_compressed_files_byte_preserved"] is not True
                or receipt["complete_stock_and_candidate_native_raw_corpus_sha256_equal"] is not True
                or receipt["all_occupied_native_K_I_TOP_keys_and_order_identical"] is not True
                or receipt["private_candidate_archive_destroyed_without_upload"] is not True
                or receipt["published"] is not False
                or receipt["independent_private_candidate_gui_receipt"] !=
                   {"source_compiled_only": True, "published": False}
                or receipt["private_candidate_module_id"] != metadata_sword_id):
            raise PilotError("Complete independent original compiled source parity not established")
        confpath = captured / "mods.d" / (metadata_sword_id.lower() + ".conf")
        upstream_version = m["upstreams"][0]["last_integrated_version"]
        confpath.write_bytes(reviewed_curated_version(
            confpath.read_bytes(), source_version=upstream_version,
            curated_version=m["version"]))
        source_rel = Path("modules/comments/zcom") / metadata_sword_id.lower()
        members = {
            suffix: sha256((captured / source_rel / suffix).read_bytes()).hexdigest()
            for suffix in SUFFIXES
        }
        if len(set(members.values())) < 2:
            raise PilotError("Unexpected degenerate SWORD compressed member inventory")
        # The source .conf remains provenance evidence, not a fabricated XML.
        evidence = {
            "schema_version": 1,
            "status": "validated",
            "source_kind": "compiled_sword_stock",
            "source_intake_manifest": f"config/commentary-intake/{resource_id}.json",
            "upstream_module_id": receipt["upstream_sword_original_module_id"],
            "curated_module_id": metadata_sword_id,
            "upstream_version": upstream_version,
            "curated_version": m["version"],
            "upstream_archive_sha256": receipt["upstream_sword_original_archive_sha256"],
            "upstream_conf_sha256": receipt["upstream_sword_original_conf_sha256"],
            "native_raw_corpus_sha256": receipt["full_native_unfiltered_raw_corpus_sha256"],
            "native_key_count": receipt["total_native_keys"],
            "compressed_members_sha256_by_filename": members,
            "curated_conf_sha256": sha256(confpath.read_bytes()).hexdigest(),
            "all_original_compressed_files_byte_identical": True,
            "all_native_original_keys_byte_identical": True,
            "only_source_metadata_relabelled": ["section_id", "DataPath", "Version"],
            "no_original_source_text_edited": True,
            "historical_print_or_ccel_parity_claimed": False,
            "gui_other_reader_compatibility_claimed": False,
        }
        intake = json.loads((Path(__file__).resolve().parents[1] /
                             evidence["source_intake_manifest"]).read_text(encoding="utf-8"))
        if (intake["module_id"] != evidence["upstream_module_id"]
                or intake["version"] != upstream_version
                or intake["archive_sha256"] != evidence["upstream_archive_sha256"]
                or intake["stock_conf_sha256"] != evidence["upstream_conf_sha256"]
                or intake["native_raw_corpus_sha256"] != evidence["native_raw_corpus_sha256"]
                or receipt["total_native_keys"] < 1
                or not all(SHA.fullmatch(value) for value in members.values())):
            raise PilotError("Original source attestation differs from reviewed research manifest")
        target = module_dir / "payload"
        shutil.copytree(captured, target)
        (module_dir / "SOURCE_VALIDATION.json").write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource-id", required=True)
    parser.add_argument("--module-dir", required=True, type=Path)
    parser.add_argument("--native-raw-binary", required=True, type=Path)
    args = parser.parse_args()
    proof = stage(args.resource_id, module_dir=args.module_dir,
                  native_raw_binary=args.native_raw_binary)
    print("Staged byte-preserved SWORD commentary with verified original "
          f"{proof['native_key_count']} native keys; release NOT YET published")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
