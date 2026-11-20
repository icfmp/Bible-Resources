#!/usr/bin/env python3
"""Build the public, identifier-only BSI UBS Greek NT v0.1.0 distribution.

Consumes the separately source-pinned and verified PRIVATE full-corpus index.
Only a strict allowlist of original MACULA word IDs and UBS MainId/LEXID
identifiers, ambiguity statuses and provisional evidence tiers can leave this
step. Never export the original Greek, Strong, Louw-Nida, morph, glosses,
verse text or original UBS dictionary definitions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

VERSION = "0.1.0"
TAG = "bsi-ubs-greek-v0.1.0"
FILE_NAME = "BSI-UBS-Greek-0.1.0.zip"
SOURCE_MACULA = "8423afe47b9e8f24b7772e808af45c7159a6fe7e"
SOURCE_UBS = "a15a96cfaa4ca18a6c0339016645ba1e534db3c8"
VALID_STATUSES = {
    "provisional_ubs_lexid": 123195,
    "ubs_entry_only": 12288,
    "ambiguous_ubs_senses": 2207,
    "ambiguous_ubs_headwords": 4,
    "missing_ubs_headword": 47,
}
VALID_TIERS = {
    "ln_unique": 122504,
    "single_sense_without_ln": 170,
    "explicit_ubs_form": 223,
    "ubs_verse_citation": 258,
    "calibrated_ubs_word_locator": 40,
}
MACULA_ID = re.compile(r"^n\d{11}$")
UBS_ID = re.compile(r"^\d{15}$")
README = """# Bible Semantic Index — UBS Greek NT lexical crosswalk v0.1.0

An offline **identifier-only** crosswalk from original MACULA SBLGNT
word IDs to source-supported UBS Greek New Testament Dictionary 1.0
lexical headwords and **provisional** candidate sense IDs.

This is NOT a SWORD dictionary, not a Greek Bible text, and not an
independently verified word-sense disambiguation. Refer to the original
UBS EN/FR edition 1.0 for any actual definitions. No external service
is contacted by the index at runtime.

Read `index.json` and look up a token's exact `by_word_id` key.
Each value contains:
- `status`: one of provisional_ubs_lexid, ubs_entry_only,
  ambiguous_ubs_senses, ambiguous_ubs_headwords, missing_ubs_headword;
- `entry_ids`: zero, one, or several authentic UBS MainIds;
- `provisional_lexid`: an original UBS LEXID or null, **never a
  certified contextual sense**;
- `candidate_lexids`: all originally LN-supported alternatives,
  not a claim that other UBS dictionary senses are impossible;
- `evidence_tier`: provenance of a provisional recommendation or null.

Words with no unique sense remain entry-only or ambiguous. No
forced headword or artificial UBS sense ID is ever introduced.

The index intentionally excludes Greek verse text, original source
lemma, Strong/LN annotations, glosses, original morphology, UBS
definitions, prose and dictionary reference quotations. Its only
original corpus keys are MACULA word identifiers. The five source
evidence tiers remain explicitly provisional, with **zero**
independently verified contextual interpretations claimed.

See ATTRIBUTION.md for exact source/edition provenance, licensing
links, transformation notice and third-party annotation caveat.
The public research edition is CC BY-SA 4.0 with appropriate source
attribution. This standalone index is not yet an integration into
the Bible application.
"""
ATTRIBUTION = """# Attribution, provenance and change notice

**Combined identifier-only index (Bible Semantic Index, v0.1.0):**
distributed under Creative Commons Attribution-ShareAlike 4.0 International:
https://creativecommons.org/licenses/by-sa/4.0/

**UBS Dictionary of the Greek New Testament, edition 1.0 (English,
French)** — © United Bible Societies, 2023; adapted from the Semantic
Dictionary of Biblical Greek © United Bible Societies 2018–2023 and
Louw & Nida's Greek-English Lexicon of the New Testament Based on
Semantic Domains © United Bible Societies 1988/1989. The original
UBS source credits the Scripture reference contribution to SIL.
Original source: https://github.com/ubsicap/ubs-open-license
Pinned revision: a15a96cfaa4ca18a6c0339016645ba1e534db3c8
Greek dictionary notice:
https://github.com/ubsicap/ubs-open-license/blob/a15a96cfaa4ca18a6c0339016645ba1e534db3c8/dictionaries/greek/README.md
License: CC BY-SA 4.0 (link above).

