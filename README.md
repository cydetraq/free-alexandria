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

## Browse or consume the archive

The repository is usable as a standalone literary bootstrap after cloning—no portal build, online service, or external catalog is required for the locally supplied editions.

- Browse the [downloadable catalog](docs/catalog.md) on GitHub or offline.
- Browse [curated reading lists](docs/curated-reading.md) separately; those titles are recommendations, not supplied files.
- Consume the committed [V1 JSON export](catalog/catalog.json) from scripts or other catalog tools.
- Inspect source records and stored editions in [`catalog/`](catalog/) and [`content/`](content/).

## Validation and release audit

```sh
python3 tools/validate_catalog.py --strict
python3 tools/audit_original_requirements.py
```

The first command validates current catalog integrity. The second is intentionally stricter: it checks the repository against the original requested outcome and must fail while any required section is missing.

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
