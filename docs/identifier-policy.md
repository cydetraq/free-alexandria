# Identifier policy

## Rule

External identifiers take precedence over Free Alexandria’s local catalog keys. Before an edition is marked `edition-identified`, record its source-native identifier. Before a work is marked `verified`, add the strongest available work-level identifiers.

## Identifier hierarchy

| Scope | Preferred identifiers | Examples |
| --- | --- | --- |
| Work | Library of Congress work or authority ID; Wikidata QID; Open Library work ID | `wikidata:Q214371`, `openlibrary:OL...W` |
| Text edition | Source-native immutable item identifier | `gutenberg:996`, `internet-archive:donquixote01cerv` |
| Scan / holding | Institutional item or catalog identifier | Library of Congress item ID; HathiTrust identifier |
| U.S. field manual | Publication number + edition date/revision + institutional item ID | `FM 21-76`, `1957`, LOC item identifier |
| Open-licensed web guide | Rights-holder canonical URL + released version/date | EFF module URL and review date |

ISBNs identify particular published manifestations and are useful when present, but they are not a replacement for a work-level identifier.

## Filesystem rule

File paths are human-browsable and include the source-native edition ID:

```text
content/books/adventures-of-huckleberry-finn/en-original-1884--gutenberg-76/book.epub
content/books/don-quixote/es-original-1605--internet-archive-{identifier}/book.pdf
content/manuals/fm-21-76-survival/en-1957--loc-{item-id}/manual.pdf
content/documents/food-and-water-in-an-emergency/en-current--ready-gov-{publication-id}/guide.pdf
```

The work record links to these locations via an edition record. This preserves a clear re-download path, keeps direct browsing pleasant, and allows multiple copies of the same work to coexist.

## Local IDs

Fields such as `id` and `work_id` in the repository are local join keys only. They must be documented as such and must never appear in user-facing provenance as a canonical bibliographic identifier.
