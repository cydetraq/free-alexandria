# Free Alexandria

> A portable archive of human knowledge.

Free Alexandria is a catalog-first offline library for public-domain and openly distributable literature, practical references, emergency-preparedness material, and works that help people evaluate authority, propaganda, and censorship. It builds a static offline library that can be served from removable storage or a simple local web server.

## Offline-first requirement

The finished distribution must work without the internet, DNS, a library catalog, an app store, or a third-party service. The portal, search index, reader-facing descriptions, rights notes, source provenance, checksums, and all included content must be local files. External links and identifiers are retained only for audit, acquisition, and future refreshes; the device must never need them at runtime.

## Principles

- Preserve source and edition clarity alongside cultural and practical value.
- Treat offline usefulness as the primary product requirement; no core feature may depend on a live service.
- Keep the catalog as the source of truth; generate the portal and distribution manifest from it.
- Prefer established bibliographic and source-native identifiers over title-derived names; local slugs are join keys, not canonical IDs.
- Keep acquisition sources and provenance beside every stored edition; external URLs are audit metadata, not substitutes for required local content.
- Preserve original-language texts alongside eligible English translations where possible.
- Label historical medical, safety, and technical information clearly when current guidance should take precedence.
- Keep the catalog usable for people making their own selections and local archives.

## Repository layout

- `catalog/` — catalog records, collection definitions, tags, and published-edition registry.
- `metadata/` — curation and metadata contracts.
- `content/` — committed EPUB/PDF editions and their provenance.
- `portal/` — static offline site source.
- `profiles/` — build selections and capacity policy.
- `tools/` — validation, acquisition, audit, and build tooling.
- `docs/` — readable catalogs plus build, content, curation, and device guidance.

## Current status

This repository is a **bootstrap archive**, not yet a completed Pocket Alexandria device edition.

The generated local catalog currently reports **111 included works**. The corpus has strong public-domain literary coverage, stored EPUB/PDF editions, provenance, checksums, local search, and profile-driven builds. It does not yet satisfy the full original requirements because the locally mirrored preparedness corpus, verified open-distribution corpus, stored cover thumbnails, multilingual reader presentation, and ESP32 captive-portal device implementation remain incomplete.

The authoritative release contract is [`docs/original-requirements.md`](docs/original-requirements.md). A release must not be described or tagged as a completed device edition until the original-requirements audit passes.

## Use the archive

Clone the repository to get an offline collection of the books and documents that Free Alexandria is legally able to distribute. You can read the included files directly or browse them through the catalog without building the portal or connecting to an outside service.

- Open the [catalog](docs/catalog.md) to see what is included and where each local file is stored.
- Read the included EPUB and PDF files from [`content/`](content/).
- Review [`docs/curated-reading.md`](docs/curated-reading.md) for recommended works that are not distributed with the archive.
- Use [`catalog/catalog.json`](catalog/catalog.json) when another program needs the catalog in machine-readable form.
- Check [`catalog/`](catalog/) for edition details, rights information, provenance, and checksums.

## Check the repository

Before publishing a release or accepting catalog changes, run:

```sh
python3 tools/validate_catalog.py --strict
python3 tools/audit_original_requirements.py
```

`validate_catalog.py` checks the current catalog, local files, metadata, canonical collection, and linked-reading list for internal consistency. `audit_original_requirements.py` checks the repository against the complete project requirements and reports anything still missing. A release is not complete unless both commands pass.

## Build the current bootstrap

```sh
python3 tools/build_profile.py profiles/free-alexandria-v1.json
```

This creates `dist/free-alexandria-v1/`, a self-contained static archive containing the editions selected by that profile, search data, local download links, provenance, and recorded source metadata. Passing this build alone does not establish that the original 32 GB captive-portal specification has been completed.

To acquire additional catalog works with a stored exact Project Gutenberg edition and rebuild a local archive:

```sh
python3 tools/populate_from_gutenberg.py --all-catalog --acquire
python3 tools/rebuild_local_registry.py
python3 tools/create_profile_from_registry.py --registry catalog/local-editions.json --output profiles/local/my-archive.json
python3 tools/build_profile.py profiles/local/my-archive.json --edition-registry catalog/local-editions.json
```

To make a personal selectable catalog view, open the built archive, choose records, and download its selection file. Convert it into a private profile with:

```sh
python3 tools/create_profile_from_selection.py profiles/local-selection.example.json --output profiles/local/my-selection.json
python3 tools/build_profile.py profiles/local/my-selection.json
```

See [adding content](docs/adding-content.md) for the acquisition workflow.

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
