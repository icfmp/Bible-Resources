#!/usr/bin/env python3
"""Stage the independently tested HMCC Modern QA binary for reviewed publication.

Inputs are solely the pinned successful GitHub Actions QA artifact (one ZIP
and one metadata receipt), plus the committed owner's editorial decisions.
No recompilation or modification of compressed authorial data is permitted.
Run only in a disposable CI checkout; this script never contacts GitHub.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SOURCE_RUN = 44695710957
SOURCE_ARTIFACT = 14610990289
OWNER_PR = "https://github.com/icfmp/Bible-Resources/pull/272"
SOURCE_ROOT = "https://github.com/icfmp/Bible-Resources"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                    encoding="utf-8")


def stage(qa_dir: Path) -> dict:
    if not qa_dir.is_dir():
        raise ValueError("Missing exact GitHub Actions QA artifact")
    archive = qa_dir / "HMCCModern-0.1.0-MANUAL-QA.zip"
    receipt_path = qa_dir / "hmcc-modern-owner-review-package-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    archive_data = archive.read_bytes()
    if (receipt.get("status") != "OWNER_MANUAL_QA_PACKAGE_NOT_PUBLIC_RELEASE"
            or receipt.get("module_id") != "HMCCModern"
            or receipt.get("version") != "0.1.0"
            or receipt.get("zip_sha256") != digest(archive_data)
            or receipt.get("zip_size_bytes") != len(archive_data)
            or receipt.get("editorial_corrections") != 15
            or receipt.get("corrected_destinations") != 28
            or receipt.get("restored_historical_expositions") != 2):
        raise ValueError("QA archive identity is not the previously attested source")
    decisions_path = ROOT / "work/mhcc-modern/production/OWNER_EDITORIAL_DECISIONS_2026-11-19.json"
    decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
    if (decisions["source_native_corpus_sha256"] !=
            "2d85930f0a69efaf30dbde195e5f9779eaaf849cf0221e85ed46d6ec8bcb025e"
            or len(decisions.get("link_cases", [])) != 15
            or sum(len(c["approved_derived_destinations"]) for c in decisions["link_cases"]) != 28
            or len(decisions.get("ccel_only_sections", [])) != 2):
        raise ValueError("Approved editorial decisions diverged")
    module = ROOT / "modules/hmcc-modern"
    if module.exists():
        raise ValueError("Refusing overwrite of an existing staged or published module")
    payload = module / "payload"
    names = {"mods.d/hmccmodern.conf"} | {
        f"modules/comments/zcom/hmccmodern/{side}.cz{suffix}"
        for side in ("ot", "nt") for suffix in ("s", "v", "z")
    }
    with ZipFile(archive) as z:
        actual = z.namelist()
        if len(actual) != 7 or set(actual) != names or z.testzip() is not None:
            raise ValueError("QA archive is not the seven-member reviewed zCom")
        if any(digest(z.read(name)) != receipt["sword_member_sha256"].get(name)
               for name in names):
            raise ValueError("Independent SHA-256 failed for QA SWORD member")
        for name in sorted(names):
            dest = payload / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(name))
    original_conf = (payload / "mods.d/hmccmodern.conf").read_bytes()
    if b"Encoding=" in original_conf or b"TextSource=" in original_conf:
        raise ValueError("Expected original QA config to require exactly two release metadata additions")
    if not original_conf.startswith(b"[HMCCModern]\n"):
        raise ValueError("SWORD configuration ID changed from reviewed package")
    original_conf_sha = digest(original_conf)
    source_url = SOURCE_ROOT + "/tree/main/work/mhcc-modern/production/accepted"
    final_conf = original_conf.rstrip(b"\n") + (
        "\nEncoding=UTF-8\nTextSource=" + source_url + "\n"
    ).encode()
    (payload / "mods.d/hmccmodern.conf").write_bytes(final_conf)
    hashes = {p.relative_to(payload).as_posix(): digest(p.read_bytes())
              for p in sorted(payload.rglob("*")) if p.is_file()}
    original_six = {name: receipt["sword_member_sha256"][name]
                    for name in names - {"mods.d/hmccmodern.conf"}}
    for name, original_sha in original_six.items():
        if hashes[name] != original_sha:
            raise ValueError("The six compiled source members must remain byte-identical")
    module_meta = {
        "schema_version": 1, "id": "hmcc-modern",
        "canonical_edition_id": "matthew-henry-concise-modern-english-2026",
        "sword_id": "HMCCModern",
        "title": {"en": "Henry's Modern Concise Commentary",
                  "fr": "Commentaire concis de Matthew Henry en anglais moderne"},
        "category": "commentary", "language": "en", "version": "0.1.0",
        "versification": "KJV",
        "origin": {
            "publisher": "Bible Resources (modern English); original Matthew Henry text via CrossWire",
            "url": "https://crosswire.org/sword/modules/ModInfo.jsp?modName=MHCC",
            "source_revision": ("Matthew Henry's Concise Commentary; curated MHCC 0.1.1 "
                                "primary witness; separately attested historical passages"),
        },
        "rights": {
            "license": "Copyrighted; Permission to distribute granted by copyright holder",
            "evidence_url": OWNER_PR,
            "redistribution_allowed": True, "derivatives_allowed": True,
            "reviewed_by": ("Bible Resources project owner — direct publication instruction "
                            "2026-11-20; primary Matthew Henry text public domain; "
                            "distinct modern derivative not relicensed as the source"),
        },
        "quality": {
            "status": "approved", "edition": "reader_optimized",
            "reviewed_by": ("Bible Resources project owner — previously approved modern "
                            "English translation and 15+2 editorial decisions; "
                            "explicit publication instruction 2026-11-20; Xiphos "
                            "note-marker manual QA deliberately deferred"),
            "smoke_key": "Gen 12:6",
        },
        "index_audit": {
            "mode": "reviewed_modern_commentary_rebuild",
            "manifest": "config/commentary-rebuilds/hmcc-modern.json",
        },
    }
    save(module / "metadata.json", module_meta)
    source_osis_sha = receipt["source_approved_editorial_osis_sha256"]
    source_run_url = SOURCE_ROOT + "/actions/runs/" + str(SOURCE_RUN)
    plan = {
        "schema_version": 1,
        "status": "owner_authorized_for_release",
        "module_id": "hmcc-modern",
        "sword_id": "HMCCModern",
        "release_id": "HMCCModern",
        "version": "0.1.0",
        "source_module": "MHCC 0.1.1",
        "original_native_sha256": decisions["source_native_corpus_sha256"],
        "source_approved_osis_sha256": source_osis_sha,
        "source_decisions": decisions_path.relative_to(ROOT).as_posix(),
        "approved_link_cases": 15,
        "approved_link_destinations": 28,
        "historical_authorial_restorations": 2,
        "source_run_id": SOURCE_RUN,
        "source_reader_run_url": source_run_url,
        "source_artifact_id": SOURCE_ARTIFACT,
        "source_archive_sha256": receipt["zip_sha256"],
        "source_archive_size_bytes": receipt["zip_size_bytes"],
        "underlying_public_domain_source":
            "CrossWire MHCC 2.0 — Public Domain / Copy Freely",
        "derivative_rights_status":
            "owner_authorized_distribution_no_relicensing_of_underlying_source",
        "authorization": {
            "approved_by": "Bible Resources project owner",
            "approval_url": OWNER_PR,
            "decision": ("Publish the source-attested modern-English derivative as "
                         "HMCC Modern 0.1.0, with owner-approved 15 link corrections "
                         "and two historical restorations. Manual note-click "
                         "navigation in Xiphos remains a post-publication test."),
        },
    }
    save(ROOT / "config/commentary-rebuilds/hmcc-modern.json", plan)
    save(module / "SOURCE_VALIDATION.json", {
        "schema_version": 1, "status": "validated",
        "source_kind": "reviewed_modern_commentary_rebuild",
        "curated_module_id": "HMCCModern", "curated_version": "0.1.0",
        "original_native_sha256": decisions["source_native_corpus_sha256"],
        "source_approved_osis_sha256": source_osis_sha,
        "source_reader_run_url": source_run_url,
        "approved_link_cases": 15,
        "approved_link_destinations": 28,
        "historical_authorial_restorations": 2,
        "compiled_zcom_members_identical_to_accepted_QA": True,
        "original_source_unchanged": True,
        "modern_manuscripts_unchanged": True,
    })
    save(module / "RELEASE_ARTIFACT_PROOF.json", {
        "schema_version": 1,
        "source_run_id": SOURCE_RUN,
        "source_artifact_id": SOURCE_ARTIFACT,
        "source_archive_sha256": receipt["zip_sha256"],
        "source_archive_size_bytes": receipt["zip_size_bytes"],
        "source_approved_osis_sha256": source_osis_sha,
        "source_binary_data_identical": True,
        "metadata_only_conf_delta": {
            "original_review_conf_sha256": original_conf_sha,
            "added_fields": ["Encoding=UTF-8", "TextSource=" + source_url],
            "final_sha256": digest(final_conf),
        },
        "payload_sha256": hashes,
        "original_QA_six_data_member_sha256": original_six,
    })
    (module / "EDITORIAL.md").write_text(
        "# HMCC Modern 0.1.0 — editorial and rights record\n\n"
        "Henry's Modern Concise Commentary is a distinct English modernization, "
        "not the original unchanged Matthew Henry edition. The primary witness "
        "is the published Bible Resources MHCC 0.1.1, curated from the CrossWire "
        "public-domain module. The approved derivative incorporates 15 separately "
        "audited reference corrections (28 source-derived navigation targets) "
        "and two restored Matthew Henry exposition sections, independently "
        "attributed to a secondary historical textual witness. The digitized "
        "CCEL PDF and its presentation are not redistributed. The source "
        "witness and modern manuscripts remain unchanged in this packaging step.\n\n"
        "The six compiled SWORD zCom data files are byte-for-byte identical "
        "to the successfully compiled editorial QA module; the only packaging "
        "change is the addition of mandatory Encoding and TextSource fields "
        "to the final module .conf. The human owner authorized publication on "
        "2026-11-20, with the remaining Xiphos editorial-note click interaction "
        "assigned to manual post-publication testing. This does not imply "
        "independent certification of every individual hyperlink.\n\n"
        f"Source and native GUI evidence: {source_run_url}.\n"
        f"Source decisions: {OWNER_PR}.\n"
        f"QA artifact: {source_run_url}/artifacts/{SOURCE_ARTIFACT}.\n"
        "The original primary historical text remains public domain. This "
        "derivative is distributed with the owner's permission; it is not a "
        "claim of new proprietary rights in the original Matthew Henry text.\n",
        encoding="utf-8",
    )
    notes = ROOT / "docs/releases/HMCC-Modern-0.1.0.md"
    notes.parent.mkdir(parents=True, exist_ok=True)
    notes.write_text(
        "# HMCC Modern 0.1.0 — Henry's Modern Concise Commentary\n\n"
        "An independently packaged modern-English Matthew Henry concise "
        "commentary for SWORD readers, with standard KJV versification and "
        "native zCom chapter compression. It uses a distinct SWORD identity "
        "`HMCCModern` to avoid overwriting original `MHCC`.\n\n"
        "**Scope:** 1,189 canonical chapters, 15 owner-approved editorial "
        "reference corrections with 28 targets, and two restored historical "
        "authorial sections. Original text/translation witnesses are tracked "
        "separately, and the six binary data members are bound to a verified "
        "private reader-workflow artifact. This release changes the modern "
        "English text, not the original CrossWire module.\n\n"
        "**Manual follow-up:** In Xiphos, open Numbers 29:1 and activate "
        "the corrected note marker leading to Leviticus 23:24; confirm the "
        "destination verse is selected in the sidebar. Other note-linked "
        "destinations have verified SWORD markup but have not all been "
        "individually clicked in Xiphos. The owner chose post-release manual "
        "verification rather than treating an inaccessible CI GUI harness "
        "as a textual failure.\n\n"
        "The primary Matthew Henry edition is public domain according "
        "to CrossWire. The modern rendering and separately recorded "
        "derivative editorial elements are not presented as a new "
        "copyright in Matthew Henry's original prose. See "
        "[the editorial record](../../modules/hmcc-modern/EDITORIAL.md).\n",
        encoding="utf-8",
    )
    # First build intentionally omits the committed stale official snapshot,
    # then pins the exact built ZIP checksum to an immutable release plan.
    from build import build
    snap = ROOT / "catalog/v1/catalog.json"
    previous = snap.read_bytes()
    snap.unlink()
    try:
        with tempfile.TemporaryDirectory(prefix="hmcc-staged-built-") as tmp:
            dist = Path(tmp) / "dist"
            build(root=ROOT, output=dist)
            package = dist / "sword/packages/HMCCModern.zip"
            package_data = package.read_bytes()
            plan_release = {
                "schema_version": 1,
                "tag": "hmcc-modern-0.1.0",
                "module_id": "hmcc-modern",
                "sword_id": "HMCCModern",
                "version": "0.1.0",
                "title": "HMCC Modern 0.1.0 — Henry's Modern Concise Commentary",
                "zip_name": "HMCCModern-0.1.0.zip",
                "package_sha256": digest(package_data),
                "package_size_bytes": len(package_data),
                "notes_path": "docs/releases/HMCC-Modern-0.1.0.md",
                "evidence_path": "modules/hmcc-modern/SOURCE_VALIDATION.json",
                "editorial_path": "modules/hmcc-modern/EDITORIAL.md",
                "authorization": {
                    "reviewed_by": "Bible Resources project owner — 2026-11-20",
                    "decision": ("Publish source-attested HMCC Modern 0.1.0 "
                                 "with approved corrections; manual Xiphos "
                                 "note-click check explicitly deferred"),
                    "evidence_url": OWNER_PR,
                    "source_rights": ("Original Matthew Henry via CrossWire Public Domain; "
                                      "separate modern derivative authorized by project owner; "
                                      "no imported CCEL formatting"),
                },
            }
            save(ROOT / "config/release-plans/hmcc-modern-0.1.0.json", plan_release)
            shutil.copyfile(dist / "catalog/v1/catalog.json", snap)
    except BaseException:
        snap.write_bytes(previous)
        raise
    print("STAGED_HMCC_MODERN_RELEASE " + json.dumps({
        "qa_source_sha256": receipt["zip_sha256"],
        "release_zip_sha256": plan_release["package_sha256"],
        "release_zip_size_bytes": plan_release["package_size_bytes"],
        "compiled_data_member_count": len(original_six),
        "approved_publication_instruction_recorded": True,
        "catalogue_committed_snapshot_updated": True,
        "published": False,
    }, sort_keys=True))
    return plan_release


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--qa-dir", type=Path, required=True)
    args = parser.parse_args()
    stage(args.qa_dir)
