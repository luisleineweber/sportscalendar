# Five-country sport catalog plan

Status: confirmed rules implemented on 2026-10-01. The catalogs remain Preview because audience reviews and a required 2027 NFL closing date remain open. The implementation uses separate year, season, and stage checks with official source evidence. It keeps coverage goals and optional gaps outside the Ready gate. See [the catalog process](catalog-process.md) for the monthly command and source review steps.

## Implementation outcome

- Coverage uses schema version 2 with 20 country and sport goals, explicit required highlights, and separate optional records.
- The checker uses stable event identity, actual season, stage, date overlap, registered official sources, and proof of the full date range.
- The monthly command checks sources, uses saved response hashes, reports changes and gaps, and replaces the manifest only after reference checks. It keeps the active batch on failure.
- Premier League and Ligue 1 have tested HTML adapters. German, US, Italian, and FIFA event records use reviewed evidence. Wikipedia remains a discovery source.
- The browser shows country, International, and Unresolved audience scope labels. It shows links only for reviewed date evidence. Country and sport filters keep event choices.
- The acceptance tests cover separate cross-year highlights, optional gaps, source authority, audience scope, full final ranges, source failures, and release crashes.

The older checkpoints below describe the state before this implementation. Event counts and current gaps are in [the manifest](../data/catalogs.json).

Completion checks on 2026-10-01: 70 Python tests and 35 Node tests pass. Every active manifest entry passes validation. An unchanged offline refresh keeps the manifest bytes and update time. Browser checks pass for country and sport filters, saved event choices, year return, rapid year changes, and a failed year load. Narrow-screen visual checks could not run because the preview resize tool failed. CodeRabbit could not run because its configured command is missing.

## Product scope

Keep the existing Sports, Events, and export panels. Use one multi-select country filter above Sports for Germany, the USA, the UK, France, and Italy. Do not repeat country choices inside sport groups. The Sports panel selects sports only. Keep individual event choices and per-sport event actions in Events. Show competition and season names only as context on event rows. Country filters affect national events only. Verified international events remain eligible for every country selection. Events with unresolved audience scope remain in Preview until classified.

Country selection is global. It filters visible events and export eligibility. Changing countries does not change sport choices or event selections. The event list stays grouped by sport, with dates sorted inside each sport.

Aim to cover major leagues, cup finals, and senior national championships. A league season groups separate dated entries for its opener, title-deciding closing highlight, and optional highlights. All-Star games may be added but cannot replace the opener or closing highlight. Never represent the full league season as one long event. Give each highlight its own stable event ID and stage under the same competition season.

Use the title-deciding final game, final series, or Final Four/Final Six as the closing highlight. A final tournament over a few days is one calendar event with its verified full date range. Use the final matchday only when the league has no separate title-deciding playoffs. A routine last regular-season matchday is outside the planned highlight scope when playoffs decide the title. Do not import full match schedules or individual rounds and heats.

Include men's and women's competitions when reliable competition and date information is available. There is no fixed mandatory list of women's leagues or per-country event quota. Keep separate editions separate. Use one entry for a combined championship. Report gaps; do not invent dates to fill them.

The website stays static: Vanilla JavaScript, TSV data, and local ICS export. The update process runs in Python on the user's computer once a month.

## Confirmed coverage decisions

| Topic | Agreed rule |
|---|---|
| Calendar year | Assess coverage for the year the user downloads. Use event dates, not the first year in the season name. |
| Required league highlights | For a league chosen for required coverage, verify its opener and title-deciding closing highlight separately in the years their dates overlap. |
| Several highlights in one year | A closing highlight from one season and an opener from the next are separate requirements when both are configured for that year. One cannot satisfy the other. |
| Optional highlights | All-Star games and other useful extras may be added. Their absence or pending date checks do not block `Ready` or satisfy required highlights. |
| Date verification | A required highlight is `verified` only when an official organizer, federation, or competition source confirms its actual date or full date range. Other sources support discovery and cross-checks. |
| Coverage goals | Seek football, basketball, athletics, and other national competitions in each of DE, US, GB, FR, and IT. Show gaps by country and sport without a fixed release floor. |
| Women's competitions | Add reliable events as they are found. Do not impose a fixed list of leagues as a release gate. |
| Audience scope | A `Ready` event is national with verified audience-country tags, or verified international. Unresolved scope remains Preview only. |
| Several audience countries | Selecting any one assigned country makes a national event eligible. |
| `Ready` coverage gate | Every explicitly configured required highlight for that catalog year needs its own verified date and source. Coverage goals and optional extras do not block this gate. Other data and release checks still apply. |

These decisions are recorded in [ADR-0001](adr/0001-league-seasons-use-separate-highlights.md), [ADR-0002](adr/0002-assess-coverage-per-catalog-year.md), [ADR-0003](adr/0003-gate-ready-on-required-highlights.md), [ADR-0004](adr/0004-require-audience-scope-for-ready.md), [ADR-0006](adr/0006-discover-womens-leagues-without-a-mandatory-list.md), and [ADR-0007](adr/0007-use-coverage-goals-not-a-fixed-country-floor.md). ADR-0006 supersedes the fixed women's-league requirement in ADR-0005. See [the glossary](../CONTEXT.md) for the agreed terms.

## Historical implementation checkpoint

