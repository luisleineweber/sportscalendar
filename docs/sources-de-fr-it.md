# Official national sources: Germany, France and Italy

Checked 2026-09-24. V1 scope: major league season highlights, cup finals, and senior national championships. Do not import full match schedules. Dates below are evidence from the checked source, not permanent catalog seeds.

## Germany

| Source | Coverage | Format and limits |
|---|---|---|
| [DFB Rahmenterminkalender](https://www.dfb.de/rahmenterminkalender) and [DFB-Pokal dates](https://www.dfb.de/maenner/wettbewerbe/dfb-pokal/rahmentermine) | Bundesliga, 2. Bundesliga, 3. Liga, DFB-Pokal, Frauen-Bundesliga and Frauen-Pokal season windows/finals. | HTML plus linked PDFs. Football seasons cross calendar years. Use headline dates only; this is a framework, not a full fixture feed. |
| [Bundesliga official season calendar](https://www.bundesliga.com/en/bundesliga/news/calendar-for-2026-27-season-world-cup-34676) | Bundesliga/Bundesliga 2 starts and ends, winter break, relegation play-offs, Supercup and DFB-Pokal final. | HTML. Good source for separate opener and title-deciding closing highlights. Exact match times change during the season. |
| [DFB women's 2026/27 calendar](https://www.dfb.de/news/rahmenterminkalender-der-frauen-2026/2027-verabschiedet) | Google Pixel Frauen-Bundesliga season range and final matchday. | Official HTML calendar: 21 August 2026 to 23 May 2027. Use separate all-day opener and closing highlights. Do not import the full fixture list. |
| [DLV German championships](https://www.leichtathletik.de/wettkaempfe/termine/deutsche-meisterschaften) | Senior athletics championships plus many youth/masters events. | HTML table with season filter, date, competition and place. Filter explicitly to senior national events. |
| [DSV swimming championships](https://www.dsv.de/de/leistungs--und-wettkampfsport/schwimmen/dsv-wettkampf-veranstaltungen/dm-langbahn/) | German long-course, sprint/medley and short-course championships; DSV also publishes open-water dates. | HTML event pages with linked documents. Use selected championship records; do not parse results/protocols as future calendar data. |
| [German Cycling / rad-net national calendar](https://static.rad-net.de/modules.php/webtools/13-bdr/modules.php?menuid=407&name=Ausschreibung&pgID_Veranstaltung=16) and [road-racing rules](https://static.rad-net.de/html/verwaltung/reglements/230404_wb-strasse-4-2023.pdf) | National road, track, MTB and indoor calendar. The rules define recurring senior Elite men/women road championship categories. | HTML search/calendar plus PDF rules. Select only confirmed “Deutsche Meisterschaft” Elite records; dates can be provisional. |

## France

| Source | Coverage | Format and limits |
|---|---|---|
| [FFF competition dates](https://www.fff.fr/article/16358-tout-sur-les-quarts-de-finale.html) and [FFF 2026/27 calendar news](https://www.fff.fr/article/17055-du-nouveau-pour-2026-2027.html) | Coupe de France and Coupe de France Féminine rounds/finals and selected national competitions. | HTML articles. Dates can be round windows or draw dates; review later amendments. |
| [Ligue 1 official calendar](https://www.ligue1.com/calendrier-resultats) | Ligue 1 and Ligue 2 season calendar/results. | Dynamic HTML application. Use only season opening/closing windows and headline events, never all match rows. |
| [FFA French championships](https://www.athle.fr/contenu/calendrier-championnats-de-france/32) | Senior athletics: indoor/outdoor Elite, cross, road, trail, marathon and clubs. | HTML table with filters. Automatic copying is disabled pending supported access. The [calendar view](https://www.athle.fr/bases/liste.aspx) states: “La Fédération Française d'Athlétisme n'autorise pas la copie des données affichées sur cette page.” Use a permitted linked/manual record only. |
| [FFN 2026 calendar](https://www.ffnatation.fr/sites/default/files/2025-11/%F0%9F%93%9926_VPUB_1_0.pdf) and [FFN press/event pages](https://www.ffnatation.fr/actualites/presse?page=2) | Elite 50m/25m, U18, open-water and national swimming events. | Annual PDF plus HTML event pages. Treat the PDF as a reviewed reference, not an executable parser promise; store selected dates with evidence and re-check revisions. |
| [FFC Elite road championships](https://structures.ffc.fr/epreuves-ffc-disciplines/route/championnats-france-route/) and [2026 event notice](https://velo.ffc.fr/informations-championnats-france-cyclisme-route/) | French road championships, including professional/Elite women and men. The federation describes four days and eight titles; the 2026 notice covers 25–28 June at La Tour-du-Pin. | HTML federation page and event notice. Recommended selected source. The previously checked FFC Masters record is outside senior scope and is excluded. |

## Italy

| Source | Coverage | Format and limits |
|---|---|---|
| [Lega Serie A 2026/27 dates](https://en.legaseriea.it/serie-a/news/looking-forward-to-the-2026-27-serie-a-fixture-list) | Serie A opening/closing windows, breaks and headline season dates. | HTML article. Use separate opener and title-deciding closing highlights only; the dynamic fixture list is out of scope. |
| [FIGC official activity dates](https://www.figc.it/media/274511/327-date-attivit%C3%A0-agonistica-ufficiale-stagione-sportiva-2025-2026.pdf) | National football competitions, Coppa Italia, women’s competitions and futsal. | Official PDF. Use as a reviewed reference and structured seed; do not promise a generic PDF parser. |
| [FIDAL federal calendar](https://www.fidal.it/calendario.php?anno=2026&livello=COD&mese=7&new_categoria=&new_regione=&new_tipo=5&submit=Invia) | Italian indoor, cross, road, track and combined-event championships. | Filterable HTML table. Select senior/absolute championship rows and selected women/men events, not every meeting. |
| [FIN national calendar](https://www.federnuoto.it/home/nuoto/gestione-manifestazioni/calendario.html) | Italian swimming and aquatics national championships and federation meets. | Calendar index with annual documents. Use reviewed structured records until a stable event table is confirmed. |
| [Italian Cycling Federation calendar](https://www.federciclismo.it/attivita/calendario/) | Italian cycling championships with discipline/category filters. | Federation calendar application. Identify selected Elite road/track/MTB events and store their event URLs; do not import the full race calendar. |

## Monthly update plan

The [implementation plan](national-catalog-plan.md) defines the final refresh rules and uses JSON configuration to avoid adding a YAML dependency. The notes below describe source-level requirements; they do not require manual review of every validated date change.

Keep a source-registry JSON entry for each selected event family. Use the main plan's fields: source ID, year URLs, language, format, mode, adapter, competition keys, and required catalog IDs. Format is HTML or PDF; mode is parsed or reviewed. The monthly script should fetch supported sources, compare reviewed records, normalise dates, and write a report before replacing the catalog.

For every row require an official source URL, a start date, and `end >= start`. Keep changed, missing, or ambiguous rows in `catalog-review.tsv`; never publish them silently. Record `source_checked_at`, `source_kind`, and `confidence`. Run monthly, with an extra check near football finals because federations amend dates and publish exact times later.

The sources do not provide one common ICS/API feed. Generate ICS locally from canonical event rows after review. This keeps the update process small and avoids promising unsupported PDF or dynamic-page automation.
