# Selection + Mobile Export Improvements

## Spec

- Goal: Improve event selection flow and reduce friction exporting `.ics` on mobile (especially iPhone) without adding live update feeds.
- In scope:
  - Add `Selected only` filter toggle.
  - Add `Invert visible` action.
  - Add smart export that uses native share when supported and falls back to download.
  - Persist selection/settings with storage size guardrail.
- Out of scope:
  - Live-updating feed URLs.
  - Presets/favorites.
  - Conflict detection.

## Acceptance Criteria

- Users can quickly refine picks with `Select visible`, `Clear visible`, `Invert visible`, and `Selected only`.
- Export button shares `.ics` on supported mobile browsers and downloads `.ics` elsewhere.
- Export remains deterministic (same selection -> same ICS content).
- State persistence works:
  - Use `localStorage` when serialized payload is <= 200 KB.
  - Fallback to `sessionStorage` when payload is > 200 KB.

## Checklist

- [x] Add events-panel controls and styles for `Invert visible` and `Selected only`.
- [x] Update filter/selection logic in `web/app.js` for selected-only and invert-visible behavior.
- [x] Replace download-only export with smart share-first export fallback.
- [x] Implement guarded persistence (localStorage/sessionStorage) and restore on boot.
- [x] Verify behavior with static checks (`node --check web/app.js`) and code-path review for deterministic ICS logic.

## Slice: Collapsible Sport Categories

### Acceptance Criteria

- Each sport category can be collapsed/expanded from its header.
- Category actions (`All` / `None`) remain available.
- Collapsed state persists with existing client-side state persistence.

### Checklist

- [x] Add collapse/expand toggle controls in each sport category header.
- [x] Implement collapsed state logic in `web/app.js`.
- [x] Persist and restore collapsed category state.
- [x] Style collapsed/expanded headers clearly in `web/styles.css`.
- [x] Verify behavior and run static syntax check.

## Slice: Collapse UX Bugfix

### Acceptance Criteria

- Category collapse works reliably on tap/click.
- No text label is shown on collapse control; icon-only interaction remains clear.
- Collapsed groups are visually obvious and their grid is hidden.

### Checklist

- [x] Make category heading area toggle collapse/expand.
- [x] Replace text collapse control with icon-only control.
- [x] Add explicit CSS rule to hide collapsed group grid.
- [x] Verify behavior with syntax check and manual smoke path review.

## Slice: Collapse Default State

### Acceptance Criteria

- On initial load, only the first 3 sport categories are expanded.
- Remaining categories start collapsed.
- Persisted user collapse state still overrides default.

### Checklist

- [x] Set default collapsed categories after grouping sports in boot flow.
- [x] Keep restore logic compatible with persisted states.
- [x] Verify via syntax check and state path review.

## Slice: TheSportsDB Event Import (Multi-Sport, No Teams Yet)

### Spec

- Goal: Add a repeatable fetch pipeline that builds TSV event catalogs from TheSportsDB across multiple sports.
- In scope:
  - Python fetch script for event-only import from TheSportsDB.
  - League-based fetch strategy (team-level features deferred).
  - Current-season event coverage with deterministic TSV output.
  - Guardrails for event count, deduplication, and missing data.
- Out of scope:
  - Team favorites/personalized team tracking.
  - Live update feeds or automatic background sync.
  - Odds, stats, or deep metadata beyond TSV columns.

### Acceptance Criteria

- Script can generate a TSV with approximately 1,000 events (target range: 800-1,500).
- TSV rows map cleanly to existing parser schema: `Datum`, `Ereignis`, `Sportart`, `Ort`.
- Output is deterministic for same inputs/config.
- Script applies a hard cap (`--max-events`) and reports filtered/dropped rows.
- At least 6 sports are covered in the default config for v1.

### Checklist

- [ ] Define v1 coverage list (sports + leagues) and save as repo config.
- [ ] Implement `scripts/fetch_thesportsdb_events.py` with API key env-var auth.
- [ ] Fetch season events per configured league and normalize to TSV rows.
- [ ] Add dedup/validation rules (missing date, duplicate key, canceled/postponed policy).
- [ ] Add CLI flags: `--season`, `--max-events`, `--output`, and `--dry-run`.
- [ ] Write output to versioned TSV path and optionally refresh sample file.
- [ ] Document usage and limits in `README.md`.
- [ ] Verify with one dry run and one real run; confirm parser + ICS generation still pass.

## Slice: Mobile Export Dock Kompakt

### Spec

