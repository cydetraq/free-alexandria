# Adding content

Free Alexandria stores a work under a readable work ID and the source's native edition ID:

```text
content/books/<work-id>/<source-id>-<source-item-id>/
├── book.epub
├── book.pdf
└── provenance.json
```

`provenance.json` stays with the files. It records the source page, the time retrieved, hashes, byte counts, and the edition identity needed to replace or verify the files later without internet access.

## Add a source already in the catalog

The catalog keeps direct source links and a fallback. To acquire every work with a stored exact Project Gutenberg edition:

```sh
python3 tools/populate_from_gutenberg.py --all-catalog --acquire
python3 tools/rebuild_local_registry.py
```

Then create a build profile from the retrieved files and build it:

```sh
python3 tools/create_profile_from_registry.py --registry catalog/local-editions.json --output profiles/my-library.json
python3 tools/build_profile.py profiles/my-library.json --edition-registry catalog/local-editions.json
```

## Add a source not already listed

Add its direct URL to the work record, regenerate the exports, then place the downloaded files and their provenance in the same content layout:

```sh
python3 tools/add_source_link.py fm-5-426-carpentry 'https://www.gutenberg.org/ebooks/70226' --label 'Project Gutenberg' --source-id project-gutenberg --source-item-id 70226
python3 tools/export_catalog.py
```

The person building an archive chooses what to download, keep, or distribute for their own location and use. Free Alexandria preserves source and edition facts; it does not replace that decision.

## Optional jurisdiction notes

`catalog/jurisdictional-access.json` contains the repository's limited, source-linked jurisdiction notes. Generate a local reference file for selected works with:

```sh
python3 tools/build_jurisdiction_manifest.py --jurisdiction CA --record nineteen-eighty-four
```

It is a convenience summary, not a substitute for the archive builder's own decision.
