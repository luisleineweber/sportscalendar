from dataclasses import replace
from datetime import date

from sportkalender.catalog_ids import event_id_for_event
from sportkalender.catalog_model import CatalogEvent
from sportkalender.catalog_sources import SourceDefinition


def highlight(stage="season_opener", season="2026-27", start="2026-08-28", end=None, **changes):
    from datetime import timedelta
    event = CatalogEvent(
        event_id="", start_date=date.fromisoformat(start),
        end_date_exclusive=date.fromisoformat(end or start) + timedelta(days=1),
        title=f"Bundesliga {season} {stage}", sport="Football", sport_key="football",
        competition_key="bundesliga", season=season, event_kind="season",
        gender="male", stage=stage, coverage="national", audience_countries=("DE",),
    )
    event = replace(event, **changes)
    return replace(event, event_id=event_id_for_event(event))


def official_source(competition="bundesliga", authority="official"):
    return SourceDefinition("organizer", {"2026": "https://example.test/schedule", "2027": "https://example.test/schedule"}, "en", "html", "reviewed", "", (competition,), (), authority)


def reviewed_evidence(event):
    return [{
        "source_id": "organizer", "source_url": "https://example.test/schedule",
        "date_decision": "verified", "date_checked_at": "2026-10-01",
        "date_statement": "The organizer confirms the full highlight dates.",
        "competition_key": event.competition_key, "season": event.season, "stage": event.stage,
        "confirmed_start_date": event.start_date.isoformat(),
        "confirmed_end_date": event.inclusive_end_date.isoformat(),
        "audience_decision": "verified", "audience_checked_at": "2026-10-01",
        "audience_statement": "The organizer identifies a domestic competition.",
        "coverage": event.coverage, "audience_countries": list(event.audience_countries),
    }]


def requirement(event, year=None, required=True):
    return {
        "catalog_year": year or event.start_date.year, "country": "DE",
        "sport_key": event.sport_key, "competition_key": event.competition_key,
        "season": event.season, "stage": event.stage, "event_kind": event.event_kind,
        "gender": event.gender, "division": event.division,
        "expected_event_id": event.event_id, "required": required, "source_ids": ["organizer"],
    }