- Goal: Mobile Sticky-Export-Banner so umstellen, dass es deutlich weniger vertikalen Platz einnimmt und nicht wie ein schwebender Block zwischen Content wirkt.
- In scope:
  - Kompaktes, vollbreites Bottom-Dock auf kleinen Viewports.
  - Reduzierte mobile Informationsdichte (kein zusätzlicher Kicker, kompaktere Stats/Button).
  - Mobile Idle-Zustand blendet Statuszeile aus, um Höhe zu sparen.
- Out of scope:
  - Desktop-Layout der Export-Leiste.
  - Änderungen an Export-Logik/Dateiinhalt.

### Acceptance Criteria

- Auf mobilen Viewports ist die Export-Leiste sichtbar, aber merklich niedriger als zuvor.
- Die Leiste sitzt bündig am unteren Bildschirmrand (kein freischwebender Abstand darunter).
- Im Idle-Zustand (`No export yet.`) wird die Statuszeile auf mobile ausgeblendet.
- Nach Export/Fehler bleibt eine Statusmeldung weiterhin sichtbar.

### Checklist

- [x] Add mobile-focused export dock styles in `web/styles.css`.
- [x] Add export dock status state handling in `web/app.js`.
- [x] Verify static syntax check (`node --check web/app.js`) and review affected UI paths.

## Slice: Sport Group Toggle Tap Reliability

### Spec

- Goal: Collapse/Expand-Toggle in Sport-Gruppen soll auf Mobile zuverlässig beim ersten Tap reagieren.
- In scope:
  - Event-Delegation robust für SVG-Targets machen.
  - Toggle-Icon darf Taps nicht abfangen.
- Out of scope:
  - Redesign der Sportgruppen-Header.
  - Änderung der Collapse-Logik/Persistenz.

### Acceptance Criteria

- Tap/Klick auf den Pfeil klappt Gruppen konsistent ein/aus.
- Taps auf SVG/Icon werden genauso verarbeitet wie Taps auf den Button-Hintergrund.

### Checklist

- [x] Fix delegated click target guard in `web/app.js`.
- [x] Prevent icon from intercepting pointer events in `web/styles.css`.
- [x] Verify static syntax check (`node --check web/app.js`) and quick code-path review.

## Slice: Mobile Panel Header in One Line

### Spec

- Goal: `panel-header` soll auf Mobile in einer Zeile bleiben statt untereinander zu umbrechen.
- In scope:
  - Mobile Layout-Regeln für `.panel-header` und Event-Panel-Actions anpassen.
  - Actions im Events-Header einzeilig halten (horizontal scrollbar, falls nötig).
  - `sports-grid` ohne Innenabstand rendern.
- Out of scope:
  - Desktop Header-Layout.
  - Inhaltliche Änderungen an Buttons/Labels.

### Acceptance Criteria

- Auf Mobile bleibt `h2` + Actions im `panel-header` in einer Zeile.
- Im Events-Panel bleiben Actions einzeilig; bei Platzmangel können sie horizontal gescrollt werden.
- `.sports-grid` hat kein Padding.

### Checklist

- [x] Update mobile `.panel-header` styles in `web/styles.css`.
- [x] Keep `.events-panel .actions` on one line on mobile.
- [x] Set `.sports-grid` padding to `0`.
- [x] Verify style rules and quick UI path review.

## Slice: Logic + UX Review

### Acceptance Criteria

- Review core parser/export logic for correctness and data-loss risks.
- Review primary web user journey for usability, accessibility, and mobile friction.
- Verify with available static/runtime checks before closing the review.

### Checklist

- [x] Inspect parser, filtering, persistence, and ICS generation logic.
- [x] Inspect main UI structure, controls, accessibility, and mobile layout behavior.
- [x] Run available checks and local smoke validation.
- [x] Deliver prioritized findings with file references and concrete fixes.

## Slice: Logic + UX Fixes

### Spec

- Goal: Resolve the highest-impact logic and usability issues from the review without widening product scope.
- In scope:
  - Preserve manual event selections when sport filters change.
  - Restore full sport-group header hit area for collapse/expand.
  - Keep keyboard focus stable across sport selection updates.
  - Add visible keyboard focus states for key interactive controls.
  - Keep the mobile events header/actions on one line.
  - Avoid auto-focusing search on initial page load while keeping explicit toggle focus behavior.
  - Add at least one executable logic test for the changed web-state behavior.
- Out of scope:
  - New product features or data sources.
  - Broad visual redesign outside the reviewed friction points.

### Acceptance Criteria

