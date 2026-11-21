#!/usr/bin/env python3
"""Audit independent v1 editorial dispositions for *all* frozen UBS WLC gaps.

The generated family register is deliberately machine classification only.
Do not edit that register or treat its candidate list as editorial approval.
All nonlinked source words, composite Strong strings and revisions remain
unchanged. This report is an acceptance-worklist audit, not a release signal.
"""
from __future__ import annotations

import argparse
import json
import unicodedata
from collections import Counter
from pathlib import Path

DISPOSITION_SOURCES = (
    "edition_headword_scope_exclusions",
    "composite_source_code_preservations",
    "lexical_nonidentity_rejections",
    "multiple_headword_abstentions",
    "grammatical_morpheme_nonlinks",
    "single_candidate_abstentions",
    "positive_headword_only_reviews",
)

SOURCE_REASON = {
    "edition_headword_scope_exclusions": "unattested_indexed_headword",
    "composite_source_code_preservations": "source_strong_unreadable",
}
LEXICAL_REASONS = {
    "different_strong_exact_attested_lemma",
    "different_strong_same_consonants",
    "same_strong_family_unresolved",
}


def family_key(record):
    """Use original full Strong syntax, not a guessed numeric alias."""
    return (
        record["lang"],
        unicodedata.normalize("NFC", record["lemma"]),
        record["original_strong"],
    )


def _source_revisions(register, scope, ledgers):
    editions = register["source_editions"]
    if (scope["ubs_revision"], scope["macula_revision"]) != (
        editions["ubs_revision"], editions["macula_revision"]
    ):
        raise ValueError("Edition scope source revisions have drifted")
    for name, ledger in ledgers.items():
        if ledger["source_editions"] != editions:
            raise ValueError(f"{name}: original source revisions have drifted")
    return editions