The app now uses a global country filter. It filters national rows by `audience_countries` and accepts any matching selected country. Currently, shared and legacy `not_tagged` rows are not hidden when a country is cleared. This legacy behavior does not establish international scope: those unresolved rows must be classified or excluded before `Ready`. Sport controls filter visibility and export eligibility. Event rows hold the event choices. The existing selection model preserves those choices when country or sport filters change. The Events panel groups rows by sport and keeps bulk event actions there.

The product page shows event and selection counts. It does not show the catalog Preview status, update timestamp, unverified-source warning, or generic one-time-export note above Events.

The current manifest is [data/catalogs.json](../data/catalogs.json). It points to the complete event TSV and evidence file for each year. The 29 September checkpoint recorded 524 rows for 2026 and 72 rows for 2027; both were `preview`. The coverage summary recorded 3 of 31 required-kind rows as verified for 2026 and 0 of 31 for 2027. These are legacy checker results, not 31 distinct editions or proof that the agreed stage rules pass. The finite [data/sports.json](../data/sports.json) registry has 34 named sports and an `Other Sports` category. This is a curated list, not a promise of a dedicated filter for every sport. Unmatched source labels need review or an explicit mapping before publication.

At that checkpoint, the 2026/27 Bundesliga and Frauen-Bundesliga highlights had reviewed dates. Their openers belonged to 2026 and their closing highlights to 2027. The checker used season-name prefixes and accepted any one verified season row. The refresh blocked `Ready` on every pending coverage row. Source adapters for all five countries were still open. The completed implementation replaces these checks with explicit yearly stages and separate required, optional, and goal reports.

## User flow

Flow before the catalog expansion:

```text
Open page
└─ Load fixed 2026 file
   └─ Choose sports and events
      └─ Adjust export settings
         └─ Download or share an ICS file
```

Revised flow:

```text
Open the existing product
├─ Choose a catalog year from the manifest
├─ Choose one or more countries in the global filter
│  └─ International competitions always appear, independent of selected countries
├─ Sports panel: select sport categories with All / None actions
├─ Events panel: show eligible events grouped by sport and date
│  ├─ Keep Select visible / Clear visible / Invert visible / Selected only
│  ├─ Keep individual event checkboxes, search, and per-sport event actions
│  └─ Show competition, season, date, reviewed source, and known place as event context
└─ Existing export dock
   ├─ Count selected events and sports
   ├─ Full year / From today; compact Export options
   └─ Download or share an all-day ICS snapshot
```

First visit keeps all countries, sports, and events selected. Country filters apply only to national events and use audience-country tags. Any selected assigned country is sufficient. Verified international events remain eligible for every country selection. If unresolved events remain available in Preview, call their scope "Unresolved audience scope"; do not present them as international or use "not tagged" as the user-facing class. Exclude them from `Ready`. Sport controls filter event visibility; event rows are the only event-selection controls. League seasons use separate dated openers, closing highlights, and optional extras. Keep each multi-day event at its actual full dates. The coverage report shows gaps by country and sport without disabling sport controls.

Keep one event selection set as the source of truth. Event checkboxes add or remove individual event IDs. Per-sport actions in Events operate only on visible events for that sport. Country and sport changes filter eligibility; they never edit selected IDs. Country filters do not use venue location or shared audience tags. Shared and international events appear once, regardless of selected countries. NFL belongs to American Football; UEFA Champions League belongs to Football.

The sport and country controls are eligibility filters and preserve manual event choices when switched off and on. Search and Selected only change the visible list. They do not change event choices. Select visible, Clear visible, and per-sport event actions use only visible rows.

For classified events, country eligibility = verified international OR (national AND any audience country is selected). Visible events = active catalog AND enabled sports AND country eligibility AND search AND optional Selected only. Export events = unique selected IDs AND active catalog AND enabled sports AND country eligibility AND export date range. Unresolved events are a separate Preview review case and never receive international scope by default. Render event groups in the taxonomy's sport order; sort dates within each group. The ICS file retains its separately specified deterministic date order. Label counts as available, selected, and visible.

Use native labelled controls, visible keyboard focus, and a stable status region for counts and load errors. Keep the export action usable at 320 px width and at 200% zoom. Do not show release status, update timestamps, or unverified source summaries above the event list. Show a source only when the event has reviewed evidence.

The exported ICS file is a snapshot. A later catalog update does not change an ICS file already imported into a calendar app.

## Historical legacy-source baseline

This table records the legacy-input audit at local commit `372b51d` on `t3code/expand-national-event-catalogs`. It is not a count of the active manifest releases above, and it is not a new check of GitHub main.

| Check | Result |
|---|---|
| 2026 source rows | DE 198; EN 562 |
| Valid source rows | DE 0; EN 542 |
| German rejection reason | All 198: `unparseable_date` |
| 2026 final rows | 542 |
| Reversed final ranges | 2: Ashes and NFL |
| Final rows with location | 0 of 542 |
| German raw rows with location | 198 of 198 |
| Sport labels | 125 |
| And More group | 426 events across 111 sport labels |
| 2027 final rows | 73; keep this catalog in Preview |
| Independently date-valid rows | 2026: 540 of 542; 2027: 72 of 73 |
| 2027 reversed final ranges | 1: NFL; the fault affects more than one catalog |
| Existing Python tests | 4 pass |
| Existing Node tests | 7 pass |
| CI / manifest / product validator | Not present |

