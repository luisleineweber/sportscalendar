# Input format (`.tsv`)

The CLI accepts a UTF-8 tab-separated file with these four legacy columns:

1. `Datum` (`dd.mm.yyyy` or `dd.mm.yyyy – dd.mm.yyyy`)
2. `Ereignis`
3. `Sportart`
4. `Ort` (optional)

Example:

```text
6.1.2025 – 12.1.2025	PDC Q-School	Darts	Milton Keynes Kalkar
12.1.2025 – 26.1.2025	Australian Open	Tennis	Melbourne
```

Notes:

- Lines beginning with `###` are ignored.
- Blank lines are ignored.
- The CLI checks duplicate IDs and invalid date ranges before export.
- Single-day dates become one all-day event (`DTEND = DTSTART + 1 day`).

## Published catalog format

Published year files have a header. Both readers use column names, so column order does not matter. Keep `Datum`, `Ereignis`, `Sportart`, and `Ort`, and add `event_id`, `competition_key`, `season`, `sport_key`, `discipline_key`, `coverage`, `audience_countries`, `uk_home_nations`, `event_kind`, `host_countries`, `division`, `gender`, and `stage`.

Country lists use semicolons. `coverage` is `national` or `shared_major`. `event_kind` is `season`, `tournament`, `cup_final`, or `national_championship`. Optional detail fields may be empty. A published row needs a stable `event_id`; a date or place correction must keep it. The companion JSON evidence file is named in `data/catalogs.json`.

Validate a candidate with `python scripts/validate_catalog.py --catalog path/to/catalog.tsv --year 2026`. A four-column input gets a deterministic `custom:` ID for export, but it is not a published catalog until metadata and source evidence are reviewed.
