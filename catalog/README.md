# Catalog data

This directory is independently useful after cloning the repository.

- [`catalog.json`](catalog.json) is the committed, dependency-free V1 export for software and other catalogs. Its normalized record index is convenient for clients, and its `source_documents` field retains every authoritative YAML source document.
- [`../docs/catalog.md`](../docs/catalog.md) is the readable inventory for GitHub browsing.
- The YAML files are the editorial source records.
- [`sources.yaml`](sources.yaml) identifies repositories and agencies used by the archive.
- [`resolved-sources.json`](resolved-sources.json) stores the direct source and fallback links shown in the catalog.
- [`published-editions.json`](published-editions.json) identifies the real local files a distribution build can include.

Refresh the exports after changing catalog records:

```sh
python3 tools/export_catalog.py
python3 tools/export_catalog.py --check
```
