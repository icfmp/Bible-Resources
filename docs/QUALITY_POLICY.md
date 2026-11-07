# Quality and release gates

A resource moves through draft → in_review → approved, or restricted when rights prohibit redistribution. Approval requires a real reviewer, provenance, explicit permissions, a precise edition, a documented editorial change record, valid SWORD configuration and an executable reader test. Automated lint is necessary but not sufficient.

Every approved resource must have an accurately attributed reader-facing profile, with evidence-linked claims for any displayed strengths or cautions. Unsubstantiated theological or historical allegations must not be published; draft claims remain internal. See [resource presentation and evidence policy](RESOURCE_PROFILES.md).

Never substitute editorial taste for original intent. Index by the original versification; never silently map variants or invent Bible verse boundaries. Missing original text, malformed files and uncertainty must become review findings.


## Mandatory structure verification

All approved source documents must have a pinned official XSD validation result and reviewed explicit treatment of every source element, with exact source path/line diagnostics for unexpected cases. Unknown structure cannot pass by "best effort" or a warning downgrade. The compiled SWORD module additionally needs a fidelity round-trip and reader validation before release. See [NORMALIZATION_POLICY.md](NORMALIZATION_POLICY.md).

## Unprocessable resources: clarity over abundance

If a source is structurally atypical or initially unsupported, stop and request a standards-based review by the Product Owner. Extend the deterministic importer only after an explicitly reviewed mapping and regression tests. If accurate text, structure, annotations, rights or interoperability still cannot be preserved, **exclude that resource** rather than publishing a broken or misleading approximation. The original source is not edited or redistributed as a fallback. See [the pilot](PILOT_SEGOND_MHC.md).

## Verse omissions and versification

Use SWORD's actual official versification systems (not a unique map invented for every Bible). An intentional editorial/text-critical omission does not authorize filling a blank verse with another translation's words. If the chosen v11n contains the slot, retain a structurally empty verse and an evidence-backed editorial note. Test first-empty-verse handling in actual SWORD clients. A different verse number or a corrupt import must not be mislabeled as an intentional omission. See [VERSIFICATION_POLICY.md](VERSIFICATION_POLICY.md).

## Actual reversible editorial workflow

The source-level diagnostic `scripts/audit_osis.py` and reviewer-gated
`scripts/normalize_osis.py` implement candidate warning reports and
lossless structural changes to a **separate OSIS output**. The original
source remains immutable, with a SHA-256-based review plan and optional
private diff. See [EDITORIAL_AUDIT_WORKFLOW.md](EDITORIAL_AUDIT_WORKFLOW.md).
Do not treat an audit as proof a SWORD module's display is wrong: real
LSG/Psalms and MHC/Genesis key probes already contain line/paragraph
signals. Check Bible GTK rendering before touching an otherwise structured
module. No actual imported/published reader-optimized resource is approved
merely by this tool.
