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
