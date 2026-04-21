# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

This is a **Darwin Core Archive (DwC-A)** biodiversity dataset for the **Colección de Ictiología de la Universidad de Antioquia (CIUA)** — a fish specimen collection. The archive is published through GBIF (doi:10.15472/lkcff8) and the SiB Colombia biodiversity network (resource ID: `udea-001`), versioned at v5.13.

This is a **data repository**, not a software project. There are no build steps, tests, or package managers.

## File structure and formats

| File | Format | Purpose |
|------|--------|---------|
| `meta.xml` | XML (DwC-A descriptor) | Defines field mappings for all data files; tab-delimited, UTF-8, 1 header line |
| `eml.xml` | XML (EML 2.2.0) | Dataset metadata: creators, abstract, coverage, licensing |
| `occurrence.txt` | TSV | Core data — 8,836 specimen records (PreservedSpecimen) |
| `extendedmeasurementorfact.txt` | TSV | Extension data — 17,672 measurement rows linked by `id`/`occurrenceID` |
| `dwca-udea-001-v5.13.zip` | ZIP | Packaged archive containing all the above files |

## Data model

- **Core**: `occurrence.txt` — one row per specimen. Primary key: `id` (= `occurrenceID`, format `UDEA:CIUA:NNNNNNN`). Also serves as `catalogNumber`.
- **Extension**: `extendedmeasurementorfact.txt` — linked to core via `id` (= `occurrenceID`). Uses OBIS ExtendedMeasurementOrFact schema (`measurementType`, `measurementValue`).
- **Taxonomy fields** in occurrence: `scientificName`, `acceptedNameUsage`, `kingdom` → `phylum` → `class` → `order` → `family` → `subfamily` → `genus` → `specificEpithet`, `taxonRank`, `scientificNameAuthorship`, `taxonomicStatus`.
- **Geospatial fields**: `decimalLatitude`, `decimalLongitude`, `geodeticDatum` (WGS84), `coordinateUncertaintyInMeters`; verbatim coordinates also stored separately.
- **Disposition values** include: `En colección`, `Extraviado` (lost).

## Key Darwin Core standards

- Terms follow the TDWG namespace: `http://rs.tdwg.org/dwc/terms/`
- `basisOfRecord` = `PreservedSpecimen` for all records
- Extension row type: `http://rs.iobis.org/obis/terms/ExtendedMeasurementOrFact`
- Coordinate system: WGS84; verbatim coordinates stored in degrees-minutes-seconds or decimal degrees alongside parsed decimal fields

## Working with the data

Parse TSV files with `\t` delimiter, `\n` line endings, no quoting, skipping 1 header line (as declared in `meta.xml`).

Quick inspection examples:
```bash
# Count records
wc -l occurrence.txt

# Check unique taxon ranks
cut -f71 occurrence.txt | sort | uniq -c

# Find records by disposition
awk -F'\t' '$23 == "Extraviado"' occurrence.txt | wc -l

# Check measurement types
cut -f3 extendedmeasurementorfact.txt | sort | uniq -c
```
