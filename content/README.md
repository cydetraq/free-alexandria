# Stored content

Each stored edition has a readable work folder and a source-native edition folder:

```text
content/books/<work-id>/<source-id>-<source-item-id>/
├── book.epub
├── book.pdf or facsimile.pdf
└── provenance.json
```

For example, `content/books/don-quixote/gutenberg-996/` is the Project Gutenberg edition numbered 996. `provenance.json` records the exact source page, acquisition time, hashes, byte counts, and edition details. A source-faithful `facsimile.pdf` is selected as the reader PDF when it has been reviewed and added; otherwise the compact `book.pdf` is labeled Text PDF in the catalog.
