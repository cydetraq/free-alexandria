# Free Alexandria

> A portable archive of human knowledge.

Free Alexandria is a catalog-first offline library for public-domain and openly distributable literature, practical references, emergency-preparedness material, and works that help people evaluate authority, propaganda, and censorship. Its first deployment target is **Pocket Alexandria**: a static captive-portal library served from removable storage.

## Offline-first requirement

The finished distribution must work without the internet, DNS, a library catalog, an app store, or a third-party service. The portal, search index, reader-facing descriptions, rights notes, source provenance, checksums, and all included content are local files. External links and identifiers are retained only for audit and future refreshes; the device must never need them at runtime.

## Principles

- Preserve legal clarity alongside cultural and practical value.
- Treat offline usefulness as the primary product requirement; no core feature may depend on a live service.
- Keep the catalog as the source of truth; generate the portal and distribution manifest from it.
- Prefer established bibliographic and source-native identifiers over title-derived names; local slugs are join keys, not canonical IDs.
- Mirror only public-domain material, government publications suitable for redistribution, and works with explicit redistribution permission.
- Link to important copyrighted works rather than copying them.
- Preserve original-language texts alongside eligible English translations where possible.
- Label historical medical, safety, and technical information clearly when current guidance should take precedence.

## Repository layout

- `catalog/` — catalog records, collection definitions, and tags.
- `metadata/` — schemas and controlled vocabularies.
- `collections/` — reader-facing descriptions of each collection.
- `content/` — local artifacts, intentionally ignored by Git except provenance and placeholders.
- `portal/` — static offline site source.
- `tools/` — validation and build tooling.
- `docs/` — editorial, licensing, acquisition, and architecture decisions.

## Status

The committed catalog currently contains 186 curated records across literature, source-language works, preparedness, practical references, open-distribution candidates, and external essential reading. The repository deliberately does not commit large book files. A local U.S.-reviewed sampler profile currently builds five acquired, hash-verified EPUB/PDF editions after the operator runs the documented acquisition workflow.

Candidate rights labels are deliberately conservative. They do not authorize copying a source edition; see [the edition-specific copyright review policy](docs/copyright-review.md).

## Browse or consume the catalog

The repository is usable as a standalone catalog after cloning—no portal build, online service, or external catalog is required.

- Browse the [readable catalog](docs/catalog.md) on GitHub or offline.
- Consume the committed [V1 JSON export](catalog/catalog.json) from scripts or other catalog tools.
- Inspect source records, source repositories, candidate editions, and publication status in [`catalog/`](catalog/).
- Generate jurisdictional acquisition plans with the guidance in [docs/jurisdictional-access.md](docs/jurisdictional-access.md).

## Quick start

```sh
python3 tools/validate_catalog.py
python3 tools/export_catalog.py --check
python3 tools/build_profile.py profiles/core-v1.json
```

The second command creates a self-contained full-catalog preview at `dist/core-v1/`. To acquire and build the first actual local distribution, run:

```sh
python3 tools/acquire_project_gutenberg.py --all-approved --acquire
python3 tools/build_profile.py profiles/us-reviewed-sampler.json
```

That sampler contains five locally acquired, source-provenanced EPUB/PDF editions. A larger distribution is assembled only from editions that have been locally acquired, rights-reviewed, and hash-verified.

## Collections

1. Banned & Challenged Literature
2. Suppressed Knowledge
3. Preparedness & Field Manuals
4. Essential Reading — External Links
5. Original-Language Library

## Curation-ready V1

Profiles in `profiles/` select a particular view of the shared catalog. They are intentionally separate from source records so a future open-curation workflow can distribute new profiles without rearchitecting the archive. See [docs/curation-profiles.md](docs/curation-profiles.md).

## License

Repository metadata and original documentation are released under [CC0 1.0](LICENSE). Individual works retain their own rights and provenance records.