**MACULA Greek Linguistic Datasets, SBLGNT** —
© 2022–2024 Biblica, Inc., CC BY 4.0.
Original authorship and attribution: "MACULA Greek Linguistic Datasets,
available at https://github.com/Clear-Bible/macula-greek/".
Pinned revision: 8423afe47b9e8f24b7772e808af45c7159a6fe7e
Original license and component notices:
https://github.com/Clear-Bible/macula-greek/blob/8423afe47b9e8f24b7772e808af45c7159a6fe7e/LICENSE.md
CC BY 4.0: https://creativecommons.org/licenses/by/4.0/

MACULA contains separately originated material. Its original license
lists UBS MARBLE semantic word annotations as 'used with permission',
as well as third-party Greek Bible text and glosses. Those annotations,
original verse text, original Greek, original LN codes and their data
fields are **not shipped here**. The source-derived word-ID identifiers
alone are included to connect the independent crosswalk to the
underlying edition.

**Modifications and transformations:** Bible Resources combined,
audited, normalized and conservatively cross-referenced identifiers
from the two pinned original sources, preserving genuine ambiguous and
unsupported cases instead of inventing semantic identities. No
source definitions or Greek verse text were copied. Sense links are
labeled provisional; they were not semantically verified one by one.
See the reconstruction scripts and tests under
https://github.com/icfmp/Bible-Resources/tree/main/entity-index/links/dictionaries/ubs-greek

