# Original project requirements

This file is the release contract for Free Alexandria. The project is not complete merely because a large literary corpus has been committed. A release may call itself a Pocket Alexandria device edition only when every required section below passes the automated audit and the resulting image has been tested offline.

## Required outcome

Produce a portable, self-contained knowledge archive that fits on a 32 GB microSD card and can be served locally from an ESP32-class device as a captive portal. It must remain useful with no internet connection, DNS, app store, third-party account, or external library service.

## Acceptance criteria

### 1. Local literary collection

- Curated public-domain and openly redistributable literature is stored locally.
- Each local edition records exact source, edition, language, translator when applicable, rights basis, acquisition date, byte count, and SHA-256.
- The banned/challenged corpus includes the titles selected from the original Sandman source research where an eligible edition exists.
- Reader-facing entries explain the work and why it was included without exposing internal list provenance as the organizing principle.

### 2. Preparedness and practical references

The device image must contain locally stored, directly downloadable material covering at minimum:

- emergency water and sanitation;
- first aid and public-health guidance;
- food safety and food preservation;
- map reading and land navigation;
- shelter, survival, and fieldcraft;
- knots, rigging, repair, and construction;
- severe-weather and disaster response;
- communications and power-outage safety.

Generic Libby, bookstore, or web-search links do not satisfy this requirement. Current civilian guidance must be preferred for health and safety topics; historical manuals must be clearly labeled.

### 3. Open-distribution works

Works that can legally be mirrored under a verified open license or explicit permission must be stored locally rather than relegated to the linked reading list. License text, attribution, source URL, edition/version, acquisition date, and hashes must accompany each stored work.

### 4. Copyrighted essential reading

Works that cannot be mirrored may appear as recommendations, but their links must be curated in this order:

1. author or rights-holder;
2. publisher or official foundation;
3. public-library catalog or WorldCat-style locator;
4. legitimate controlled digital lending;
5. bookstore or bibliographic listing.

A generic Libby query alone is not sufficient when a more authoritative destination exists.

### 5. Covers and presentation

- Each reader-facing work card has an actual cover thumbnail from an eligible source or a clearly labeled project-generated cover image.
- A styled text rectangle generated at runtime does not count as a stored thumbnail.
- Cover provenance and rights status are recorded.

### 6. Languages and translations

- Original-language editions are retained when eligible.
- When an eligible English translation and original-language edition both exist, both are exposed to the reader.
- The catalog records translator and translation year where known.
- The portal must not collapse a multilingual work into one selected edition without an explicit profile choice.

### 7. Captive-portal device deliverable

The repository must contain:

- firmware or a reproducible device build for the selected ESP32 hardware;
- SD-card/static-file serving configuration;
- captive-portal DNS and HTTP redirect behavior;
- build and flash instructions;
- a generated device-image layout;
- a smoke test proving the portal and local downloads work with the upstream network absent.

A static HTML portal by itself does not satisfy this requirement.

### 8. Capacity and release integrity

- The generated release fits within the declared 32 GB target with documented filesystem overhead and reserve space.
- Catalog counts are generated from source data and agree across README, generated documentation, manifests, and the portal.
- Every selected local file exists and matches its recorded hash and byte count.
- No required reader action points to the public internet.
- The release audit passes before a device edition is tagged.

## Release terminology

Until all criteria pass, the repository must describe the current corpus as a **bootstrap archive**, not a completed Pocket Alexandria device edition.
