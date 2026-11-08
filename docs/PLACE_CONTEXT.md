# Offline place context

Related to Bible #218 and #238. This resource is independent of SWORD module approval and imports no Bible text. The application renders this prepared JSON offline. It never matches names, invents historical equivalences, translates source content, or queries Wikipedia each time a place opens.

## Acquisition and review

Run `python scripts/build_place_context.py --cache /tmp/place-sources --output datasets/place-context-v2.json --ids <OpenBible ancient IDs> --generation YYYY-MM-DD`. `--offline` reproduces a run from its source cache; `--refresh` explicitly reacquires upstream revisions. Preserve the source cache in the build evidence, not Git: it contains raw source documents and image thumbnails. The output records pinned source URLs/SHA-256, revisions, languages and gaps. Full source-service introductory extracts are retained unchanged, rather than authored summaries.

The pinned OpenBible ancient resolution supplies a modern_basis_id. The corresponding modern record may supply a **Wikidata coordinate source**. This is provenance for a coordinate, not proof that the Wikidata entity is the ancient place, or even that it describes the identical modern entity. These records have scope `coordinate-source-entity`: the renderer must label this qualification explicitly and keep the proposed OpenBible site name separate. It must not attach that entity's photograph/history as an unqualified description of the ancient place.

Direct ancient identity requires explicit evidence in `config/place-context-identities.json`. Jerusalem preserves the already documented identity from alpha.27. Adding another reviewed identity changes data, not renderer logic; review its source IDs, collisions and ancient/modern scope in the PR. A name match is never sufficient.

Wikidata sitelinks select Wikipedia articles. A summary is accepted only when its returned Wikidata ID matches exactly and its type is standard. English and French source articles are acquired independently; missing languages stay missing. The app labels the actual source language. An English article is never silently translated. Wikidata P18 supplies image identities. Every Commons file must have a supported CC BY, CC BY-SA or CC0 file license, author, source page, revision, dimensions, bounded thumbnail size and checksum. Unsupported licensing, mismatched articles and absent identities are recorded as gaps; there is no arbitrary image search.

## Distribution and updates

The normal reviewed Pages build publishes `place-context/v1/catalog.json` and an immutable, SHA-256-named JSON payload. The application ships a small generated seed for offline use and discovers updates through the existing explicit Library refresh. Installing the optional context resource replaces only its own checked JSON, atomically; it does not rewrite the OpenBible index, notes, translations or preferences. Content expansion needs a reviewed resource update, not an application release. No full photograph archive is bundled. Image acquisition remains an explicit user action with the existing bounded verified image cache and individual attribution.

The metadata manifest is not an assertion that curated Bible modules are approved: the separate module catalogue still contains zero approved imports.

## Actual sample, 8 November 2026

12 ancient IDs requested; 10 have direct or related source context, 11 coordinate-source entities, 8 verified photographs, English and French introductions. Coverage is **not universal** and includes related entities whose identity is explicitly qualified. Bethlehem 2 and Nod lack a vetted source identity; Nod receives no pin, invented history or photograph. Emmaus retains its distinct disputed candidate sites. An English Emmaus source response with a mismatched identity was rejected; its independently matching French source remains available.

Moreh 1 has three genuinely different OpenBible resolutions for modern ID m657590 (Tell Balatah): within a kilometre, within a settlement, and within 200 metres. Their roles, coordinates and evidence paths remain intact. The Wikidata coordinate source labels Q7951237 as Shechem: do not assert that it proves Moreh = Shechem. Group only the repeated modern ID for presentation. Moreh 2 has a different modern ID and coordinate-source entity; never group it with Moreh 1 by translated name.

## Licenses and attribution

OpenBible inputs: CC BY 4.0, with OpenStreetMap-derived database terms ODbL 1.0 as declared by the source. Wikidata: CC0 1.0. Wikipedia introductions: CC BY-SA 4.0, linked to source revisions. Images: each file's recorded license and attribution; no single license is inferred for all Commons files. Dataset field metadata and preparation code follow the repository license; third-party content retains its original terms. Source captions/file names remain source content, including a language-neutral filename when no source caption is supplied. No new French content translation was authored by the application.
