# Reviewed BSI entity data (tracked inputs, not compiled output)

- `source.lock.json`: exact original ACAI revision, original corpus editions,
  and source snapshot fingerprint.
- `editorial-decisions.json`: reviewed reversible editorial corrections.
- `reviewed-person-word-overlaps.json`: source-audited overlap decisions.
- `source-reference-qualifications.json`: qualified reference claims.
- `source-unattested-words.json` and `source-unattested-verses.json`:
  original-source negative evidence (not invented verses or words).

These files are **input/evidence under version control**, not an
`index.json` intended for consumers. The compiled entity index is produced
in ignored `../dist/` and the authorized public edition is preserved as
a [GitHub Release ZIP](https://github.com/icfmp/Bible-Resources/releases/tag/bsi-v0.1.0).

Never overwrite original records or normalize their references silently.
