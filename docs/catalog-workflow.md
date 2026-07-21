# Catalog workflow

## Catalog states

| State | Meaning |
| --- | --- |
| `candidate` | Worth including; no source edition has been approved yet. |
| `edition-identified` | A specific source edition is known but not downloaded. |
| `acquired` | File has been downloaded and hashed, pending review. |
| `verified` | Rights, edition, completeness, and metadata have been reviewed. |
| `published` | Included in the generated offline distribution. |
| `link-only` | Important copyrighted work: provide legitimate external links only. |

## Acquisition order

1. Public-domain literature with clear English editions.
2. Civilian-relevant government preparedness publications.
3. Original-language texts and historic translations.
4. Explicitly open-licensed material.
5. External-reading bibliography.

No candidate becomes a local mirror merely because a web copy exists.
