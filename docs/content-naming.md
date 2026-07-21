# Content naming and replacement policy

## Decision

Use a local **record ID** as the human-readable work folder, retain all applicable external identifiers, and include the source-native identifier in the edition folder. Do not encode mutable claims such as “best,” “final,” or “latest” in a filename, and do not overwrite an acquired edition merely because a better copy becomes available.

```text
content/
  books/
    don-quixote/
      en-ormsby-1885--gutenberg-996/
        book.epub
        book.pdf
        provenance.json
      es-original-1605--internet-archive-donquixote01cerv/
        book.epub
        provenance.json
```

`don-quixote` remains a local record ID; it is not a claimed global identifier. `gutenberg-996` is the source-native identity for that acquired Gutenberg edition. File roles are deliberately short and predictable: `book.epub`, `book.pdf`, `source.txt`, `cover.webp`, and `provenance.json`.

## Why this is preferable

- A better edition can be added beside the earlier file without losing an audit trail.
- SHA-256 hashes remain meaningful because an acquired artifact is never silently replaced.
- The portal can switch `preferred_edition_id` in the catalog without breaking historical links.
- The directory itself makes manual browsing straightforward on an offline card.

## Canonical IDs

- **Catalog record ID:** lowercase kebab case, stable within this repository: `the-great-gatsby`. It is a join key, not an external authority ID.
- **Work identifiers:** use external authority IDs where available, with a scheme label: Wikidata QID, Open Library work ID, Library of Congress work/authority ID, or another established bibliographic identifier.
- **Edition directory:** `{language}-{translator-or-original}-{edition-year}--{source-slug}-{source-item}`. Example: `en-ormsby-1885--gutenberg-996`.
- **Edition identifiers:** use the source's native immutable ID: Project Gutenberg ebook number, Internet Archive identifier, Library of Congress item ID, HathiTrust identifier, or a publisher's stable record ID.
- **Manual identifiers:** preserve publication number, date/revision, and an institutional record identifier. A field-manual number alone is not unique.

Use a local accession number only when the source lacks a stable identifier. Avoid URLs in filenames. The combination of the readable edition description and source-native suffix is intended to be browsable on a card without opening the catalog.

## Required provenance

Every edition has a `provenance.json` adjacent to its files. It records the source, retrieval date, rights evidence, edition statement, checksums, and review status. The same information begins in `catalog/edition-queue.yaml` before a file is acquired.

## Replacement workflow

1. Add a new source-native edition directory and provenance record.
2. Validate its rights, completeness, readability, and checksum.
3. Update the work record’s `preferred_edition_id` only after review.
4. Keep earlier editions unless storage pressure or a specific rights issue requires their removal.
