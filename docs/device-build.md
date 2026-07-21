# Pocket Alexandria ESP32 device build

This is the first reproducible captive-portal target for Free Alexandria. It serves a generated static archive directly from a microSD card and redirects captive-portal probes to the local library.

## Reference hardware

- ESP32-S3 development board compatible with `esp32-s3-devkitc-1` in PlatformIO.
- A reliable microSD module or board-integrated microSD slot.
- A 32 GB microSD card formatted as FAT32.
- Stable 5 V power supply.

The default firmware assumes SD chip-select pin **GPIO 10**. Override it by adding a build flag such as `-D FREE_ALEXANDRIA_SD_CS=5` to `platformio.ini` for the selected board.

## Build the archive

From the repository root:

```sh
python3 tools/validate_catalog.py --strict
python3 tools/build_profile.py profiles/free-alexandria-v1.json
```

Copy the **contents** of `dist/free-alexandria-v1/` to the root of the FAT32 card. The card root must contain `index.html`, `manifest.json`, and the referenced local content paths.

Before treating a build as a device release, also run:

```sh
python3 tools/audit_original_requirements.py
```

That audit is expected to fail until all original project requirements have been completed. A successful static build is not by itself a completed Pocket Alexandria edition.

## Build and flash firmware

Install PlatformIO Core, connect the ESP32-S3 board, then run:

```sh
pio run
pio run --target upload
pio device monitor
```

The default access point is:

```text
SSID: Free_Alexandria
Password: none
Portal address: http://192.168.4.1/
Optional mDNS: http://free-alexandria.local/
```

The archive is intentionally available without a password so a nearby person can use the device without credentials. Deployments requiring restricted access should set an AP password and document how recipients obtain it.

## Captive-portal behavior

The firmware:

- creates an isolated Wi-Fi access point;
- assigns the device `192.168.4.1`;
- answers all DNS names with the device address;
- redirects common Android, Apple, Windows, and Firefox captive-network probes to `/`;
- serves static files and byte-downloadable EPUB/PDF assets from the SD card;
- redirects unknown routes to the portal;
- refuses paths containing traversal segments;
- does not require or provide an upstream internet connection.

## Smoke test with no upstream network

1. Remove or disable any Ethernet, station-mode Wi-Fi, or cellular tether from the ESP32.
2. Insert the prepared card and power the device.
3. Join `Free_Alexandria` from a phone and a laptop.
4. Confirm the captive portal opens automatically, or browse to `http://192.168.4.1/`.
5. Search the catalog and change collection/language filters.
6. Download at least one EPUB and one PDF and open both while the client device is in airplane mode with Wi-Fi re-enabled.
7. Request a nonexistent hostname and confirm it resolves to the local portal.
8. Request a nonexistent path and confirm it returns to the portal rather than an external site.
9. Leave the device serving files for at least one hour and repeat a large PDF download.

Record the board model, SD module, card model, profile, archive byte count, firmware commit, and test results in a release note before tagging a device edition.

## Current limitation

This firmware establishes the captive-portal and SD-serving architecture. Hardware-specific validation, large-file stress testing, and completion of the content requirements remain mandatory before a device release.
