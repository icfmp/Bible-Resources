# Post-MHCC cross-resource/toolchain validation — 2026-11-16

## Baseline, source ownership and scope

Maintained `main` baseline: `a1cb96cb87f5a8d21200810159187552c61c4bff` (MHCC 0.1.1 published and public SHA verified). The cleanup is isolated to [PR #280](https://github.com/icfmp/Bible-Resources/pull/280); original published modules, notes, SWORD identities and public catalogue must remain **byte-for-byte unchanged**.

At kickoff: **152 tracked Python scripts, six native C++ scripts, 45 workflows, 147 Python test files and 105 docs/evidence files**. A generated [complete source- and caller-bound registry](../TOOL_REGISTRY.md) records every current tracked script; no script is deleted based on guessed use. These numbers are the fixed baseline, not the expected count after adding future reusable tools.

## Reusable SWORD packaging/preflight

The generic `release_preflight.inspect_approved_releases` deliberately invokes the **existing** `validate`, `build`, `catalogue_release_coverage` and `approved_release` production interfaces; it does not create another archive format or publishing path.

Actual versioned and source-reviewed checked-in resources:

| Edition | Driver | Current curated version | Approved release route |
| --- | --- | --- | --- |
| Louis Segond, `lsg-1910` | `RawText` | `BRLSG1910 0.1.0` | **Frozen historical binding**; its actual GitHub Release and Pages ZIP have different independently pinned SHA-256 values. No fake active plan. |
| Darby, `darby-jnd-2024` | `zText` | `BRJND2024 0.1.1` | **Frozen historical binding**, with independently reviewed matching versioned/public bytes. |
| Matthew Henry Concise, `mhcc-crosswire` | `zCom` | `MHCC 0.1.1` | **Current source-corrected approved release plan**, exact seven native members, one public catalogue row. |

This difference is crucial: a generic tool must **not** assume every source has a current active release plan. The frozen historical route checks the exact published Pages ZIP and its original source-proof record, but does **not** falsely claim to have downloaded the independent historic GitHub asset offline. Its public download integrity is a distinct production check.

The test exercises one interface against all three *real* checked-in, independently attested resources. Invalid unknown/duplicate/path-traversal module IDs fail closed. The normal production validator already rejects wrong source/rights, driver, hash, notes/reference evidence, incomplete member inventory and unsanctioned release plans.

## Second actual source: John Wesley's Notes, not an MHCC clone

[CrossWire official module listing](https://crosswire.org/sword/modules/ModInfo.jsp?modName=Wesley) states `Wesley` **version 1.1 (2001-11-28)** and the upstream module **Public Domain** distribution claim. This was observed **independently of MHCC**, using the same read-only `commentary_intake.py` and `commentary_native_inventory.py` code, on multiple fresh official ZIP downloads:

- Real ZIP **2,842,885 bytes**, SHA-256 `d9e2d98b11f6b9e62d448c29f76453d7c9a97dec6a3112c83045c9ce592ae24c`. Independently observed without repinning in three runs, including [#43924646297](https://github.com/icfmp/Bible-Resources/actions/runs/43924646297), [#43924893157](https://github.com/icfmp/Bible-Resources/actions/runs/43924893157) and [#43924948939](https://github.com/icfmp/Bible-Resources/actions/runs/43924948939).
- **Discrepancy left explicit:** that downloaded official ZIP's actual native `.conf` says **`Version=2.0`**, not the public listing's `1.1`. It is **`ModDrv=zCom4`**, not the MHCC `zCom`. This is a source-provider metadata disagreement requiring editorial/source review; no version was silently rewritten or treated as authorized for release. The current research manifest pins the *observed technical ZIP* and records both versions.
- [Pinned source + real native index run #43925130357](https://github.com/icfmp/Bible-Resources/actions/runs/43925130357): **SUCCESS**, actual SWORD native `Wesley` readback showed **18,022 occupied numbered K slots, 1,255 introductions and two opaque TOP slots**. These are **occupied native addresses, not verified authorial section/range count or source-original text/annotation/formatting parity**. Four CLI samples were queried; their response lengths/hashes were recorded without revealing prose, **not** all certified by an independent real GUI reader.
- Independent text/edition and rights approval: **not performed**, **not granted**. The actual CrossWire source's credited electronic editors and markups are attributed, not replaced by presumed public-domain source contents. No Wesley module was added to the approved public catalogue, release plans or `modules/`; source files stayed in a private ephemeral CI directory and were never uploaded.

**Reusable improvement discovered by this second test:** `commentary_intake.py --stage observe` now reports actual publisher ZIP `Version`/language drift as `observed_identity_discrepancy_needs_review` instead of silently treating it as a structurally identical edition or failing before recording the anomaly. **Stage 2 remains strictly blocked** unless the source ZIP hash and actual downloaded `.conf` agree with the reviewed manifest. This behavior is covered by a synthetic negative test.

The dedicated Wesley-only pilot workflow used for the initial private evidence has been removed from the current PR; its already-completed Actions receipts remain in GitHub history. The existing **generic** `commentary-intake.yml` now also runs the native occupied-key inspector for any reviewed, SHA-pinned commentary, reporting separate source-identity vs occupied-index vs authorial-text-parity states. There is no new one-off production pipeline.

## Historical diagnostics, quality and next resources

The heavy MHCC one-off private text comparison and 0.1.0→0.1.1 editorial transition workflows have been frozen to **manual historic replay only**. Their source and receipts are not deleted; automatically running the old transition on every unrelated PR after MHCC 0.1.1 publication produced false errors, long runtimes and wasted CI quota.

The standard single GitHub Release-before-Pages pipeline is unchanged. In particular, external publication, human editorial/rights acceptance, independent full native text parity and application-level UX/installation testing remain **separate** gates. The Bible app's stale catalogue entry and duplicated commentary heading have separate issues, not resource text rewrites.

The registry's `GENERALIZE` and `MERGE` categories are **review priorities**, not automatic cleanup instructions. Deleting a historical tool requires a separate evidence-preserving change with equivalent source-native output and runnable old release tags; uncertain scripts stay `UNDECIDED`. Full Bible source parity remains in #28, resumable CI receipts in #83, and the remaining targeted maintenance checks in #255/#256. **No Codex review was invoked.**
