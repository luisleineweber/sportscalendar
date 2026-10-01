from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, timedelta
from html.parser import HTMLParser
import re
import time

from sportkalender.catalog_ids import event_id_for_event
from sportkalender.catalog_model import CatalogEvent
from sportkalender.catalog_sources import SourceDefinition, SourceSnapshot, fetch_snapshot


class _PageText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


@dataclass(frozen=True, slots=True)
class SourceRefreshResult:
    events: tuple[CatalogEvent, ...]
    evidence: dict[str, object]
    rows: tuple[dict[str, object], ...]
    blockers: tuple[str, ...]


def parse_official_highlights(source: SourceDefinition, snapshot: SourceSnapshot) -> SourceRefreshResult:
    parser = _PageText()
    try:
        parser.feed(snapshot.content.decode("utf-8"))
    except UnicodeDecodeError as error:
        return SourceRefreshResult((), {}, (), (f"Source {source.id} cannot be read as UTF-8: {error}",))
    text = " ".join(" ".join(parser.parts).split())
    if source.adapter == "premier_league_highlights":
        pattern = r"opening match round of the (\d{4})/(\d{2,4}) Premier League season.{0,150}?will start on \w+ (\d{1,2}) (\w+) (\d{4}).{0,150}?final match round will be played on \w+ (\d{1,2}) (\w+) (\d{4})"
        months = {name.lower(): index for index, name in enumerate("January February March April May June July August September October November December".split(), 1)}
        country, competition, label = "GB", "premier_league", "Premier League"
    elif source.adapter == "ligue_1_highlights":
        pattern = r"saison (\d{4})/(\d{2,4}) de Ligue 1.{0,80}?d[eé]butera le \w+ (\d{1,2}) (\w+) (\d{4}) et se terminera le \w+ (\d{1,2}) (\w+) (\d{4})"
        months = {name: index for index, name in enumerate("janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split(), 1)}
        country, competition, label = "FR", "ligue_1", "Ligue 1"
    else:
        return SourceRefreshResult((), {}, (), (f"No official highlight parser for {source.id}.",))
    if source.authority != "official" or competition not in source.competition_keys:
        return SourceRefreshResult((), {}, (), (f"Source {source.id} is not registered as the official {competition} source.",))
    matches = list(re.finditer(pattern, text, re.IGNORECASE))
    if len(matches) != 1:
        return SourceRefreshResult((), {}, (), (f"Source {source.id} needs one complete dated season statement; found {len(matches)}.",))
    match = matches[0]
    start_year, end_year, *tokens = match.groups()
    season = f"{start_year}-{end_year[-2:]}"
    configured_years = {int(year) for year in source.urls_by_year}
    if int(start_year) not in configured_years or int(start_year) + 1 not in configured_years:
        return SourceRefreshResult((), {}, (), (f"Source {source.id} contains a stale or unexpected season: {season}.",))
    try:
        dates = [date(int(tokens[offset + 2]), months[tokens[offset + 1].lower()], int(tokens[offset])) for offset in (0, 3)]
    except (KeyError, ValueError) as error:
        return SourceRefreshResult((), {}, (), (f"Source {source.id} contains invalid dates: {error}",))
    if dates[0] >= dates[1] or dates[0].year != int(start_year) or dates[1].year != int(start_year) + 1:
        return SourceRefreshResult((), {}, (), (f"Source {source.id} dates do not match season {season}.",))
    events, evidence = [], {}
    for stage, day in zip(("season_opener", "final_matchday"), dates):
        event = CatalogEvent("", day, day + timedelta(days=1), f"{start_year}/{end_year[-2:]} {label} {'opener' if stage == 'season_opener' else 'final matchday'}", "Football",
                             competition_key=competition, season=season, sport_key="football", coverage="national",
                             audience_countries=(country,), event_kind="season", gender="male", stage=stage)
        event = replace(event, event_id=event_id_for_event(event))
        events.append(event)
        evidence[event.event_id] = [{
            "source_id": source.id, "source_url": snapshot.url, "source_hash": snapshot.content_hash,
            "fetched_at": snapshot.fetched_at, "date_checked_at": snapshot.fetched_at,
            "date_decision": "verified", "date_statement": f"The official {season} calendar confirms {stage} on {day.isoformat()}.",
            "competition_key": competition, "season": season, "stage": stage,
            "source_year": int(start_year), "source_season": season,
            "confirmed_start_date": day.isoformat(), "confirmed_end_date": day.isoformat(),
            "audience_decision": "verified", "audience_checked_at": snapshot.fetched_at,
            "audience_statement": f"The official source identifies the domestic {label} league.",
            "coverage": "national", "audience_countries": [country],
        }]
    return SourceRefreshResult(tuple(events), evidence, (), ())


def refresh_sources(sources, years, seed_events, seed_evidence, cache_dir, *, offline=False, save=True, fetch=fetch_snapshot, pause=time.sleep):
    events = {event.event_id: event for event in seed_events}
    evidence = {key: [dict(item) for item in value] for key, value in seed_evidence.items()}
    rows, blockers, snapshots = [], [], {}
    for source in sources.values():
        relevant = [year for year in years if str(year) in source.urls_by_year]
        if source.adapter == "wikipedia":
            relevant = sorted({year + offset for year in years for offset in (-1, 0, 1) if str(year + offset) in source.urls_by_year})
        if not relevant:
            continue
        for year in relevant:
            required = str(year) in source.required_catalog_ids
            url = source.urls_by_year[str(year)]
            if url not in snapshots:
                if snapshots and not offline:
                    pause(0.5)
                snapshots[url] = fetch(source, year, cache_dir, offline=offline, save=save)
            snapshot = snapshots[url]
            row = {"source_id": source.id, "source_year": year, "source_url": url, "fetched_at": snapshot.fetched_at,
                   "source_hash": snapshot.content_hash, "mode": source.mode, "blocks_release": False}
            if snapshot.error:
                row.update(status="fetch_failed", reason=snapshot.error)
            elif source.mode == "parsed":
                if source.adapter == "wikipedia":
                    from sportkalender.catalog_discovery import discover_wikipedia
                    discovery = discover_wikipedia(source, snapshot, year)
                    row.update(discovery)
                    if row["status"] == "parse_failed" and required:
                        row["blocks_release"] = True
                        blockers.append(f"{source.id} ({year}): {row['reason']}")
                    rows.append(row)
                    continue
                parsed = parse_official_highlights(source, snapshot)
                if parsed.blockers:
                    row.update(status="parse_failed", reason="; ".join(parsed.blockers))
                else:
                    for event in parsed.events:
                        events[event.event_id] = event
                        previous = evidence.get(event.event_id, [])
                        fresh = parsed.evidence[event.event_id]
                        if previous and previous[0].get("source_hash") == snapshot.content_hash:
                            # Keep the actual date-check age when the response is unchanged.
                            evidence[event.event_id] = previous
                        else:
                            evidence[event.event_id] = fresh
                    row.update(status="parsed", parsed_count=len(parsed.events))
            else:
                records = [item for values in evidence.values() for item in values if item.get("source_id") == source.id]
                changed = not records or any(item.get("source_hash") != snapshot.content_hash for item in records)
                row.update(status="review_required" if changed else "unchanged_reviewed", date_checked_at=sorted({str(item.get("date_checked_at", "")) for item in records}))
                if changed:
                    row["reason"] = "The reviewed source changed or has no reviewed content hash."
                    for item in records:
                        item["source_current"] = False
            if row["status"] in {"fetch_failed", "parse_failed", "review_required"}:
                row["blocks_release"] = required
                if required:
                    blockers.append(f"{source.id} ({year}): {row['reason']}")
            rows.append(row)
    return SourceRefreshResult(tuple(events.values()), evidence, tuple(rows), tuple(blockers))
