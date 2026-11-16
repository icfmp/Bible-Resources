#!/usr/bin/env python3
"""Generic source-neutral SWORD commentary public metadata *proposal* preflight.

This only constructs a candidate UTF-8 .conf **in memory** from a completely
verified private versioned SWORD candidate. The original upstream About
remains byte-for-byte within an explicitly attributed upstream block, while
SwordVersionDate changes to the actual future release's declared day. The
caller must separately review, authorize and publish by the normal release
plan. This module DOES NOT approve an edition, write assets or publish.
"""
from __future__ import annotations

from datetime import date
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import re
import zipfile

from reviewed_compiled_commentary_rebuild import zcom_member_suffixes


def _exact_conf_value(conf: str, key: str) -> str:
    fields = re.findall(rf"^{re.escape(key)}=([^\r\n]*)$", conf, flags=re.M)
    if len(fields) != 1:
        raise ValueError("Required single SWORD commentary metadata value missing")
    return fields[0]


def _iso_day(value: str) -> date:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("SWORD module revision must use complete ISO 8601 calendar date")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError("SWORD module revision date is not a valid calendar day") from None


def prepare_provisional_public_commentary_conf(
        private_conf: bytes, *, expected_module_id: str,
        expected_module_version: str, source_provider: str,
        original_sword_version_date: str,
        proposed_public_revision_day: str, revision_summary: str) -> tuple[bytes, dict]:
    """Build two reviewed field deltas only; original source About is retained.

    The proposed date is just an input: only the actual approved public
    publication day is acceptable when the release is eventually published.
    Supplying a plausible date or passing these tests NEVER authorizes release.
    """
    if (not isinstance(private_conf, bytes) or not 1 <= len(private_conf) <= 128 * 1024
            or b"\x00" in private_conf
            or not isinstance(expected_module_id, str)
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,79}", expected_module_id)
            or not isinstance(expected_module_version, str)
            or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", expected_module_version)
            or not isinstance(source_provider, str)
            or not 2 <= len(source_provider) <= 120
            or not re.fullmatch(r"[A-Za-z0-9 .&()/:-]+", source_provider)
            or not isinstance(revision_summary, str)
            or not 16 <= len(revision_summary) <= 220
            or not re.fullmatch(r"[A-Za-z0-9 ,.;:()/-]+", revision_summary)):
        raise ValueError("Untrusted proposed final commentary metadata")
    try:
        original = private_conf.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("Original SWORD .conf not valid UTF-8") from None
    if ("\r" in original or
            _exact_conf_value(original, "Version") != expected_module_version or
            original.count(f"[{expected_module_id}]") != 1 or
            _exact_conf_value(original, "ModDrv") != "zCom" or
            _exact_conf_value(original, "SourceType") != "OSIS" or
            not _exact_conf_value(original, "DistributionLicense").strip() or
            _exact_conf_value(original, "SwordVersionDate") != original_sword_version_date):
        raise ValueError("Original private SWORD commentary metadata unexpectedly changed")
    if _iso_day(proposed_public_revision_day) <= _iso_day(original_sword_version_date):
        raise ValueError("New edited commentary revision cannot carry an inherited source date")
    old_about = _exact_conf_value(original, "About")
    if not old_about:
        raise ValueError("Original upstream About provenance missing")
    # This is an attributed presentation of the *exact upstream About*, not
    # a rephrasing of the authorial text. SWORD About uses literal \par tokens.
    notice = (
        f"Bible Resources edited module {expected_module_id} "
        f"version {expected_module_version}. {revision_summary}. "
        "The historical printed-edition equivalence claim in the original "
        f"{source_provider} description below is inherited upstream and has NOT been "
        "independently verified by Bible Resources."
        rf"\par\parOriginal upstream {source_provider} About (verbatim):\par"
    )
    revised_about = notice + old_about
    # Only changes SwordVersionDate and About; preserve every other line,
    # comments, history entry, licence, source URL and source configuration.
    staged = original.replace(
        f"SwordVersionDate={original_sword_version_date}\n",
        f"SwordVersionDate={proposed_public_revision_day}\n",
        1,
    ).replace(
        f"About={old_about}\n",
        f"About={revised_about}\n",
        1,
    )
    if staged == original or _exact_conf_value(staged, "About") != revised_about:
        raise ValueError("Proposed public SWORD metadata fields not found exactly")
    restored = staged.replace(
        f"About={revised_about}\n",
        f"About={old_about}\n",
        1,
    ).replace(
        f"SwordVersionDate={proposed_public_revision_day}\n",
        f"SwordVersionDate={original_sword_version_date}\n",
        1,
    )
    if restored != original:
        raise ValueError("Unapproved metadata besides explicit About/date proposal changed")
    if (staged.count(f"SwordVersionDate={proposed_public_revision_day}\n") != 1
            or staged.count(f"About={revised_about}\n") != 1
            or not _exact_conf_value(staged, "History_" + expected_module_version)
            or _exact_conf_value(staged, "DistributionLicense")
               != _exact_conf_value(original, "DistributionLicense")):
        raise ValueError("Original source/license or verified history lost in public proposal")
    proposed = staged.encode("utf-8")
    return proposed, {
        "status": "PROVISIONAL_PUBLIC_SWORD_COMMENTARY_METADATA_TWO_FIELDS_ONLY_NOT_APPROVED",
        "exact_changed_fields": ["About", "SwordVersionDate"],
        "original_private_conf_sha256": sha256(private_conf).hexdigest(),
        "proposed_public_conf_sha256": sha256(proposed).hexdigest(),
        "original_upstream_about_verbatim_preserved_with_explicit_attribution": True,
        "original_source_date_retained_in_private_original_provenance": True,
        "new_revision_date_not_inherited_from_upstream": True,
        "all_other_fields_comments_license_textsource_and_history_exact": True,
        "proposed_day_must_match_actual_approved_release_day": True,
        "publication_authorized": False,
        "public_asset_generated": False,
    }



