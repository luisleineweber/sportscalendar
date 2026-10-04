# Sportkalender

Generate deterministic `.ics` files from tab-separated sports event data.

## Web MVP

A static web MVP is available in `web/`:

- filter a ready-made sports event catalog
- select events
- export deterministic `.ics` in-browser
- choose `Full year`, or `From today` for the current-year catalog

Run locally from repository root:

```bash
py -m http.server 8000
```

Then open `http://localhost:8000/web/`.

The web app reads `data/catalogs.json`. The manifest lists available years and points to immutable release TSV files. The default is 2026; 2027 remains a preview. Selection is saved for each catalog year. Exported ICS files are one-time downloads and do not update after a catalog refresh.

For a current-year TSV, the export dock offers `From today`; this keeps events that are active today or later and excludes events that have already ended. Future-year catalogs offer `Full year` only.

### Catalog refresh

Install the project, then validate the current release:

```bash
python -m pip install -e .
python scripts/validate_catalog.py --manifest data/catalogs.json
```

To publish reviewed, header-based local candidate files for both years:

```bash
python scripts/refresh_catalogs.py --years 2026 2027 --input 2026=data/catalog-candidates/catalog_2026.tsv --input 2027=data/catalog-candidates/catalog_2027.tsv --preview-years 2026 2027 --dry-run
python scripts/refresh_catalogs.py --years 2026 2027 --input 2026=data/catalog-candidates/catalog_2026.tsv --input 2027=data/catalog-candidates/catalog_2027.tsv --preview-years 2026 2027
```

The monthly command fetches configured sources when no explicit input files are supplied. It starts from the active year files and replaces the local manifest last. Explicit candidates fetch sources only with `--fetch-sources`. Use `--offline` for saved responses and `--report .cache/catalog-report.json` for the review report. The command does not commit, push, or deploy. Four-column candidates need reviewed metadata sidecars with `--enrichment YEAR=PATH`.

`data/coverage.json` separates goals, required highlights, and optional events. Only pending required highlights block its coverage gate. Included events also need reviewed audience scope before Ready. See [the catalog process](docs/catalog-process.md) for source records, review checks, and the monthly commands.

### Deploy options

- **GitHub Pages**: publish from `main` branch root (`/`) and use `index.html` redirect.
- **Vercel**: import repository; it serves the static files directly (entry: `index.html` / `web/index.html`).

## Quick start

```bash
python -m pip install -e .
python -m sportkalender --input data/sample_events_2025.tsv --output output/events.ics
```

## CLI usage

```bash
sportkalender --input <input.tsv> --output <events.ics> [--sport "<Sport>"] [--list-sports]
```

- `--sport` can be used multiple times to include only selected sports.
- `--list-sports` prints all recognized sports and exits.

## Input format

See `docs/input-format.md`.

## Web roadmap

MVP plan is documented in `docs/mvp.md`.

## Wikipedia fetch scripts

Install the optional fetch dependencies first:

```bash
python -m pip install -e ".[fetch]"
```

### Raw DE table dump

For a quick German-only raw export:

```bash
python scripts/fetch_wikipedia_tables.py
```

This writes a mostly raw `data/sportkalender_<year>.tsv`.

### Dual-source normalized merge

For the production-oriented Wikipedia merge pipeline:

```bash
python scripts/fetch_wikipedia_merged.py --year 2025
```

Useful variants:

```bash
python scripts/fetch_wikipedia_merged.py --year 2025 --dry-run --verbose
python scripts/fetch_wikipedia_merged.py --year 2025 --keep-source-exports
```

Outputs:

- Final TSV: `data/sportkalender_<year>.tsv`
- Debug TSV: `data/sportkalender_<year>_debug.tsv`
- Optional source debug TSVs: `data/sources/sportkalender_<year>_<source>.tsv`

Notes:

- The final TSV remains valid CLI input. The web app uses the published catalog files listed in the manifest.
- The debug TSV keeps raw source values, validation state, and exact-duplicate flags.
- Exact normalized DE/EN collisions are deduplicated conservatively, preferring `de`.

## Deterministic output

For identical input + filters, output is stable by:

- deterministic event sorting
- stable event UID hashing
- fixed `DTSTAMP`
