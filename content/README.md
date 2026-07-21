# Stored content

Each stored edition has a readable work folder and a source-native edition folder:

```text
content/books/<work-id>/<source-id>-<source-item-id>/
├── book.epub
├── book.pdf
└── provenance.json
```

For example, `content/books/don-quixote/gutenberg-996/` is the Project Gutenberg edition numbered 996. `provenance.json` records the exact source page, acquisition time, hashes, byte counts, and edition details. A better copy from a different source receives its own source-native folder rather than overwriting an unrelated edition.