def rehearse_private_versioned_commentary_package(
        original_install_root: Path, scratch: Path, *,
        module_id: str, expected_version: str, source_provider: str,
        original_sword_version_date: str, hypothetical_revision_day: str,
        revision_summary: str) -> dict:
    """Create and privately reinstall a deterministic, never-published ZIP.

    Reuse the already installed and native-verified SWORD zCom binary members.
    Change ONLY the independently checked About/SwordVersionDate fields and
    read all seven rebuilt files back. The hypothetical date is strictly a
    test input, never approval of a public version date or permission to ship.
    Callers must verify libSWORD's complete native corpus after this function.
    """
    if (not isinstance(original_install_root, Path)
            or not original_install_root.is_dir()
            or original_install_root.is_symlink()
            or not isinstance(scratch, Path)
            or not scratch.is_dir() or scratch.is_symlink()
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,79}", module_id)
            or not re.fullmatch(r"\d+\.\d+\.\d+", expected_version)):
        raise ValueError("Untrusted private commentary package rehearsal paths")
    folder = module_id.lower()
    source_conf = original_install_root / "mods.d" / (folder + ".conf")
    if (source_conf.is_symlink() or not source_conf.is_file()
            or source_conf.stat().st_size > 128 * 1024):
        raise ValueError("Source-reviewed original SWORD configuration missing")
    source_bytes = source_conf.read_bytes()
    private_conf = source_bytes.decode("utf-8")
    if (_exact_conf_value(private_conf, "DataPath")
            != "./modules/comments/zcom/" + folder + "/"
            or _exact_conf_value(private_conf, "Version") != expected_version
            or _exact_conf_value(private_conf, "ModDrv") != "zCom"
            or _exact_conf_value(private_conf, "SourceType") != "OSIS"
            or _exact_conf_value(private_conf, "CompressType") not in ("ZIP", "LZSS", "BZIP2", "XZ")):
        raise ValueError("Private compiled configuration does not describe expected zCom")
    block = _exact_conf_value(private_conf, "BlockType")
    suffixes = zcom_member_suffixes(block)
    expected_members = {
        "mods.d/" + folder + ".conf",
        *("modules/comments/zcom/" + folder + "/" + name for name in suffixes),
    }
    data_folder = original_install_root / "modules/comments/zcom" / folder
    if data_folder.is_symlink() or not data_folder.is_dir():
        raise ValueError("Untrusted private SWORD compressed-data location")
    if any(path.is_symlink() or not path.is_file() for path in data_folder.iterdir()):
        raise ValueError("Compiled data contains symbolic links or unreviewed directories")
    if {p.name for p in data_folder.iterdir()} != set(suffixes):
        raise ValueError("Missing, extra or incorrectly named compiled SWORD members")
    staged_conf, proposal = prepare_provisional_public_commentary_conf(
        source_bytes, expected_module_id=module_id,
        expected_module_version=expected_version,
        source_provider=source_provider,
        original_sword_version_date=original_sword_version_date,
        proposed_public_revision_day=hypothetical_revision_day,
        revision_summary=revision_summary,
    )
    members = {"mods.d/" + folder + ".conf": staged_conf}
    for member in sorted(expected_members - set(members)):
        source = original_install_root / member
        if (source.is_symlink() or not source.is_file()
                or not 0 < source.stat().st_size < 32 * 1024 * 1024):
            raise ValueError("Untrusted compiled SWORD member length or file type")
        members[member] = source.read_bytes()
    if (set(members) != expected_members
            or sum(map(len, members.values())) > 64 * 1024 * 1024):
        raise ValueError("Rehearsal member inventory violates native SWORD contract")

    def deterministic_archive() -> bytes:
        destination = BytesIO()
        # Match the actual public catalogue builder's deterministic ZIP,
        # rather than the original private compiler probe's STORED ZIP.
        with zipfile.ZipFile(
                destination, "w", compression=zipfile.ZIP_DEFLATED,
                compresslevel=9) as package:
            for name, content in sorted(members.items()):
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                package.writestr(info, content)
        return destination.getvalue()

    zip_bytes = deterministic_archive()
    if zip_bytes != deterministic_archive():
        raise ValueError("SWORD rehearsal ZIP output is not deterministic")
    package_path = scratch / "PRIVATE-REHEARSAL-DO-NOT-RELEASE.zip"
    install = scratch / "private-rehearsed-install"
    if (package_path.exists() or package_path.is_symlink()
            or install.exists() or install.is_symlink()):
        raise ValueError("Private rehearsal may not overwrite earlier output")
    package_path.write_bytes(zip_bytes)
    install.mkdir()
    with zipfile.ZipFile(BytesIO(package_path.read_bytes())) as package:
        if (set(package.namelist()) != expected_members
                or len(package.infolist()) != len(expected_members)):
            raise ValueError("Private package ZIP inventory changed in transit")
        for info in package.infolist():
            if (info.is_dir() or info.filename not in members
                    or package.read(info) != members[info.filename]):
                raise ValueError("Private SWORD ZIP extraction differs from compiled source")
            output = install / info.filename
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(members[info.filename])
    # Never recompress or transform authorial content, notes or native links.
    original_binary_sha = {}
    for name in sorted(expected_members - {"mods.d/" + folder + ".conf"}):
        a = original_install_root / name
        b = install / name
        if a.read_bytes() != b.read_bytes():
            raise ValueError("Rehearsal changed a compiled commentary source member")
        original_binary_sha[name] = sha256(b.read_bytes()).hexdigest()
    if (not proposal["all_other_fields_comments_license_textsource_and_history_exact"]
            or proposal["publication_authorized"] is not False
            or proposal["public_asset_generated"] is not False):
        raise ValueError("Private rehearsal wrongly implies publication authority")
    return {
        "status": "PRIVATE_FULL_CONF_AND_SWORD_ZCOM_ZIP_REHEARSAL_NOT_RELEASE",
        "module_id": module_id,
        "version": expected_version,
        "compiled_block_type": block,
        "original_sword_version_date": original_sword_version_date,
        "hypothetical_revision_day_only": hypothetical_revision_day,
        "source_conf_sha256": sha256(source_bytes).hexdigest(),
        "proposed_conf_sha256": sha256(staged_conf).hexdigest(),
        "all_six_native_compiled_members_preserved": len(original_binary_sha) == 6,
        "native_member_sha256": original_binary_sha,
        "zip_sha256": sha256(zip_bytes).hexdigest(),
        "zip_member_count": len(expected_members),
        "reinstalled_member_bytes_match_exactly": True,
        "only_about_and_sword_version_date_changed": True,
        "actual_release_date_selected": False,
        "owner_release_authorized": False,
        "artifact_published_or_uploaded": False,
    }