The tests pass while the catalog contains invalid dates. Add product checks before expanding imports. There is no requirement to keep exactly 542 events: the new catalog must follow the agreed event scope.

### Measured availability, not target counts

[catalog-inventory.json](catalog-inventory.json) records the measured legacy input files, SHA-256 hashes, raw sport counts, source acceptance counts, date errors, and named league matches. The HTML embeds this historical snapshot; it does not report the active manifest. Use [data/catalogs.json](../data/catalogs.json) to find the current event TSVs. The inventory measurement date is not a source update date. Rebuild the inventory when its input files change.

Use four separate numbers: stored rows, date-valid rows, selected/exportable entries, and configured required highlights with verified coverage. Date-valid does not mean release-ready or checked against an official source. The historical legacy inventory lacks reliable country and competition identity metadata, so do not infer counts from it. Current releases have explicit tags, but country counts still do not prove required-highlight coverage. Use coverage records for that check. Do not add rows across year catalogs and call the sum distinct events; compare stable IDs because one event can appear in both years.

Show required-highlight gaps explicitly for each catalog year. An All-Star or Draft row cannot satisfy a required opener or closing highlight. A full-season range is out of scope even when its endpoints parse. A 2026-27 season opener in 2026 does not require its 2027 closing highlight in the 2026 catalog. The 2027 catalog checks that closing highlight and any configured 2027-28 opener separately. A multi-day final series is one closing highlight. Invalid, rejected, and published rows are different counts. Validate every catalog, not only the default one.

The finished product shows available and selected event counts by sport and year. Final rows carry stable IDs so counts use unique IDs. The monthly coverage report has two views: goals and gaps by country and sport; and explicit requirements by catalog year, country, sport, competition, season, and stage. Record verified, pending date, missing source, and rejected states. Show whether each pending item blocks `Ready`. Report men's and women's events without fixed quotas. A source link alone never counts as an imported event.

### Coverage report contract

| Report view | Required information | Release effect |
|---|---|---|
| Country and sport goals | For each target country, show football, basketball, athletics, and other discovered national sports; available event counts and gaps. | Inform source discovery. Missing goals alone do not block `Ready`. |
| Required highlights | Catalog year, competition key, actual season/edition, stage, division where needed, expected event identity, date evidence, status, and blocking reason. | Every configured highlight for the year must pass separately. |
| Optional highlights | Discovered extras, their dates and source evidence when known, and pending or rejected state. | Show gaps without adding them to the required pending count. |
| Audience review | Events with unresolved country or international scope and the evidence still needed. | Preview only until classified; an unresolved included event blocks `Ready`. |

Count unique published event IDs separately from required-highlight records. One event can have several audience-country tags without becoming several calendar events. Keep a goal row visible even when that country and sport have no imported events.

## Sources and coverage

Research notes: [USA and UK](sources-us-uk.md), [Germany, France, and Italy](sources-de-fr-it.md). These contain checked links, source formats, and access limits. A readable page is a source candidate, not proof of a working importer.

| List | First source families | Initial event inventory |
|---|---|---|
| Shared international | Wikipedia DE/EN for discovery; IOC, FIFA, UCI, World Athletics and event owners for date checks | Olympic Games, major international championships, major tennis tournaments and cycling races. Add verified owner pages for each chosen event family. |
| Germany | DFB/DFL, DLV, DSV; cycling federation event pages | Bundesliga and women's league openers and closing highlights, plus optional extras; domestic cup finals; senior athletics and swimming championships; selected cycling championships once verified |
| USA | NFL, NBA, MLB, U.S. Soccer, USA Cycling, USA Swimming | Major league openers, closing highlights, and verified finals; U.S. Open Cup final; senior cycling and swimming championships |
| UK | Premier League, FA, Scottish FA, FAW, Irish FA, UK Athletics, Aquatics GB | Major league highlights; senior domestic cup finals for the four home nations; British athletics and swimming championships |
| France | LFP, FFF, FFA, FFN; FFC elite event records | Ligue 1 and women's league highlights; domestic cup finals; senior athletics and swimming championships; elite cycling once verified |
| Italy | Lega Serie A, FIGC, FIDAL, FIN, FCI | Serie A and women's league highlights; domestic cup finals; senior athletics, swimming, and selected cycling championships |

Use this inventory as a discovery list, not a mandatory competition list. Seek football, basketball, athletics, and other national events in each country. Add men's and women's leagues, cup finals, and championships when reliable dates and source access are found. Record each chosen competition, season, stage, catalog year, and source in a coverage file. Mark required highlights explicitly; keep optional extras and coverage goals separate. A source gap is a reported pending item, not a completed event.

There is no fixed per-country release floor, required women's-league list, or minimum count of cup finals or individual-sport championships. Coverage goals guide source work and appear as gaps in the report; those gaps alone do not block `Ready`. NFL, NBA, UEFA Champions League, and other competitions keep separate identities and event choices. Only highlights explicitly selected as required for a catalog year enter its coverage gate. Do not turn the entire discovery list into required rows automatically.

For the UK, use `GB` as the country code and keep England, Scotland, Wales, and Northern Ireland as optional detail tags. Seek cup events across the home nations and report gaps without a compulsory final for each one. A cross-border league can have several audience tags; selecting any one assigned country is sufficient. Its host country does not determine its audience.

### Required-highlight records and the Ready gate

