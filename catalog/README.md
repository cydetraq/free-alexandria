# Catalog data

This directory is independently useful after cloning the repository.

- [`catalog.json`](catalog.json) is the committed, dependency-free V1 export for software and other catalogs. Its local `download_files` field identifies the one EPUB and one PDF selected for each reader-facing work.
- [`../docs/catalog.md`](../docs/catalog.md) is the readable inventory for GitHub browsing.
- The YAML files are the editorial source records.
- [`sources.yaml`](sources.yaml) identifies repositories and agencies used by the archive.
- [`resolved-sources.json`](resolved-sources.json) stores acquisition and library-fallback links for future refreshes; the offline reader does not need or display them.
- [`published-editions.json`](published-editions.json) identifies the real local files a distribution build can include.

Refresh the exports after changing catalog records:

```sh
python3 tools/export_catalog.py
python3 tools/export_catalog.py --check
```
