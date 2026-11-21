# Développement et vérification du dépôt

Ce document concerne **le dépôt Bible Resources**, pas l'installation de l'application [Bible](https://github.com/icfmp/Bible) ni celle d'un module SWORD dans un lecteur. Pour comprendre la production d'une ressource, lire d'abord le [processus de production](docs/PRODUCTION_PIPELINE.md).

## Préparer un environnement local

Depuis une copie du dépôt, avec Python et ses dépendances :

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/validate.py
python scripts/build.py --output dist
python scripts/smoke.py
```

Pour les audits natifs, installer également le compilateur C++ et une version stable compatible de **libSWORD** ainsi que `diatheke`. Les tests graphiques Xiphos/AndBible nécessitent des environnements indépendants : un simple `smoke.py` ne les remplace pas.

Avant de déplacer ou modifier un script, consulter le [registre des outils](reports/tooling/TOOL_REGISTRY.md) et son [guide de maintenance](scripts/README.md). Ne pas considérer les chemins prévus mais non encore migrés comme des interfaces déjà disponibles.

## Environnement GitHub

Les workflows GitHub Actions fournissent des **preuves bornées**. `Validate` vérifie le dépôt, `Tool registry consistency` contrôle la cohérence de l'inventaire des scripts, et [`pages.yml`](.github/workflows/pages.yml) est le **seul chemin de publication** autorisé : GitHub Releases vérifiées avant référencement dans Pages.

Les règles de protection de `main` sont à inspecter dans les paramètres actuels du dépôt ; ne pas déduire leur présence ni leur bon fonctionnement d'une ancienne capture ou d'un guide d'installation. Les issues et PR décrivent le travail actif, et le résultat exact des Actions doit être vérifié au SHA concerné.

## Publication : conditions distinctes

Un paquet local créé avec `build.py` n'est **pas** une édition publiable. La publication exige provenance et licence, source originale intacte, corrections éditoriales approuvées, comparaisons exhaustives source/cleaned/native, validations SWORD et lecteurs, identité/version/hash du paquet, approbation explicite, puis vérification indépendante des URL et octets publics.

Suivre [la procédure de publication](docs/workflows/PUBLISHING.md) et [l'intégration du catalogue](docs/workflows/CATALOGUE_INTEGRATION.md). Ne jamais publier un commentaire ou une traduction dont les droits spécifiques demeurent incertains.
