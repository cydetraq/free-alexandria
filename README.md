# Free Alexandria

> A portable archive of human knowledge.

Free Alexandria is a catalog-first offline library for public-domain and openly distributable literature, practical references, emergency-preparedness material, and works that help people evaluate authority, propaganda, and censorship. Its first deployment target is **Pocket Alexandria**: a static captive-portal library served from removable storage.

## Principles

- Preserve legal clarity alongside cultural and practical value.
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

This initial commit establishes the structure, policy, schema, and seed catalog. It contains no books, manuals, covers, or downloaded content.

## Quick start

```sh
python3 tools/validate_catalog.py
```

## Collections

1. Banned & Challenged Literature
2. Suppressed Knowledge
3. Preparedness & Field Manuals
4. Essential Reading — External Links
5. Original-Language Library

## License

Repository metadata and original documentation are released under [CC0 1.0](LICENSE). Individual works retain their own rights and provenance records.