def collect(register, scope, ledgers, index=None):
    """Produce a lossless and disjoint inventory of human editorial outcomes.

    These are dispositions *of unresolved original word families*, not
    generated links. Accepted headword identities may remain unlinked.
    """
    editions = _source_revisions(register, scope, ledgers)
    families = {family_key(f): f for f in register["families"]}
    if len(families) != len(register["families"]):
        raise ValueError("Duplicate original family keys")
    summary = register["summary"]
    if (sum(f["occurrences"] for f in families.values())
            != summary["unresolved_occurrences"]):
        raise ValueError("Original unresolved occurrence conservation failed")

    seen = {}
    counted = Counter()

    def register_decision(source, decision, occurrence_field):
        key = family_key(decision)
        f = families.get(key)
        if f is None:
            raise ValueError(f"{source}: unknown source family key: {key}")
        if key in seen:
            raise ValueError(
                f"Editorial family recorded twice: {key}: {seen[key]} and {source}"
            )
        if decision[occurrence_field] != f["occurrences"]:
            raise ValueError(f"{source}: original occurrence count drift: {key}")
        if source in SOURCE_REASON:
            if f["reason"] != SOURCE_REASON[source]:
                raise ValueError(f"{source}: source reason mismatch: {key}")
        elif f["reason"] not in LEXICAL_REASONS:
            raise ValueError(f"{source}: unsupported lexical reason: {key}")

        if source == "lexical_nonidentity_rejections":
            if (decision["decision"] != "candidate_lexical_nonidentity"
                    or f["ubs_candidate_entries"] !=
                    [decision["ubs_candidate"]["main_id"]]):
                raise ValueError(f"{source}: not an original sole-candidate rejection")
        elif source == "multiple_headword_abstentions":
            if (decision["disposition"] !=
                    "retain_unlinked_ambiguous_headword_choice"
                    or len(f["ubs_candidate_entries"]) < 2
                    or decision["ubs_candidate_entries"] != f["ubs_candidate_entries"]):
                raise ValueError(f"{source}: not a valid multiple-candidate abstention")
        elif source == "grammatical_morpheme_nonlinks":
            if (decision["decision"] !=
                    "retain_unlinked_source_morpheme_not_candidate_headword"
                    or f["ubs_candidate_entries"] !=
                    [decision["ubs_candidate_entry_id"]]):
                raise ValueError(f"{source}: source segment candidate changed")
        elif source == "single_candidate_abstentions":
            if (decision["disposition"] !=
                    "reversible_single_candidate_identity_abstention"
                    or f["ubs_candidate_entries"] !=
                    [decision["ubs_candidate"]["main_id"]]
                    or len(f["ubs_candidate_entries"]) != 1
                    or decision["lexical_identity_approved"] is not False
                    or decision["contextual_sense_approved"] is not False
                    or decision["index_word_links_applied"] is not False):
                raise ValueError(f"{source}: unsafe or unverified lexical abstention")
        elif source == "positive_headword_only_reviews":
            if (decision["disposition"] !=
                    "source_reviewed_ubs_headword_entry_only"
                    or f["ubs_candidate_entries"] !=
                    [decision["ubs_candidate_main_id"]]
                    or decision["contextual_sense_id_approved"] is not False
                    or decision["index_word_links_applied"] is not False):
                raise ValueError(f"{source}: unsafe or changed positive identity")
        elif source == "edition_headword_scope_exclusions":
            if (decision["disposition"] !=
                    "approved_ubs_0_9_4_indexed_headword_scope_exclusion"
                    or f["ubs_candidate_entries"]):
                raise ValueError(f"{source}: not a source-tested scope exclusion")
        elif source == "composite_source_code_preservations":
            if (decision["disposition"] !=
                    "preserve_composite_source_code_pending_original_annotation_review"
                    or "|" not in f["original_strong"]):
                raise ValueError(f"{source}: composite Strong was altered")
        # The original negative-candidate ledger predates the explicit
        # no-mutation flag. Its read-only source verifier independently
        # validates original MACULA words. Missing legacy flag means no
        # mutation was requested, never permission to modify originals.
        if source == "lexical_nonidentity_rejections":
            changed = decision.get("source_data_modified", False)
        else:
            changed = decision.get("source_data_modified")
        if changed is not False:
            raise ValueError(f"{source}: source modification was not forbidden")
        seen[key] = source
        counted[source + "_families"] += 1
        counted[source + "_occurrences"] += f["occurrences"]

    for d in scope["dispositions"]:
        f = families.get(family_key(d))
        if f is None:
            raise ValueError("Unknown edition-scope original family")
        source = (
            "edition_headword_scope_exclusions"
            if f["reason"] == "unattested_indexed_headword"
            else "composite_source_code_preservations"
        )
        register_decision(source, d, "original_occurrences")

    for source, field in (
        ("lexical_nonidentity_rejections", "occurrences"),
        ("multiple_headword_abstentions", "original_occurrences"),
        ("grammatical_morpheme_nonlinks", "original_occurrences"),
        ("single_candidate_abstentions", "original_occurrences"),
        ("positive_headword_only_reviews", "original_occurrences"),
    ):
        ledger = ledgers[source]
        records = (ledger["dispositions"] if source in (
            "multiple_headword_abstentions", "single_candidate_abstentions"
        ) else ledger["decisions"])
        for d in records:
            register_decision(source, d, field)

    excluded = counted["edition_headword_scope_exclusions_occurrences"]
    if excluded != summary["outside_scope_occurrences"]:
        raise ValueError("Edition-scope exclusion count changed")

    covered = sum(counted[source + "_occurrences"] for source in DISPOSITION_SOURCES)
    pending = [f for k, f in families.items() if k not in seen]
    pending.sort(key=lambda f: (-f["occurrences"], f["lang"], f["lemma"], f["original_strong"]))
    pending_occ = sum(f["occurrences"] for f in pending)
    if covered + pending_occ != summary["unresolved_occurrences"]:
        raise ValueError("Original unresolved word counts not conserved")
    if len(seen) + len(pending) != summary["unresolved_families"]:
        raise ValueError("Original unresolved family counts not conserved")

    in_scope_lexically_dispositioned = sum(
        counted[source + "_occurrences"] for source in (
            "lexical_nonidentity_rejections",
            "multiple_headword_abstentions",
            "grammatical_morpheme_nonlinks",
            "single_candidate_abstentions",
            "positive_headword_only_reviews",
        )
    )
    in_scope_with_any_decision = (
        in_scope_lexically_dispositioned
        + counted["composite_source_code_preservations_occurrences"]
    )
    if (in_scope_with_any_decision + pending_occ !=
            summary["inside_scope_unresolved_occurrences"]):
        raise ValueError("In-scope disposition conservation failed")
    if index is not None:
        index_scope = index["coverage_scope"]
        expected = {
            "original_lexical_source_occurrences": summary["lexical_source_occurrences"],
            "linked_occurrences": summary["linked_occurrences"],
            "outside_indexed_headword_scope": excluded,
            "indexable_unresolved": summary["inside_scope_unresolved_occurrences"],
        }
        if any(index_scope.get(k) != v for k, v in expected.items()):
            raise ValueError("Frozen dictionary-index scope disagrees with family register")

    count_report = {
        "original_lexical_occurrences": summary["lexical_source_occurrences"],
        "already_linked_occurrences": summary["linked_occurrences"],
        "original_unresolved_families": summary["unresolved_families"],
        "original_unresolved_occurrences": summary["unresolved_occurrences"],
        "edition_scope_excluded_occurrences": excluded,
        "in_scope_unresolved_occurrences_at_baseline": summary[
            "inside_scope_unresolved_occurrences"
        ],
        "in_scope_lexically_dispositioned_occurrences": in_scope_lexically_dispositioned,
        "composite_source_syntax_preserved_occurrences": counted[
            "composite_source_code_preservations_occurrences"
        ],
        "in_scope_occurrences_with_any_disposition": in_scope_with_any_decision,
        "in_scope_families_with_any_disposition": sum(
            counted[source + "_families"] for source in DISPOSITION_SOURCES
            if source != "edition_headword_scope_exclusions"
        ),
        "in_scope_lexical_family_dispositions": sum(
            counted[source + "_families"] for source in (
                "lexical_nonidentity_rejections",
                "multiple_headword_abstentions",
                "grammatical_morpheme_nonlinks",
                "single_candidate_abstentions",
                "positive_headword_only_reviews",
            )
        ),
        "not_yet_dispositioned_original_families": len(pending),
        "not_yet_dispositioned_original_occurrences": pending_occ,
    }
    for name in DISPOSITION_SOURCES:
        count_report[name] = {
            "families": counted[name + "_families"],
            "occurrences": counted[name + "_occurrences"],
        }
    return {
        "schema_version": 1,
        "format": "bsi-ubs-hebrew-v1-read-only-editorial-coverage-audit",
        "source_editions": editions,
        "policy": {
            "machine_classifications_are_not_editorial_dispositions": True,
            "source_text_modified": False,
            "automatic_contextual_sense_inference": False,
            "publication_approved": False,
            "remaining_is_not_a_claim_of_dictionary_absence": True,
        },
        "counts": count_report,
        "pending_families": [
            {
                "lang": f["lang"], "lemma": f["lemma"],
                "original_strong": f["original_strong"],
                "original_occurrences": f["occurrences"],
                "classification": f["reason"],
                "original_word_witness": f["source_witnesses"][0],
                "ubs_candidate_entries": f["ubs_candidate_entries"],
            }
            for f in pending
        ],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("register", "scope", "nonidentity", "ambiguous",
                 "morphemes", "single", "positive", "index", "output"):
        p.add_argument("--" + name, required=True, type=Path)
    args = p.parse_args()
    ledgers = {
        "lexical_nonidentity_rejections": json.loads(args.nonidentity.read_text(encoding="utf-8")),
        "multiple_headword_abstentions": json.loads(args.ambiguous.read_text(encoding="utf-8")),
        "grammatical_morpheme_nonlinks": json.loads(args.morphemes.read_text(encoding="utf-8")),
        "single_candidate_abstentions": json.loads(args.single.read_text(encoding="utf-8")),
        "positive_headword_only_reviews": json.loads(args.positive.read_text(encoding="utf-8")),
    }
    report = collect(
        json.loads(args.register.read_text(encoding="utf-8")),
        json.loads(args.scope.read_text(encoding="utf-8")),
        ledgers,
        json.loads(args.index.read_text(encoding="utf-8")),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("UBS_V1_EDITORIAL_COVERAGE", json.dumps(report["counts"], sort_keys=True))
    for f in report["pending_families"][:12]:
        print("UBS_V1_PENDING_FAMILY", json.dumps(f, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