Identify each requirement by catalog year, competition key, actual season/edition, and stage, with country and division where needed. Specify its date window from source evidence so the checker knows which year it belongs to. If a required date is unresolved, retain the pending requirement; do not remove it merely because no event row exists. Check the expected identity and stage, then its date overlap and evidence. A different stage or season cannot satisfy it.

For a league chosen for required coverage, retain both opener and closing requirements, assigned to their respective calendar years. Each year checks only its own highlights. If both occur in the same year, both must pass separately. Optional All-Star entries cannot replace them. Do not filter by `season.startswith(catalog_year)` or accept any one verified `season` row as complete coverage.

`Ready` requires all configured required highlights for that year to be present with verified dates and sources. Missing or unchecked optional events stay pending in the report without blocking this gate; do not publish guessed event dates. Every included `Ready` event must also pass date, identity, sport, and audience-scope checks. Classify unresolved scope or exclude the event from the candidate, while retaining it for Preview review. If that event is required, its missing verified classification still blocks the requirement.

Confirmed source rule: a required highlight is `verified` only when an official organizer, federation, or competition source explicitly confirms its date or full date range for the correct edition and stage. Wikipedia, sport databases, and other secondary sources can help find events and cross-check dates, but cannot establish this status alone. If official date evidence is missing, keep the requirement pending. A URL, a fetch timestamp, or a manual check alone does not prove that the source is official or confirms the event date.

## Data contract

Keep the four existing TSV columns: `Datum`, `Ereignis`, `Sportart`, `Ort`, and the named metadata columns below. Both clients now read catalog fields by header. Keep that contract so metadata never becomes part of the location.

| Field | Rule |
|---|---|
| `event_id` | Stable ASCII ID for one competition edition and stage. Use competition, season/edition, division and event kind. Do not derive it from date, title, location, or source language. |
| `competition_key`, `season` | Stable competition key and explicit edition, such as `2026` or `2026-27`. Keep every opener, closing highlight, and final as a separate event under that edition. |
| Competition registry | Map `competition_key` to display name, `sport_key`, competition kind, primary display group, audience tags, and source aliases. NFL and NBA are leagues; UEFA Champions League is a competition. The UI label is Competitions. |
| `sport_key` | Canonical key such as `football`, `ice_hockey`, `cycling`, `table_tennis`. |
| `discipline_key` | Optional detail such as road cycling, track cycling, or mountain biking. Preserve it when sports share one group. |
| `coverage` | `shared_major` for verified international scope, or `national` for verified country scope. Use clear country or International labels. Legacy `not_tagged` means unresolved scope and is Preview only; do not map it to international automatically. A Wikipedia label is not proof of scope or importance. |
| `audience_countries` | Explicit list of `DE`, `US`, `GB`, `FR`, `IT`, joined with semicolons. A national event needs at least one. Eligibility uses any selected matching country. |
| `uk_home_nations` | Optional explicit list. Never infer it from an English source. |
| `event_kind` | `season`, `tournament`, `cup_final`, or `national_championship`. A `season` row is a dated highlight, not a full-season range. |
| `stage` | Required for league highlights. Use a stable stage such as `season_opener`, `final_matchday`, `playoff_final`, `final_tournament`, or `all_star`. Each event has its own ID; optional stages cannot replace required anchors. A multi-day final tournament is one event. |
| `division`, `gender` | Preserve the covered division and men's, women's, or combined edition. Do not merge separate editions. |
| `host_countries` | Optional venue-country facts, separate from audience. Leave blank when unknown. |

Keep source evidence in a companion JSON file keyed by `event_id`: source IDs/URLs, raw row references, source revision or content hash, fetched time, date-check time, and date decision. For required highlights, retain the official source identity and the date statement for the actual edition and stage. Retain evidence for the audience-country or international classification too. Keep field-level evidence when date, audience scope, and location come from different sources. The source registry is configuration; the evidence file is generated output.

Add `data/sports.json` for keys, display names, groups, and aliases, and `data/competitions.json` for the competition registry. These are shared data, not separate UI hard-coded lists. Map Association football to Football; both Ice hockey forms to Ice Hockey; road/track/MTB labels to Cycling; Vollyball to Volleyball; both Table tennis forms to Table Tennis. Keep American Football separate from Football. Keep raw source names in debug output. All published keys must map to a named group. Unknown labels go to the review report; they must not silently create a large And More group.

Use an explicit competition alias list to merge translated names. Merge on edition identity, not title alone. Preserve both source links. Prefer a verified owner source over Wikipedia. If equal-priority sources conflict, require a review. Do not choose a date only because its source is German. New names without a clear match remain pending.

Keep the documented four-column user TSV input valid. Give such input a documented content-based ID in a separate `custom` namespace. Published catalog rows require stable `event_id` values. This preserves an existing input format without keeping two production catalog systems.

## Date and publication rules

1. Parse numeric and named German months, including Jan., Feb., Mrz./März, and Dez. Resolve omitted months and years from explicit range values, then table context. Validate leap days and month lengths.
2. Preserve explicit years. Use the table month and season evidence to decide which endpoint belongs to the catalog year. Do not fix every reversed range by adding one year to its end.
3. Required regression: January 2026 context, `21 November – 8`, Ashes 2025/26 => 2025-11-21 through 2026-01-08.
4. Required regression: September 2026 context, `9–10 January`, NFL 2026 => 2026-09-09 through 2027-01-10. These test the inference from stored source text; re-fetch and check actual event dates before publishing.
   Include the same failure pattern for the 2027 NFL row. Also test explicit endpoint years such as the rejected 2026-27 UEFA season row. Do not drop an explicit 2027 endpoint from a 2026 source page.
