# Configuration et exploitation du dépôt GitHub

Le dépôt source est désormais créé : https://github.com/icfmp/Bible-Resources

## Étapes restant à effectuer dans l'interface GitHub

1. **Settings → Pages → Build and deployment → Source : GitHub Actions.** Attendre une exécution réussie du workflow Publish catalogue. L'URL prévue est https://icfmp.github.io/Bible-Resources/catalog/v1/catalog.json .
2. **Settings → Rules → Rulesets** : protéger `main`, bloquer les force-push et suppressions, exiger des pull requests et le contrôle obligatoire `Validate / validate` après la première exécution verte. Vérifier les possibilités d'approbation sur le plan GitHub actuel.
3. **Actions** : vérifier les workflows Validate et Publish catalogue. Sur zéro module approuvé, le test SWORD réel est explicitement ignoré ; aucun module ne sera certifié par ce résultat.
4. Ne publier des modules qu'avec licence, provenance, rapport éditorial, approbation humaine et vérification effective via le moteur SWORD (`diatheke`).

L'application Bible doit utiliser une URL de catalogue configurable plutôt qu'un lien vers GitHub codé en dur.

## Développement local

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/validate.py
python scripts/build.py --output dist
python scripts/smoke.py
```

Ne pas publier le commentaire français Matthew Henry tant que la redistribution de cette traduction exacte n'est pas documentée.
