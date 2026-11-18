# Dictionary crosswalks

Reserved for compact BSI entity → dictionary entry mappings, **one file per exact dictionary edition**. Do not store dictionary text, definitions, licensed articles or an inferred Strong-to-person identity table. See [../schema.v1.json](../schema.v1.json).

## Implemented lexical bridges

- [UBS Greek NT — bilingual English/French v1.0](ubs-greek/README.md): real source-pinned MACULA Strong and Louw–Nida → UBS entry/sense ID index. It is a lexical bridge, not an unreviewed BSI entity-to-article identity assertion. English and French definitions remain in their original UBS datasets.

- [UBS Biblical Hebrew — bilingual English/French v0.9.4](ubs-hebrew/README.md): pinned Macula WLC `sdbh` → exact UBS lexical sense ID when attested; otherwise exact Hebrew/Aramaic Strong → *entry-only* candidates, never an invented contextual sense. Definitions stay in source UBS editions.
