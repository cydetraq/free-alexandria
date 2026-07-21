# Architecture

The catalog is the source of truth. A build process will validate catalog records and generate a static portal, offline search index, checksum manifest, and deployment tree.

```text
catalog records + verified local artifacts
                │
                ├── validation
                ├── static portal
                ├── search index
                └── distribution manifest
```

`dist/` is a generated deployment directory and must not be committed. An ESP32-S3 captive portal can serve that directory from a microSD card.
