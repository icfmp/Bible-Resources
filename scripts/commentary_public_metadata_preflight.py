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
import re


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
