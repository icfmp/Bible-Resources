# Quality and release gates

A resource moves through draft → in_review → approved, or restricted when rights prohibit redistribution. Approval requires a real reviewer, provenance, explicit permissions, a precise edition, a documented editorial change record, valid SWORD configuration and an executable reader test. Automated lint is necessary but not sufficient.

Never substitute editorial taste for original intent. Index by the original versification; never silently map variants or invent Bible verse boundaries. Missing original text, malformed files and uncertainty must become review findings.


## Mandatory structure verification

All approved source documents must have a pinned official XSD validation result and reviewed explicit treatment of every source element, with exact source path/line diagnostics for unexpected cases. Unknown structure cannot pass by "best effort" or a warning downgrade. The compiled SWORD module additionally needs a fidelity round-trip and reader validation before release. See [NORMALIZATION_POLICY.md](NORMALIZATION_POLICY.md).
