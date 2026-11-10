# Full numbered-main-text vs stock SWORD — strict whitespace-only witness

See [cross-edition quality issue #28](https://github.com/icfmp/Bible-Resources/issues/28) and
[Darby 2024 import #62](https://github.com/icfmp/Bible-Resources/issues/62).

The original USFX and original stock SWORD modules are independently SHA-pinned
and read privately. The word, case and punctuation comparison in
`scripts/source_native_maintext_probe.py` continues to require exact source
characters for `mapped_numbered_maintext_exact_semantic_characters_verified`.
It reports the original `whitespace_only` category separately rather than
silently changing whitespace. All source vs stock comparisons use original
authored index identities; no verse is inferred or reintroduced.

## Generic reporting classification

`scripts/maintext_fidelity_classification.py` consumes **only metadata**
from the full original/native corpus scanner and refuses a positive
whitespace-folded witness unless all of the following hold:

- original mapped numbered source keys, compiled occupied native keys, and
  independently captured stock reader keys have equal totals;
- all authorial numbered source keys were actually inspected at their
  corresponding stock SWORD indexed entries; no source-only, native-only or
  unmapped original books/numbered references;
- independent exact-key raw entry spot-check and full native SWORD corpus
  scanner both passed;
- every mapped indexed main-text comparison is `exact_semantic_characters`,
  `unicode_normalization_only` or `whitespace_only`;
- no lexical, case, punctuation, wrong key, unparseable raw entry, missing
  note-body text, truncated material difference report or unreviewed
  absorbed-verse index is smuggled into the positive main-text witness.

The resulting state is `PARTIAL`, never an automatic publication or
editorial sign-off. It identifies **numbered words/case/punctuation preservation
after whitespace folding**, not exact character identity. The original native
report still explicitly records whether exact characters matched, and the
new classification declares original whitespace, paragraphs, verse-zero
intros, poetry, note callers, word anchors, cross-reference targets and
book order **NOT VERIFIED**.

This distinction matters because spacing affects layout and may be editorial
material even when the complete word and punctuation sequences remain present.
It is not permitted to normalize source whitespace or declare lost line
breaks irrelevant. Stage 5 must address original editorial layout and notes,
with a separately recorded owner decision where necessary.

## The Darby 2024 original trial

[Stage-4 run 42814369072](https://github.com/icfmp/Bible-Resources/actions/runs/42814369072)
compared 31,170 source USFX numbered verses and 31,170 official eBible
`frajnd2024eb` `zText` stock entries using its actual `Luther`
versification; there were no missing/extra numbered reference keys.
All 31,170 verses classified `whitespace_only` and no material word, case
or punctuation mismatch was detected. This **does not** mean byte-exact
publication quality. The `f` note bodies (6,340 notes) match after
whitespace folding, while all original literal note callers lack a native
`n` marker and machine-target metadata differ. Those are real separate
stage-5 audit findings.

No original Scripture/notes or SWORD payload is committed or emitted in
reports; exact original ZIP digests remain in the associated research issue.

## Regression tests

```sh
python -m unittest discover -s tests -p 'test_maintext_fidelity_classification.py' -v
python -m unittest discover -s tests -p 'test_bible_stage_runner.py' -v
```

These fixtures require missing/reordered references and material
word/case/punctuation differences to remain `BLOCKED`. No Bible-specific
exceptions are included.
