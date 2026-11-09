"""Test source-neutral, private raw stock SWORD whole-corpus framing.

Synthetic byte streams deliberately contain newline/tab, malformed/duplicate
keys and incomplete data; no publisher Scripture or note text is included.
"""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sword_native_raw_corpus_inventory import (
    parse_native_raw_corpus, RawCorpusError, write_new_metadata_report
)


def record(kind, key, raw=b"synthetic"):
    return (f"{kind}\t{key}\t{len(raw)}\n".encode("ascii") + raw)


def sample():
    chunks = [
        record("U", "TOP:1", b"<div type='intro'>anonymous intro</div>"),
        record("I", "Gen", b"<title>book intro</title>"),
        record("I", "Gen.1", b"<p>chapter intro</p>"),
        record("K", "Gen.1.1", b"<p>body line 1\nbody line 2\tend</p>"),
        record("K", "Gen.1.2", "Unicode e\u0301 sequence".encode("utf-8")),
        record("K", "Exod.1.1", b"<w lemma='X'>synthetic</w>"),
        b"S\t6\t3\t2\t1\n",
    ]
    return b"".join(chunks)


class NativeWholeCorpusTests(unittest.TestCase):
    def test_private_stream_hashes_every_real_frame_and_intros(self):
        report, ordinary, intros, anonymous = parse_native_raw_corpus(io.BytesIO(sample()))
        self.assertEqual(ordinary, ["Gen.1.1", "Gen.1.2", "Exod.1.1"])
        self.assertEqual(intros, ["Gen", "Gen.1"])
        self.assertEqual(anonymous, ["TOP:1"])
        self.assertEqual(report["actual_occupied_numbered_entry_count"], 3)
        self.assertEqual(report["actual_occupied_intro_entry_count"], 2)
        self.assertEqual(report["actual_occupied_anonymous_top_entry_count"], 1)
        self.assertEqual(report["all_actual_raw_entries_scanned"], 6)
        self.assertEqual(len(report["all_native_raw_entries_ordered_sha256"]), 64)
        self.assertEqual([x["book"] for x in report["books_and_opaque_top"]],
                         ["_ANONYMOUS_TOP", "Gen", "Exod"])
        self.assertFalse(report["exact_text_punctuation_and_spacing_fidelity_verified"])
        self.assertFalse(report["source_original_authorial_text_compared"])
        self.assertFalse(report["published"])
        rendered = json.dumps(report)
        self.assertNotIn("anonymous intro", rendered)
        self.assertNotIn("body line", rendered)
        self.assertNotIn("synthetic</w>", rendered)

    def test_byte_difference_changes_compiled_corpus_sha(self):
        one, *_ = parse_native_raw_corpus(io.BytesIO(sample()))
        two, *_ = parse_native_raw_corpus(io.BytesIO(sample().replace(
            b"body line 1", b"body line 7")))
        self.assertNotEqual(one["all_native_raw_entries_ordered_sha256"],
                            two["all_native_raw_entries_ordered_sha256"])

    def test_reordered_source_records_change_hash_without_claiming_parity(self):
        before = sample()
        changed = before.replace(record("K", "Gen.1.1", b"<p>body line 1\nbody line 2\tend</p>"),
                                 record("K", "Gen.1.1", b"<p>body line 1\nbody line 2\tend</p>"))
        # no-op is stable, and a real reordering is distinguishable
        first, *_ = parse_native_raw_corpus(io.BytesIO(before))
        same, *_ = parse_native_raw_corpus(io.BytesIO(changed))
        self.assertEqual(first["all_native_raw_entries_ordered_sha256"],
                         same["all_native_raw_entries_ordered_sha256"])
        swapped = before.replace(record("K", "Gen.1.1", b"<p>body line 1\nbody line 2\tend</p>") +
                                 record("K", "Gen.1.2", "Unicode e\u0301 sequence".encode()),
                                 record("K", "Gen.1.2", "Unicode e\u0301 sequence".encode()) +
                                 record("K", "Gen.1.1", b"<p>body line 1\nbody line 2\tend</p>"))
        second, *_ = parse_native_raw_corpus(io.BytesIO(swapped))
        self.assertNotEqual(first["all_native_raw_entries_ordered_sha256"],
                            second["all_native_raw_entries_ordered_sha256"])

    def test_truncated_raw_body_blocks(self):
        broken = record("K", "Gen.1.1", b"too small")[:-3]
        with self.assertRaises(RawCorpusError):
            parse_native_raw_corpus(io.BytesIO(broken))

    def test_missing_or_wrong_completion_counts_block(self):
        for bad in [sample().replace(b"S\t6\t3\t2\t1\n", b""),
                    sample().replace(b"S\t6\t3\t2\t1\n", b"S\t6\t4\t2\t0\n"),
                    sample().replace(b"S\t6\t3\t2\t1\n", b"S\t6\t3\t2\t1\nEXTRA")]:
            with self.subTest(length=len(bad)), self.assertRaises(RawCorpusError):
                parse_native_raw_corpus(io.BytesIO(bad))

    def test_duplicate_verse_key_blocks(self):
        bad = (record("K", "Gen.1.1") + record("K", "Gen.1.1")
               + b"S\t2\t2\t0\t0\n")
        with self.assertRaisesRegex(RawCorpusError, "Repeated"):
            parse_native_raw_corpus(io.BytesIO(bad))

    def test_opaque_top_count_is_exact_and_ordered(self):
        bad = record("U", "TOP:2") + record("K", "Gen.1.1") + b"S\t2\t1\t0\t1\n"
        with self.assertRaisesRegex(RawCorpusError, "TOP"):
            parse_native_raw_corpus(io.BytesIO(bad))

    def test_non_utf8_raw_bytes_block(self):
        with self.assertRaisesRegex(RawCorpusError, "Non-UTF-8"):
            parse_native_raw_corpus(io.BytesIO(
                record("K", "Gen.1.1", b"\xff\xfe") + b"S\t1\t1\t0\t0\n"))

    def test_unknown_frame_or_native_key_blocks(self):
        for bad in [record("Z", "Gen.1.1"), record("K", "Gen.0.1"),
                    record("I", "Gen.1.2"), record("U", "FakeTop:1")]:
            with self.subTest(bad=bad[:20]), self.assertRaises(RawCorpusError):
                parse_native_raw_corpus(io.BytesIO(bad + b"S\t1\t1\t0\t0\n"))

    def test_full_metadata_report_never_overwrites_original_module(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            module = root / "approved_module"
            module.mkdir()
            report, *_ = parse_native_raw_corpus(io.BytesIO(sample()))
            saved = root / "metadata.json"
            write_new_metadata_report(saved, module, report)
            self.assertEqual(json.loads(saved.read_text()), report)
            with self.assertRaisesRegex(RawCorpusError, "Unsafe or existing"):
                write_new_metadata_report(saved, module, report)
            blocked = module / "forbidden.json"
            with self.assertRaisesRegex(RawCorpusError, "Unsafe or existing"):
                write_new_metadata_report(blocked, module, report)
            self.assertFalse(blocked.exists())


if __name__ == "__main__":
    unittest.main()
