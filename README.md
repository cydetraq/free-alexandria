# Free Alexandria

> A portable archive of human knowledge.

Free Alexandria is a catalog-first offline library for public-domain and openly distributable literature, practical references, emergency-preparedness material, and works that help people evaluate authority, propaganda, and censorship. It builds a static offline library that can be served from removable storage or any simple local web server.

## Offline-first requirement

The finished distribution must work without the internet, DNS, a library catalog, an app store, or a third-party service. The portal, search index, reader-facing descriptions, rights notes, source provenance, checksums, and all included content are local files. External links and identifiers are retained only for audit and future refreshes; the device must never need them at runtime.

## Principles

- Preserve source and edition clarity alongside cultural and practical value.
- Treat offline usefulness as the primary product requirement; no core feature may depend on a live service.
- Keep the catalog as the source of truth; generate the portal and distribution manifest from it.
- Prefer established bibliographic and source-native identifiers over title-derived names; local slugs are join keys, not canonical IDs.
- Keep acquisition sources and provenance beside every stored edition; external URLs are audit metadata, not reader-facing local-download controls.
- Preserve original-language texts alongside eligible English translations where possible.
- Label historical medical, safety, and technical information clearly when current guidance should take precedence.
- Keep the catalog usable for people making their own selections and local archives.

## Repository layout

- `catalog/` — catalog records, collection definitions, and tags.
- `metadata/` — the curation-profile contract.
- `content/` — committed EPUB/PDF editions and their provenance.
- `portal/` — static offline site source.
- `tools/` — validation and build tooling.
- `docs/` — the readable catalog plus build, content, and curation guidance.

## Status

The downloadable catalog is currently a **381 MB bootstrap**: 85 retrieved works (86 distinct source editions) as EPUB/PDF pairs. Every stored edition records its source, acquisition time, file hashes, and byte counts in its adjacent provenance file. Recommendations for works not supplied here live separately in the curated reading lists. It is not the intended 32 GB Pocket Alexandria device edition; that edition will use roughly 28 GB of usable capacity for source-faithful scans, practical manuals, and other high-value offline references.

The catalog distinguishes reader-facing local EPUB/PDF files from acquisition metadata. Every local edition has adjacent provenance with its source and file checksums.

## Browse or consume the archive

The repository is usable as a standalone catalog after cloning—no portal build, online service, or external catalog is required.

- Browse the [downloadable catalog](docs/catalog.md) on GitHub or offline.
- Browse [curated reading lists](docs/curated-reading.md) separately; those titles are recommendations, not supplied files.
- Consume the committed [V1 JSON export](catalog/catalog.json) from scripts or other catalog tools.
- Inspect source records and stored editions in [`catalog/`](catalog/) and [`content/`](content/).

## Quick start

```sh
python3 tools/validate_catalog.py --strict
python3 tools/build_profile.py profiles/free-alexandria-v1.json
```

The second command creates `dist/free-alexandria-v1/`: a self-contained offline library containing all committed EPUB/PDF editions, search data, direct local download links, provenance, and recorded source fallbacks. `--strict` is the offline release check: it verifies the taxonomy, selected files, provenance, reader metadata, local links, and checksums without contacting a live service. Run `python3 tools/lint_sources.py --online` separately when you deliberately want to test recorded Gutenberg source endpoints.

To acquire additional catalog works with a stored exact Project Gutenberg edition and rebuild your local archive, run:

```sh
python3 tools/populate_from_gutenberg.py --all-catalog --acquire
python3 tools/rebuild_local_registry.py
python3 tools/create_profile_from_registry.py --registry catalog/local-editions.json --output profiles/local/my-archive.json
python3 tools/build_profile.py profiles/local/my-archive.json --edition-registry catalog/local-editions.json
```

The result is a static portal with its selected EPUB/PDF files, local search data, provenance records, and checksums. Works without an exact stored Project Gutenberg edition remain available through their recorded source options and can be added with the same workflow.

To make a personal, selectable catalog view, open the built archive, choose individual records (or select all/none), and download its selection file. Convert it into a private profile with:

```sh
python3 tools/create_profile_from_selection.py profiles/local-selection.example.json --output profiles/local/my-selection.json
python3 tools/build_profile.py profiles/local/my-selection.json
```

The profile is a wish list and build input, not a forced download list. See [adding content](docs/adding-content.md) for the acquisition workflow.

## Collections

1. Banned & Challenged Literature
2. Essential Literature
3. Suppressed Knowledge
4. Preparedness & Field Manuals
5. Practical Library
6. Original-Language Library
7. Open-Distribution Library
8. Essential Reading

## Curation-ready V1

Profiles in `profiles/` select a particular view of the shared catalog. They are intentionally separate from source records so a future open-curation workflow can distribute new profiles without rearchitecting the archive. See [docs/curation-profiles.md](docs/curation-profiles.md).

## License

Repository metadata and original documentation are released under [CC0 1.0](LICENSE). Individual works retain their own rights and provenance records.
