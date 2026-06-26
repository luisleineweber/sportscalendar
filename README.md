# Sportkalender

Generate deterministic `.ics` files from tab-separated sports event data.

## Web MVP

A static web MVP is available in `web/`:

- filter a ready-made sports event catalog
- select events
- export deterministic `.ics` in-browser

Run locally from repository root:

```bash
py -m http.server 8000
```

Then open `http://localhost:8000/web/`.

The current web app reads its event catalog from `DATA_URL` in `web/app.js`. To use newly scraped events right now, either replace `data/sample_events_2025.tsv` or point `DATA_URL` at your new TSV path.

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

- Only the final TSV is intended as input for the CLI/web import flow.
- The debug TSV keeps raw source values, validation state, and exact-duplicate flags.
- Exact normalized DE/EN collisions are deduplicated conservatively, preferring `de`.

## Deterministic output

For identical input + filters, output is stable by:

- deterministic event sorting
- stable event UID hashing
- fixed `DTSTAMP`