5. Reject ambiguous ranges, unknown dates, and impossible dates with a reason. Do not turn TBD into 1 January or invent a duration. Keep expected but unpublished events in the coverage report.
6. Before final output, enforce inclusive `end >= start`, required title/sport/ID, valid keys, unique IDs, and no exact duplicates. Check again when loading a catalog and before export. A candidate marked valid that violates these rules blocks the build.
7. A year catalog includes any event that overlaps that year. Keep the actual full date range and the same ID across overlapping year catalogs. Do not clip a season at 31 December.
8. Unknown location is allowed. Keep real DE locations and omit the empty-place label in the UI. Track location coverage by source and event type; a final series held at several venues need not have one place.

## Monthly update command

Current interface:

```powershell
python scripts/refresh_catalogs.py --years 2026 2027
```

The command and release validation flow exist. They build and validate local candidates and update immutable release files and the manifest. Tested HTML adapters and reviewed source records cover the configured five-country families. Other source families remain discovery and review work. Run a dry build to inspect a candidate without changing active catalog files. The command does not commit, push, or deploy. The normal project release process makes local updates visible on the website.

Use JSON configuration and current Python dependencies. Start with existing Wikipedia table extraction and small, tested adapters for stable official HTML. Do not build a generic scraper platform. Annual news URLs need an index or an explicit season mapping; do not guess next year's URL.

Update flow:

```text
Source registry + competition inventory + reviewed records
└─ Fetch raw HTML/PDF and keep source evidence
   └─ Parse configured event families
      └─ Resolve dates, sports, IDs and source conflicts
         └─ Compare with the active catalog
            ├─ Failure: report why; retain the active release
            └─ Pass: write complete release files; replace manifest last
```

The source registry records ID, URL or year mapping, language, adapter, covered competitions, required/optional status per catalog, and last successful check. HTTP 200 alone is not success: check the expected table/season and parsed row counts. An empty or stale season page must be visible as a source failure.

Use one registry schema: `id`, `urls_by_year`, `language`, `format` (`html` or `pdf`), `mode` (`parsed` or `reviewed`), `adapter` (required for parsed sources), `competition_keys`, and `required_catalog_ids`. Keep fetch/date-check timestamps in generated evidence. A reviewed source can have either format; it is not a third file format. Source notes must use this same distinction.

Use timeouts, limited retries, request spacing, and conditional HTTP requests where supported. Keep raw snapshots and hashes for repeatable offline tests. A 304 response is usable only with its matching saved response. A missing cache cannot produce a successful refresh.

For PDF or dynamic sources without a tested parser, store a small reviewed record with a source URL and date-check time. The script can detect a source change and request review. It cannot claim to have verified dates just by fetching a page. Changed manual sources block updates to their required event families until the records are checked. Show unchanged manual records and their actual verification age in the report.

Report added, date-changed, metadata-changed, missing, cancelled, rejected, and unresolved events. Include counts by source/country/sport/kind, place coverage, unrecognised labels, pending dates, and unresolved audience scope. Show coverage goals by country and sport and required highlights by year, season, and stage. Separate blocking required items from optional gaps. Separate source-fetch time from last successful catalog update.

Stop replacement if a required source fails, an established required event disappears without explanation, identities collide, or a selected event has conflicting dates. A removed row is not proof of cancellation. Keep the old active release while the report records the problem. Explicit cancellation or confirmed removal can remove an event in the next release and must appear in the report. Exact date changes from an approved parser and authoritative source can pass validation; do not require manual work for every routine update.

The 2027 German Wikipedia page can be optional if it is absent and the manifest reports the gap. Apply the same `Ready` rules to each year: required highlights must pass; optional events and coverage goals may remain pending. A pending requirement cannot pass merely because it has an evidence note. Optional source failures are reported and do not block the coverage gate; required source failures still stop replacement. An unexpected drop to zero from a previously working parser is a source failure, even if HTTP succeeds.

Write new catalog and evidence files in a unique staging directory on the same filesystem. After validation, rename it to a new immutable release directory. Write the complete manifest to a temporary sibling file, then atomically replace `data/catalogs.json` as the final step. Validate all references before replacement. Keep old release files. A failed run must leave the current manifest and files usable. Test crashes before release rename and before manifest replacement. Use a content revision to identify catalog changes. Identical saved sources and configuration produce the same event rows and IDs; fetch timestamps remain metadata.

## Catalog manifest and saved selection

Keep `data/catalogs.json` as the source of active year paths and status. Each entry records `id`, `year`, `file`, `status`, `revision`, `updated_at`, `event_count`, evidence path, and source/coverage summary. A file path points to a complete release. Keep 2026 as the default until a reviewed decision promotes a catalog that passes the coverage and date checks. Never switch from the clock alone.

Use catalog IDs such as `2026` and `2027`, and separate storage keys such as `sportkalender:web-state:v3:2026`. Scope session storage too. A schema version and catalog ID are different from a monthly content revision. Do not reset preferences every month.

For a new catalog, initialise the normal selection. For the same catalog after a monthly update, retain choices for known IDs, remove retired IDs, and show newly added events as new and initially unselected. Store the known IDs needed to distinguish new events. Respect a deliberate empty selection. Stable IDs preserve choices after date or place corrections.

