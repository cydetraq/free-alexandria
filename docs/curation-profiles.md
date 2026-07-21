# Curation profiles

A curation profile is a small, reviewable JSON document that selects a versioned subset of the shared catalog. It may represent a named curator, a language preference, a practical use case, or a storage-constrained device edition.

Profiles do not contain files, URLs that must work at runtime, or ad-hoc copies of catalog metadata. They reference local catalog record IDs and state their language and storage preferences.

## Two build modes

- `catalog-preview` produces a local offline catalog and a lockfile, even when selected files have not yet been acquired. It is useful for review and planning.
- `distribution` fails unless each selected work resolves through `catalog/published-editions.json` to a local edition with matching hashes, provenance, and a size within the profile limit. It then copies those verified files into the release.

## Reproducibility

Every build emits `build-lock.json`, recording the profile contents, catalog commit, record IDs, selected edition IDs, source identifiers, and hashes. A profile is therefore an editorial request; the lockfile is the exact offline release.

## Open-curation compatibility

Future curation can publish profile files in a separate repository or registry. Free Alexandria only needs to fetch or copy a profile during an update. The actual offline build uses the profile plus its locally checked-out catalog and never needs that registry while running.

## Hard boundaries

Profiles can choose among catalog records. They cannot turn an external link into a local file or omit required provenance.
