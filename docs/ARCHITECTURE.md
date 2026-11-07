# Architecture

Bible Resources is a SWORD-compatible distribution service. Sources and editorial transformation recipes are distinct from compiled artifacts. GitHub Pages initially publishes `catalog/v1/catalog.json` alongside `sword/mods.d.tar.gz`, `sword/modules/` and `sword/packages/`. Bible consumes a configurable HTTPS catalogue endpoint. A future API must preserve the v1 contract or provide explicit migration.

CrossWire repositories remain upstream sources; this project is independent. Do not scrape and mirror their entire inventory without a per-edition license review.


## One canonical curated edition across upstream repositories

The five upstream SWORD catalogues are discovery sources, not five independent import queues. Only one provider may supply each **verified identical edition**, according to [SOURCE_PRIORITY.md](SOURCE_PRIORITY.md). The selector is currently read-only, with ambiguity and higher-priority outages blocking import. Approved manifests require a provider-independent canonical edition ID; the build gate rejects duplicate edition variants. The future importer must consume the reviewed selection result and must not mirror every upstream automatically.