def reconcile_private_rebuild_package_evidence(
        attestation: dict, rehearsal: dict, *,
        original_install_root: Path, rehearsal_install_root: Path,
        rehearsal_zip_path: Path) -> dict:
    """Reconcile full native attestation with the seven exact test-ZIP members.

    Metadata-only private evidence, not a chosen release day or permission
    to modify an approved module, its catalogue or existing releases.
    """
    import json

    if (not isinstance(attestation, dict) or not isinstance(rehearsal, dict)
            or any(not isinstance(p, Path) or p.is_symlink()
                   for p in (original_install_root, rehearsal_install_root,
                             rehearsal_zip_path))
            or not original_install_root.is_dir()
            or not rehearsal_install_root.is_dir()
            or not rehearsal_zip_path.is_file()
            or rehearsal_zip_path.stat().st_size > 64 * 1024 * 1024):
        raise ValueError("Unsafe or missing private SWORD evidence")
    audit = attestation.get("source_audit")
    review = attestation.get("review_manifest")
    validation = attestation.get("source_validation")
    if any(not isinstance(x, dict) for x in (audit, review, validation)):
        raise ValueError("Native audit and review manifest missing")
    audit_sha = sha256((json.dumps(audit, sort_keys=True, indent=2) + "\n").encode()).hexdigest()
    native_sha = rehearsal.get("native_corpus_sha256")
    if (attestation.get("status") != "PRIVATE_REAL_NATIVE_ATTESTATION_DRAFT_NOT_RELEASE"
            or attestation.get("release_authorized") is not False
            or attestation.get("data_text_exported") is not False
            or audit.get("status") != "complete_native_rebuild_comparison"
            or audit.get("source_kind") != "reviewed_compiled_commentary_rebuild"
            or audit.get("full_original_and_rebuilt_native_inventory_compared") is not True
            or review.get("status") != "private_draft_not_owner_authorized_for_release"
            or validation.get("status") != "private_draft_not_release_validated"
            or any(x != audit_sha for x in (
                attestation.get("source_audit_sha256"),
                review.get("source_audit_sha256"),
                validation.get("source_audit_sha256")))
            or not re.fullmatch(r"[a-f0-9]{64}", native_sha or "")
            or any(x != native_sha for x in (
                audit.get("candidate_native_corpus_sha256"),
                review.get("candidate_native_corpus_sha256"),
                validation.get("candidate_native_corpus_sha256")))):
        raise ValueError("Private source/native attestation does not reconcile")
    module_id = rehearsal.get("module_id")
    version = rehearsal.get("version")
    block = rehearsal.get("compiled_block_type")
    if (not isinstance(module_id, str)
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,79}", module_id)
            or not isinstance(version, str)
            or not re.fullmatch(r"\d+\.\d+\.\d+", version)
            or review.get("sword_id") != module_id
            or review.get("version") != version
            or review.get("block_type") != block
            or rehearsal.get("status")
               != "PRIVATE_FULL_CONF_AND_SWORD_ZCOM_ZIP_REHEARSAL_NOT_RELEASE"
            or rehearsal.get("zip_member_count") != 7
            or rehearsal.get("only_about_and_sword_version_date_changed") is not True
            or rehearsal.get("all_six_native_compiled_members_preserved") is not True
            or rehearsal.get("reinstalled_member_bytes_match_exactly") is not True
            or rehearsal.get("complete_rehearsed_libsword_native_readback_exact") is not True
            or any(rehearsal.get(k) is not False for k in (
                "actual_release_date_selected", "owner_release_authorized",
                "artifact_published_or_uploaded"))):
        raise ValueError("Unsafe private rehearsal identity or approval claim")
    if (not isinstance(rehearsal.get("hypothetical_revision_day_only"), str)
            or not _iso_day(rehearsal["hypothetical_revision_day_only"])
            > _iso_day(rehearsal["original_sword_version_date"])):
        raise ValueError("Hypothetical day must follow original source revision")
    folder = module_id.lower()
    config_name = "mods.d/" + folder + ".conf"
    expected = {
        config_name,
        *("modules/comments/zcom/" + folder + "/" + suffix
          for suffix in zcom_member_suffixes(block)),
    }
    old_hashes = review.get("payload_sha256")
    native_hashes = rehearsal.get("native_member_sha256")
    if (not isinstance(old_hashes, dict) or set(old_hashes) != expected
            or not isinstance(native_hashes, dict)
            or set(native_hashes) != expected - {config_name}
            or old_hashes[config_name] != rehearsal.get("source_conf_sha256")):
        raise ValueError("Original attested seven member inventory incomplete")
    staged_hashes = {}
    for name in sorted(expected):
        original = original_install_root / name
        staged = rehearsal_install_root / name
        if (any(p.is_symlink() or not p.is_file()
                or not 0 < p.stat().st_size <= 32 * 1024 * 1024
                for p in (original, staged))):
            raise ValueError("Untrusted SWORD config or compiled native member")
        original_sha = sha256(original.read_bytes()).hexdigest()
        staged_sha = sha256(staged.read_bytes()).hexdigest()
        if original_sha != old_hashes[name]:
            raise ValueError("Original compiled member no longer matches source proof")
        if name == config_name:
            if (staged_sha != rehearsal.get("proposed_conf_sha256")
                    or staged_sha == original_sha):
                raise ValueError("Prepared conf hash did not reconcile")
        elif staged_sha != original_sha or staged_sha != native_hashes[name]:
            raise ValueError("Compiled original zCom member changed during rehearsal")
        staged_hashes[name] = staged_sha
    try:
        with zipfile.ZipFile(rehearsal_zip_path) as package:
            if (len(package.infolist()) != 7
                    or set(package.namelist()) != expected
                    or package.testzip() is not None):
                raise ValueError("Private SWORD ZIP member inventory corrupt")
            for member in package.infolist():
                if (member.is_dir()
                        or member.compress_type != zipfile.ZIP_DEFLATED
                        or sha256(package.read(member)).hexdigest()
                           != staged_hashes[member.filename]):
                    raise ValueError("Private SWORD ZIP differs from installed native members")
    except zipfile.BadZipFile as exc:
        raise ValueError("Corrupt private ZIP") from exc
    package_sha = sha256(rehearsal_zip_path.read_bytes()).hexdigest()
    if package_sha != rehearsal.get("zip_sha256"):
        raise ValueError("Private ZIP bytes differ from prior private rehearsal")
    return {
        "status": "PRIVATE_NATIVE_AND_TEST_DATE_ZIP_SEVEN_FILES_RECONCILED_NOT_RELEASE",
        "source_audit_sha256": audit_sha,
        "candidate_native_corpus_sha256": native_sha,
        "test_date_only_seven_member_sha256": staged_hashes,
        "test_date_only_zip_sha256": package_sha,
        "hypothetical_revision_day_only": rehearsal["hypothetical_revision_day_only"],
        "actual_release_date_selected": False,
        "release_authorized": False,
        "catalogue_changed": False,
        "public_artifact_generated": False,
    }