- Changing sport filters no longer re-selects previously deselected events automatically.
- Tapping/clicking anywhere on a sport-group header toggles collapse, except the explicit `All`/`None` actions.
- Keyboard users retain a sensible focus target after sport selection updates.
- Buttons and custom checkboxes show a clear visible focus state.
- On mobile, the events panel header stays on one line and actions can scroll horizontally if needed.
- Initial boot does not auto-focus the search field.
- Verification includes static checks plus an executable test covering selection-preservation behavior.

### Checklist

- [x] Update selection-sync and sport-group interaction logic in `web/app.js`.
- [x] Update focus, header hit-area, and mobile action layout styles in `web/styles.css`.
- [x] Add an executable web-logic regression test.
- [x] Run static checks and targeted verification for the changed behavior.

## Slice: Dual-Source Wikipedia Fetch

### Spec

- Goal: Build a production-ready Wikipedia fetch pipeline that merges German and English event tables into a parser-compatible final TSV plus a richer debug TSV.
- In scope:
  - Add a new dual-source fetch script under `scripts/`.
  - Fetch HTML with a user agent and parse tables from downloaded markup.
  - Normalize DE and EN tables into a shared internal schema.
  - Convert EN date formats into the existing final TSV date format.
  - Deduplicate exact normalized matches while preferring `de` rows on source collisions.
  - Write a final 4-column TSV and a debug TSV with validation and dedup metadata.
  - Add documentation and targeted automated tests for date normalization and dedup behavior.
- Out of scope:
  - Fuzzy matching across translated event names.
  - Changing the main parser or web import format.
  - Enriching final TSV rows with winner/status data.

### Acceptance Criteria

- `scripts/fetch_wikipedia_merged.py` fetches both Wikipedia pages and continues when one source fails.
- Final output remains directly compatible with `sportkalender/core.py` and `web/app.js`.
- Debug output exposes source, raw values, validation state, and exact-duplicate flags.
- EN monthly date ranges are converted into parseable `d.m.yyyy` or `d.m.yyyy - d.m.yyyy` strings.
- Exact normalized duplicate rows are merged conservatively, with `de` preferred over `en`.
- Verification includes dry-run, a real fetch, parser compatibility, and at least one executable logic test.

### Checklist

- [x] Add the new dual-source fetch script with normalization, validation, dedup, and output stages.
- [x] Add targeted automated tests for EN date normalization and exact-duplicate preference.
- [x] Document final/debug outputs and usage in `README.md`.
- [x] Capture the Wikipedia fetch lesson in `tasks/lessons.md`.
- [x] Verify dry-run, real fetch, and downstream ICS generation.

## Slice: Web Copy Reset + Default Selection

### Spec

- Goal: Reset the current web UI copy to English and restore the expected default selection state on first visit without adding a language switch yet.
- In scope:
  - Remove remaining German UI copy in the current static web app.
  - Reset persisted client state keys so stale browser storage from previous experiments does not override the intended default state.
  - Keep the default boot state as "all sports selected" and "all events selected".
  - Document how to point the web app at newly scraped TSV data.
- Out of scope:
  - Building a language switch or translation system.
  - Translating event data coming from TSV files.
  - Adding a full event-catalog selector UI.

### Acceptance Criteria

- All current UI labels and placeholders shipped by `web/index.html` and `web/app.js` are English.
- A fresh visit starts with all sports and all events selected.
- Old persisted browser state from the multilingual experiment no longer forces zero selected events on boot.
- Verification includes static JS checks and the existing web-state test suite.

### Checklist

- [x] Reset current web copy to English where needed.
- [x] Bump persisted web-state storage keys to clear stale browser state.
- [x] Verify default event selection still starts fully selected.
- [x] Add a short note on how to use freshly scraped TSV data with the current web app.
- [x] Run static checks and existing web-state tests.

## Slice: Selection Restore Migration

### Spec

- Goal: Fix the boot-time `Selected 0` regression by migrating legacy empty stored selections back to the intended default without breaking explicit future empty selections.
- In scope:
  - Move restore/default selection logic into a testable helper.
  - Treat legacy stored empty selections without an explicit initialization marker as uninitialized state.
  - Persist an explicit marker so intentionally empty future selections remain respected.
- Out of scope:
  - Removing state persistence entirely.
  - Reworking the broader sports/event selection model.

### Acceptance Criteria

- A legacy stored state with `selectedEventIds: []` and no initialization marker restores to all events selected.
- A newly persisted state can still intentionally restore an empty selection.
- Verification includes targeted web-state tests and static syntax checks.

### Checklist

- [x] Add restore/migration helper logic for selected event ids.
- [x] Use the helper during boot hydration and persist an initialization marker.
- [x] Add regression tests for legacy-empty and explicit-empty restore behavior.
- [x] Run static checks and web-state tests.