Test 2026 -> 2027 -> 2026, fresh storage, explicit empty storage, date correction, newly added events, storage size handling, and a failed catalog load. A failed switch must not display old events under a new year label.

Identity tests must prove that a date or location correction keeps the same event ID and UID, while a new competition edition gets a new ID. The same cross-year edition in two yearly catalogs keeps its ID.

### Multi-year rules

| Concept | Meaning |
|---|---|
| Catalog year | A selectable date window, driven by the manifest. It contains all events that overlap 1 January through 31 December. |
| Competition | NFL, NBA, UEFA Champions League, or another recurring competition. The key stays stable across years. |
| Season/edition | An explicit edition such as 2026-27. It is not inferred from the catalog filename. |
| Event ID | One competition occurrence or season highlight. An opener, final matchday, and playoff final have separate IDs under the same season. |
| Revision | A particular data build. A monthly revision does not create a new event or reset selection. |

Coverage is a separate result for each calendar year. For example, verify the Bundesliga 2026-27 opener in 2026 and its closing matchday in 2027. A configured 2027-28 opener in 2027 is another required row. Preserve the real season names in both rows; do not combine the yearly results into one season-wide coverage gate.

| Catalog year | Competition season | Required highlight in this example |
|---|---|---|
| 2026 | Bundesliga 2026-27 | Opener, event B |
| 2027 | Bundesliga 2026-27 | Closing matchday, event C |
| 2027 | Bundesliga 2027-28 | Opener, event D |

This example defines identities and yearly checks, not new source dates. Events C and D are independent checks for 2027. Neither depends on event B being present in the 2027 download.

- For year Y, use `start < 1 January (Y+1)` and `end_exclusive > 1 January Y`. Keep full event dates; do not clip them at the year boundary.
- Each source adapter must declare its year-to-season lookup. To build 2027, fetch or reuse evidence for both 2026-27 and 2027-28 seasons where they overlap. Check adjacent Wikipedia year pages as needed. A calendar-year page alone is not proof of complete season coverage.
- The manifest can list any supported year. Adding 2028 must not require edits to app code, storage constants, or parser year assumptions. Reject an unavailable year with a clear message; do not silently load the current year.
- Validate all manifest entries and cross-catalog identities. The same event ID must have the same dates and event facts wherever it appears. Generate year projections from the canonical edition records and check that every overlapping supported year contains that event. If a correction changes a shared edition, update all affected year projections in one release or stop with a consistency report.
- Use one immutable release batch and one final atomic manifest replacement for related years. Add crash tests that keep the previous batch active. Record source year/season, source time, and catalog build time separately.
- Retain year-specific selected IDs, collapsed groups, and settings. On a switch, fetch first, then replace the active label and state together. Ignore a late response from an earlier year request. Missing or failed data must not overwrite either year's saved state.
- First release: one active year in the existing page. Combined-year export is a separate future control, not required to make the data safe. If added, form a union by event ID, check conflicting copies, and count/export each event once. Importing separate files into a calendar app does not itself guarantee deduplication.
- Test 31 December/1 January, leap day, a season crossing years, a new season with the same display name, an explicit next-year endpoint, a missing preview page, a rapid year switch, and the same event in two projections. Test adding 2028 through the manifest without an app-code change.

Selection acceptance examples: Events for NBA, NFL, UEFA Champions League, and Bundesliga remain individually selectable in Events; the Sports panel has no competition or country checkboxes; disabling a sport and restoring it preserves event choices; changing countries filters national events without changing sport or event selections; verified international finals stay eligible with no countries selected; a national event assigned DE and FR needs only one of them selected; unresolved World Championship rows remain Preview only; manual deselection changes only that event; new monthly rows remain unselected; opener and closing highlights use separate stable IDs for the same season.

After a monthly refresh adds or removes events, retain choices for existing IDs, leave new IDs unselected, and remove retired IDs. Sport filters never act as a second event-selection source.

## Shared ICS rules

For published events use `UID:<event_id>@sportkalender`. Both Python and browser read the ID from the catalog. Define the custom-input ID in one shared specification with test vectors. Title format, country filters, date corrections, and source language must not change a published event UID.

Use the same export fields and settings, and sort by `(start_date, end_date_exclusive, event_id)` with an explicit ordinal comparison. Avoid locale-dependent sorting. Keep the current fixed DTSTAMP for deterministic file exports. Reuse Python's installed `icalendar` library.