No upstream organization endorses this independently prepared index.
"""
ZIP_DATE = (2026, 1, 1, 0, 0, 0)


def _verify_source(source: dict) -> None:
    if (source.get("status") !=
            "PRIVATE_REPRODUCIBLE_UBS_Greek_NT_v1_original_word_candidate_INDEX_NOT_PUBLISHED"
            or source.get("original_word_ids") != 137741
            or source.get("reviewed_source_lexical_headword_words") != 137694
            or source.get("provisional_semantic_word_ids") != 123195
            or source.get("not_assigned_a_provisional_sense") != 14546
            or source.get("provisional_evidence_tiers") != VALID_TIERS
            or source.get("word_status_counts") != VALID_STATUSES
            or source.get("semantic_context_independently_verified") != 0
            or source.get("publication_approved") is not False
            or source.get("original_index_and_sources_modified") is not False):
        raise ValueError("Original private UBS Greek source-pinned review report drift")
    editions = source["source_editions"]
    revisions = json.dumps(editions)
    if SOURCE_MACULA not in revisions or SOURCE_UBS not in revisions:
        raise ValueError("Unknown original source revisions")
    if len(source.get("by_original_macula_word_id", {})) != 137741:
        raise ValueError("Missing or duplicate original-word ID records")


def _ids(items: list[str]) -> list[str]:
    if not isinstance(items, list) or len(items) != len(set(items)):
        raise ValueError("UBS IDs not a unique list")
    if any(not isinstance(v, str) or not UBS_ID.fullmatch(v) for v in items):
        raise ValueError("Malformed source UBS MainId / LEXID")
    return items


def project(source: dict) -> dict:
    """Deliberately drop every source field not explicitly allowed."""
    _verify_source(source)
    rows = {}
    counts = Counter()
    tiers = Counter()
    for wid, record in source["by_original_macula_word_id"].items():
        if not MACULA_ID.fullmatch(wid):
            raise ValueError("Noncanonical original MACULA word ID")
        status = record["status"]
        if status not in VALID_STATUSES:
            raise ValueError("Unsupported public word status")
        entries = _ids(record["ubs_main_ids"])
        candidates = _ids(record["ubs_lexid_candidates_from_original_ln"])
        provisional = record["provisional_ubs_lexid"]
        tier = record["evidence_tier"]
        if provisional is not None and not (isinstance(provisional, str) and UBS_ID.fullmatch(provisional)):
            raise ValueError("Invalid UBS source sense ID")
        if ((status == "provisional_ubs_lexid") != (provisional is not None) or
            ((tier is not None) != (provisional is not None)) or
            (tier is not None and tier not in VALID_TIERS)):
            raise ValueError("Source provisional word sense mislabeled")
        if (status == "missing_ubs_headword") != (not entries):
            raise ValueError("Missing UBS lexical source inconsistency")
        if status == "ambiguous_ubs_headwords" and len(entries) < 2:
            raise ValueError("Original source headword ambiguities discarded")
        if status == "ambiguous_ubs_senses" and (len(entries) != 1 or len(candidates) < 2):
            raise ValueError("Original UBS sense alternatives discarded")
        if status in ("ubs_entry_only", "provisional_ubs_lexid", "ambiguous_ubs_senses") and len(entries) != 1:
            raise ValueError("Multiple/absent headword for normal source-linked word")
        if provisional is not None and candidates and provisional not in candidates and tier != "single_sense_without_ln":
            raise ValueError("Provisional UBS source sense absent from attested alternatives")
        counts[status] += 1
        if tier is not None:
            tiers[tier] += 1
        rows[wid] = {
            "status": status,
            "entry_ids": entries,
            "provisional_lexid": provisional,
            "candidate_lexids": candidates,
            "evidence_tier": tier,
        }
    if dict(counts) != VALID_STATUSES or dict(tiers) != VALID_TIERS:
        raise ValueError("Original word statuses / 5 provenance tiers differ")
    public = {
        "schema": "bsi.ubs-greek-word-crosswalk.v1",
        "version": VERSION,
        "upstream_ubs_edition": "1.0 EN/FR",
        "source_ubs_revision": SOURCE_UBS,
        "source_macula_revision": SOURCE_MACULA,
        "license": "CC BY-SA 4.0",
        "contextual_semantics_independently_verified": False,
        "counts": {
            "total_word_ids": 137741,
            "supported_lexical_word_ids": 137694,
            "provisional_sense_word_ids": 123195,
            "unassigned_sense_word_ids": 14546,
            "statuses": dict(sorted(counts.items())),
            "tiers": dict(sorted(tiers.items())),
        },
        "by_word_id": dict(sorted(rows.items())),
    }
    # Strict *published* field whitelist: all source LN, Strong, Greek and
    # morphology remain inside the existing private audit.
    allowed = {"schema", "version", "upstream_ubs_edition",
               "source_ubs_revision", "source_macula_revision", "license",
               "contextual_semantics_independently_verified", "counts", "by_word_id"}
    assert set(public) == allowed
    return public


def _json_bytes(record: dict) -> bytes:
    return (json.dumps(record, ensure_ascii=True, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("ascii")


def package(public: dict, output: Path) -> str:
    data = _json_bytes(public)
    manifest = {
        "file": "index.json",
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "format": "bsi.ubs-greek-word-crosswalk.v1",
        "version": VERSION,
        "license": "CC BY-SA 4.0",
        "word_count": 137741,
        "provisional_sense_count": 123195,
        "includes_dictionary_definitions": False,
        "includes_verse_text": False,
        "includes_original_ln_strong_morph_lemma": False,
    }
    contents = {
        "index.json": data,
        "manifest.json": _json_bytes(manifest),
        "README.md": README.encode("utf-8"),
        "ATTRIBUTION.md": ATTRIBUTION.encode("utf-8"),
    }
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9, allowZip64=True) as z:
        for name, blob in sorted(contents.items()):
            zi = zipfile.ZipInfo(filename=name, date_time=ZIP_DATE)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            zi.create_system = 3
            z.writestr(zi, blob, compress_type=zipfile.ZIP_DEFLATED,
                       compresslevel=9)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_name(output.name + ".sha256").write_text(
        digest + "  " + output.name + "\n", encoding="ascii")
    return digest


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--private-index", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.name != FILE_NAME:
        raise ValueError("Published archive name must exactly match fixed version")
    source = json.loads(args.private_index.read_text(encoding="utf-8"))
    public = project(source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    digest = package(public, args.output)
    print("BSI_UBS_GREEK_IDENTIFIER_ONLY_PUBLIC_PACKAGE_READY",
          json.dumps({"sha256": digest, "bytes": args.output.stat().st_size,
                      "words": len(public["by_word_id"]),
                      "license": public["license"],
                      "version": public["version"]}, sort_keys=True))


if __name__ == "__main__":
    main()
