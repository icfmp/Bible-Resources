# Roadmap

1. Prove the pipeline with one legally redistributable Bible, commentary, and dictionary.
2. Import SWORD modules selectively from one highest-priority verified source per edition across CrossWire, eBible, STEP, AndBible and AndBible Extra. Review duplicate identity and retain original source archives and transformation logs. The priority selector is read-only until the future importer is implemented.
3. Enforce official OSIS 2.1.1 XSD validation and fail-closed source structure checks; pin and review the actual CrossWire schema, then implement explicitly reviewed source-to-source transformations (TEI and legacy adapters separately) with full text/structure fidelity tests. Publish diagnostic reports for typography, duplicated scripture and malformed references.
4. Monitor distinct installed/curated/upstream versions for all five SWORD providers declared by Bible; run scheduled/PR source parity checks. Add independently reviewed dataset-update adapters for OpenBible and an authorized YouVersion revision check later; implement user-consented verified client updates in Bible separately.
5. Implement a future API without replacing the existing SWORD distribution structure.