Emit all-day DATE values and an exclusive DTEND. In the browser, fold at UTF-8 character boundaries with at most 75 bytes per physical line, including a continuation space and excluding CRLF. Escape backslashes, line breaks, commas, and semicolons. These rules follow [RFC 5545 sections 3.1 and 3.6.1](https://www.rfc-editor.org/rfc/rfc5545). The RFC recommends the 75-octet limit; make it a product test requirement.

Test shared fixtures with umlauts, accents, a four-byte character, punctuation, and long locations. Compare UIDs, order, dates, and decoded field values across exporters. Each exporter must be byte-stable for repeated equal input; library property order need not match byte for byte. A stable UID does not turn a downloaded calendar file into a subscription or guarantee a calendar app's re-import behavior.

## Work order and pass conditions

| Step | Work | Status and pass condition |
|---|---|---|
| 1. Coverage contract | Record country/sport goals, explicit required highlights, source registry, and ID/schema rules | **Implemented.** Report goal gaps without a fixed country floor. Required rows use real seasons, stages, and date-based catalog years. |
| 2. Data safety | Validate catalogs and reject date faults | **Implemented; keep checking all years.** Invalid or reversed ranges block publication. |
| 3. Parse and group | Fix DE dates, year inference, places, and sport aliases | **Implemented in the current pipeline.** Review multi-date league rows against the separate-highlight rule; keep all published sport keys mapped. |
| 4. Country and competition imports | Add stable identity, registries, header-based TSV readers, and national source adapters | **Implemented for configured source families.** Registry, IDs, and reviewed country tags exist. Seek broad national coverage; verify audience scope and retain unresolved events for Preview only. |
| 5. Monthly refresh | Build local candidates, reports, immutable releases, and manifest replacement | **Implemented.** The command checks configured sources, gates coverage on required highlights, and validates the atomic release path. Source gaps stay in the report. |
| 6. Catalog UI | Keep Sports / Events / export dock; global multi-country filter, sport-only controls, event actions, year selection, counts | **Implemented in the current app.** Country and sport filters update visibility and export without changing event choices; finish coverage data before Ready. |
| 7. ICS agreement | Share ID/sort/date rules and test UTF-8 folding | **Implemented in the current app.** Keep cross-export fixtures for IDs, dates, ordering, and Unicode folding. |
| 8. CI and docs | Run Python, Node, and catalog checks; keep links and architecture docs current | **Implemented.** Coverage acceptance cases run in the test suite. CI validates every manifest entry. |

The validator, manifest-based UI, selection model, export rules, and CI are already in place. The coverage records, checker, and `Ready` gate now enforce the confirmed rules. Audience scope and event-kind reviews run before release checks. Continue source discovery across all five countries and show gaps without quotas. Keep the legacy parser fixtures in CI while the source adapters grow.

### Implemented interview checklist

These changes now run in the existing catalog process. The table retains the agreed acceptance rules.

| Order | Change and code area | Done when |
|---|---|---|
| 1 | Update `data/coverage.json` and `load_coverage_families` in `sportkalender/catalog_coverage.py`. Separate country/sport goals, chosen required highlights, and optional extras. Replace generic required-kind rows with actual edition and stage requirements. | The discovery list does not create automatic quotas. Chosen league requirements include distinct opener and closing records in the correct years. |
| 2 | Update `build_coverage_report` in `sportkalender/catalog_coverage.py` and `verified_date_records` in `sportkalender/catalog_evidence.py`, plus the source registry and event evidence. Match identity, season, stage, date overlap, and official date confirmation. | A different stage, season, or secondary-only source cannot satisfy a requirement. Missing required records remain pending. |
| 3 | Review league rows and audience classifications through `sportkalender/catalog_enrichment.py` and `sportkalender/catalog_validation.py`. Retain IDs for valid highlights and evidence for dates and scope. | A Final Four/Final Six is one dated event. Every included Ready event has verified national or international scope; unresolved candidates remain available for Preview review. |
| 4 | Update the report and Ready decision in `scripts/refresh_catalogs.py`. Count only pending required highlights as coverage blockers; apply the other release checks separately. | Optional extras and goal gaps do not block the coverage gate. Required failures and unresolved included scope do. Dry runs explain each blocker before manifest replacement. |
| 5 | Use clear country, International, and Unresolved audience scope labels in `web/app.js`; retain the existing any-country match in `web/app-state.mjs`. Add the acceptance cases to `tests/test_catalog_coverage.py`, `tests/test_catalog_refresh.py`, `tests/test_catalog_validation.py`, and relevant browser checks. | The report and UI use the agreed terms. Yearly coverage, official evidence, optional gaps, multi-day finals, and audience filtering pass the specified checks. |

The implementation and acceptance tests now enforce these rules. Source discovery and audience review continue through the report.

### Coverage acceptance cases for implementation

| Case | Expected result |
|---|---|
| 2026-27 opener dated in 2026; closing highlight dated in 2027 | Each event is checked in its own catalog year. The season-name prefix does not filter out the 2027 closing highlight. |
| Required 2026-27 closing and 2027-28 opener both dated in 2027 | Both need separate verified events. One verified row cannot pass both requirements. |
| Verified All-Star event, missing required opener or closing | Required coverage remains pending. |
| Required highlights verified; optional All-Star absent or unchecked | Optional coverage does not block `Ready`. Keep any unpublished optional candidate in the report. |
| Required highlight has only Wikipedia or sport-database date evidence | Keep it pending; secondary sources alone cannot establish `verified`. |
| Official source confirms the required edition, stage, and full dates | The date check can pass with recorded evidence; the other release checks still apply. |
| League ends with a Final Four or Final Six | One closing event uses the verified tournament date range. Do not emit a schedule of separate games. |
| Playoffs decide the title | The final game, series, or tournament is the closing anchor; the routine last regular-season matchday is outside scope. |
| A country has no basketball event yet | Report the country/sport gap. It does not block `Ready` by itself. |
| A women's league has reliable dates | Include its verified highlights as discovered; no fixed women's-league list is required. |
| Event dates verified, audience scope unresolved | Preview only. Classify or exclude it before `Ready`; do not default to International. |
| National event assigned DE and FR | Either selected country is sufficient for visibility and export eligibility. |

These cases now have implementation checks. Pending data stays visible in the monthly report.

## Code status and anchors

These are implementation points for the completed rules. The monthly report tracks the remaining source and audience evidence gaps.

| Existing code | Current state and remaining check |
|---|---|
| `scripts/fetch_wikipedia_merged.py`: date normalization and candidate building | Parser and rejection checks exist. Keep cross-year and ambiguous-date regressions; treat this as legacy discovery input. |
| Same file: table extraction and TSV output | Preserve raw/debug evidence. The refresh command owns publication; do not publish a full-season league row. |
| `sportkalender/core.py`: date parsing, TSV loading, `SportEvent`, `write_ics` | Named fields, stable IDs, and shared export rules are in place. Keep metadata out of `LOCATION` and retain cross-export fixtures. |
| `web/app.js`: `boot`, filtering, and event rendering | Manifest loading, the global country filter, sport groups, event-only selection, and per-sport event actions are in place. Keep country eligibility applied to exports as well as visible rows. |
| `web/app.js`: stored state; `web/app-state.mjs` | Catalog-scoped choices and explicit-empty behavior are in place. Keep year-switch and update-aware selection checks. |
| `web/ics.mjs`, Python ICS exporter | Stable catalog IDs and UTF-8 byte folding are in place. Keep shared Unicode and ordering fixtures. |
| `web/catalog.test.mjs`, Python tests, and `.github/workflows/validate.yml` | Manifest and product checks run in CI. Keep all manifest years in the validation matrix. |
| `scripts/refresh_catalogs.py`, `scripts/validate_catalog.py` | Refresh checks configured sources. Validation checks saved event and source evidence. Failure, dry-run, and unchanged-run tests cover manifest safety. |
| `sportkalender/catalog_coverage.py`, `data/coverage.json` | Uses date-based, per-season, per-stage requirements. Separates required highlights, optional extras, and country/sport goals. Required dates need a registered official source and matching full-range evidence. |
| `web/index.html`, `web/styles.css` | The country filter is global; Sports contains sport controls only; event choices and sport-level actions are in Events. Keep focus visible and actions usable at narrow widths. |
| `scripts/fetch_wikipedia_tables.py` | Keep raw inspection output separate from active releases and route publication through the validated refresh path. |

Keep new modules near 400 lines or less. Split the catalog, dates, source extraction, and export concerns as they change. Do not add another framework, data store, or parallel catalog implementation.

## Legacy defect audit

| Reported fault | Current handling | Remaining check |
|---|---|
| 198 rejected German dates | Parser and reasoned rejection handling exist. | Keep the rejected source evidence; only publish rows with checked dates. |
| Ashes/NFL invalid cross-year dates | Date validation blocks reversed ranges. | Keep regression fixtures for both years. Apply the separate-highlight rule when reviewing league rows. |
| Empty locations and “No location” text | Empty places are optional event context. | Preserve known places and omit an empty-place label in the UI. |
| 125 raw labels and the large “And More” group | A finite 34-sport registry plus `Other Sports` now controls the UI. | Review unmatched source labels before publication; do not add a filter for every raw spelling. |
| Case variants and `Vollyball` typo | Canonical sport keys and aliases exist. | Keep aliases and raw source labels in the review output. |
| Fixed 2026 data URL | The manifest selects the catalog year and status. | Validate every manifest target before loading or publishing. |
| Lost choices at year change | State is scoped by catalog year. | Keep explicit-empty, failed-load, and rapid-switch checks. |
| Different Python/browser UIDs | Both exporters use catalog event IDs. | Keep UID agreement checks after date or metadata corrections. |
| Folding by JavaScript character count | Browser export folds by UTF-8 bytes. | Keep long Unicode fixture checks at the 75-byte limit. |
| Wrong repository links | Docs and page use `https://github.com/luisleineweber/sportscalendar`. | The local Git remote still uses the old owner; this plan does not change it. |
| Stale Next.js/JSON/API/timezone plan | The current product plan uses static JavaScript, TSV, and all-day export. | Keep `docs/mvp.md` and input documentation aligned with the shipped product. |
| Missing product tests and CI | Catalog validation, Python/Node checks, and CI exist. | Keep source-coverage and every-manifest-year checks current. |

The target repository URL was checked with `gh repo view`. The local Git remote still uses the old owner. This plan does not change the remote.

## Decisions and limits

- Recommended: one canonical catalog per year, explicit country relevance, a small source registry, tested adapters, and a monthly local command.
- Keep Wikipedia in the monthly fetch process for discovery and cross-checks. Required highlights need official date confirmation; Wikipedia-only evidence leaves the requirement pending.
- Some PDF/news sources need a short manual review. Fully automatic refresh is a later claim that needs working adapters, not just source links.
- Assess each catalog's `Ready` status against verified required highlights and the other release checks. Coverage goals and optional gaps do not block it. Unresolved audience scope is Preview only. Report pending dates without fabricating them.
- Defer TheSportsDB, accounts, favorites, a database, Next.js, an API backend, live sync, and PWA work. The old TheSportsDB task is superseded by this catalog work.
- Discover additional men's and women's national leagues without a fixed compulsory list. Mark any chosen release requirements explicitly; do not infer them from coverage goals.
- Confirmed: only official organizer, federation, or competition sources can establish `verified` dates for required highlights. Record the supporting date statement and source identity.
