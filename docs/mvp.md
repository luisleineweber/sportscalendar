# Sportkalender Web MVP

## Product goal

A simple web app where users pick from ready-made sports events and export a personal `.ics` calendar.

## Target users

- sports fans following multiple competitions
- users who want a calendar feed without manual event entry

## Core v1 scope

1. Preloaded event catalog (season/year dataset).
2. Filters:
   - sport
   - competition
   - country/region for national competitions only; international events always show
3. Event list with checkbox selection.
4. Export selected events as `.ics`.
5. Basic settings:
   - timezone
   - event title format (`Sport - Event` vs `Event`)

## Data + architecture

- The Python CLI accepts legacy four-column and published header-based TSV files.
- `data/catalogs.json` selects immutable yearly release TSV files.
- Vanilla JavaScript loads the catalog, filters events, saves catalog-specific choices, and generates ICS locally.
- A local Python refresh command validates candidate files and replaces the manifest last.

## Deployment

- GitHub Pages and Vercel can serve the static files. No application server is required.

## v1.1 (after launch)

1. “Import from URL/text” advanced mode.
2. Team/athlete favorites.
3. Saved filter presets.
4. One-click “download updates” for new yearly data.

## Success criteria

- user can export a filtered calendar in under 60 seconds
- exported ICS is deterministic for same inputs
- at least 3 curated sports categories available at launch

The current catalogs are previews. The five-country coverage and source-verification requirements are recorded in `national-catalog-plan.md`.
