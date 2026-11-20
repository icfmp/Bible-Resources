# Source editions

Source work is grouped **first by resource type**, then by stable curated
resource ID. The two parallel trees are:

- [`original/`](original/README.md): immutable, exact original witnesses;
- [`cleaned/`](cleaned/README.md): normalized, reviewed, edition-faithful
  editable masters.

Supported default formats: **OSIS and USFM**. Additional standards are
introduced only for real needs and reviewed/tested adapters. Never store
compiled SWORD files or uncontrolled working drafts in either tree.

The root `modules/` retains final SWORD payloads and approval receipts;
`work/` is a separate scratch/evidence area. Full directory policies,
rights limitations, legacy compatibility and migration gates:
[Workspace layout](../docs/WORKSPACE_LAYOUT.md).
