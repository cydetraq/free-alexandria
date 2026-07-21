# Architecture

The catalog is the source of truth. Stable work records are separate from edition-specific acquisition records. A build process will validate both and generate a static portal, offline search index, checksum manifest, and deployment tree.

```text
work records + edition queue + verified local artifacts
                │
                ├── validation
                ├── static portal
                ├── search index
                └── distribution manifest
```

`dist/` is a generated deployment directory and must not be committed. An ESP32-S3 captive portal can serve that directory from a microSD card.

## Offline runtime contract

The deployed `dist/` directory is self-contained. It includes rendered catalog metadata, full-text files, cover assets, a local search index, provenance and license records, and checksums. A live source catalog is never consulted to render a card, search, open a text, verify an included file, or explain its rights status.

External URLs are useful acquisition metadata, but they are not runtime dependencies. The portal should make this explicit when a title is intentionally link-only: that card is a bibliography record and cannot promise availability while offline.
