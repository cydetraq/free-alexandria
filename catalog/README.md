# Catalog data

This directory is independently useful after cloning the repository.

- [`catalog.json`](catalog.json) is the committed, dependency-free V1 export for software and other catalogs. Its normalized record index is convenient for clients, and its `source_documents` field retains every authoritative YAML source document.
- [`../docs/catalog.md`](../docs/catalog.md) is the readable inventory for GitHub browsing.
- The YAML files remain the editorial source records.
- [`sources.yaml`](sources.yaml) identifies the repositories and agencies from which future local artifacts may be acquired.
- [`edition-queue.yaml`](edition-queue.yaml) identifies specific candidate editions; it does not claim that those files have been downloaded.
- [`rights-review-queue.yaml`](rights-review-queue.yaml) preserves titles whose U.S. status may turn on renewal, foreign-publication, or restoration research; they are candidates, not exclusions.
- [`jurisdictional-access.json`](jurisdictional-access.json) records country-specific access facts and source links without treating a foreign public-domain determination as U.S. distribution permission.
- [`published-editions.json`](published-editions.json) is the only registry a distribution build uses to include real local files.

Refresh the exports after changing catalog records:

```sh
python3 tools/export_catalog.py
python3 tools/export_catalog.py --check
```
