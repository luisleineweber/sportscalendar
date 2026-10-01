# Catalog checks and monthly updates

Run the monthly check from the project root:

```powershell
python scripts/refresh_catalogs.py --years 2026 2027 --dry-run --report .cache/catalog-report.json
python scripts/refresh_catalogs.py --years 2026 2027 --report .cache/catalog-report.json
```

The command reads the active files as its starting point. It checks the configured sources. It keeps the current Preview status. Use `--preview-years` for new Preview catalogs. Explicit local candidates use `--input YEAR=PATH`. These do not fetch sources unless you add `--fetch-sources`.

Use `--offline` to repeat a check with saved source responses. Use `--source-cache PATH` to change the cache path. A dry run changes no active catalog files. An explicit report path still saves the report.

The report contains source checks, event changes, counts by source, country and sport goals, required highlights, optional highlights, and audience reviews. Source counts include sport, country, event kind, and known locations. A rejected candidate also saves its reason. A gap in a goal or an optional highlight does not block Ready. Each required highlight needs official proof for its edition, stage, and full dates. Audience reviews also block Ready.

## Configuration

`data/coverage.json` uses schema version 2. `goals` lists country and sport pairs. `highlights` lists explicit records with `catalog_year`, `country`, `sport_key`, `competition_key`, `season`, `event_kind`, `stage`, `gender`, optional `division`, `required`, and `source_ids`. Known date windows use inclusive `expected_start_date` and `expected_end_date`, plus `date_statement`. Unknown dates stay null. Each chosen league has an opener and a title-deciding closing record in their respective years.

`data/sources.json` uses one source schema: `id`, `urls_by_year`, `language`, `format`, `mode`, `adapter`, `competition_keys`, `required_catalog_ids`, and `authority`. Formats are `html` and `pdf`. Modes are `parsed` and `reviewed`. Authorities are `official` and `secondary`. A parsed source needs a tested adapter. Every year URL is explicit.

The Premier League and Ligue 1 adapters read dated season statements. They publish separate opener and final-matchday events. The Wikipedia adapter uses the existing table parser for discovery. Its rows remain in the report until reviewed. German, US, and Italian source records use the reviewed mode. PDF sources also use reviewed records.

`data/catalog-seeds.json` holds reviewed event records. Keep `source_id`, `source_url`, `source_hash`, `date_checked_at`, and a short `date_statement`. Keep audience proof in `coverage`, `audience_countries`, `audience_checked_at`, and `audience_statement`. The generated evidence records the confirmed dates and identity. Fetching a page alone does not verify a date or audience.

When a reviewed source changes, inspect the saved response. Check the actual dates and audience. Then update its reviewed record and content hash. The command blocks required families until this review is complete. It reports the original check date for unchanged records.

`data/event-reviews.json` records corrections to event kinds. It keeps a reason for each correction. The seed file also records superseded and retired IDs. Missing rows alone do not prove cancellation. Unexplained loss of an established required event blocks replacement.

## Release checks

The command validates all candidate rows and projects shared events into every requested year they overlap. It checks every supported year for identity and metadata conflicts. Update all affected years together. Dry runs use the same release checks, including the files that stay in the manifest. The command writes complete files to one new release directory. It validates every manifest reference and replaces the manifest last. It keeps old release files. An unchanged build checks the active files and keeps the existing manifest and update time.

Run the complete checks:

```powershell
python -m unittest discover -s tests
node --test web/*.test.mjs
python scripts/validate_catalog.py --manifest data/catalogs.json
```

The command makes a local data update. It does not commit, push, or deploy the website.
