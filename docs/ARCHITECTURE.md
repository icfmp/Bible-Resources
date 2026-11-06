# Architecture

Bible Resources is a SWORD-compatible distribution service. Sources and editorial transformation recipes are distinct from compiled artifacts. GitHub Pages initially publishes `catalog/v1/catalog.json` alongside `sword/mods.d.tar.gz`, `sword/modules/` and `sword/packages/`. Bible consumes a configurable HTTPS catalogue endpoint. A future API must preserve the v1 contract or provide explicit migration.

CrossWire repositories remain upstream sources; this project is independent. Do not scrape and mirror their entire inventory without a per-edition license review.
