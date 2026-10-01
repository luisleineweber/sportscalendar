from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta
import re

from sportkalender.catalog_ids import stable_event_id
from sportkalender.catalog_model import CatalogEvent, normalize_key
from sportkalender.catalog_registry import CatalogRegistry
from sportkalender.catalog_tsv import CatalogReadResult


YEAR_PATTERN = re.compile(r"\b(20\d{2})(?:[-/]((?:20)?\d{2}))?\b")


def promote_legacy_catalog(
    read_result: CatalogReadResult,
    *,
    catalog_year: int,
    registry: CatalogRegistry,
) -> tuple[CatalogEvent, ...]:
    if read_result.issues:
        raise ValueError("legacy catalog contains unreadable rows")

    promoted: list[CatalogEvent] = []
    for event in read_result.events:
        event = repair_known_legacy_range(event, catalog_year)
        sport_key = registry.sports_by_alias.get(normalize_key(event.sport), "other")
        competition_key = resolve_competition_key(event.title, registry, sport_key=sport_key) or f"catalog_{sport_key}"
        competition = registry.competitions.get(competition_key)
        if competition is None:
            competition_key = "catalog_other"
            competition = registry.competitions[competition_key]
            sport_key = competition.sport_key

        season = infer_season(event.title, catalog_year)
        event_kind = infer_event_kind(event.title)
        gender = infer_gender(event.title)
        stage = f"{sport_key}:{normalize_key(event.title)}"
        event_id = stable_event_id(
            competition_key=competition_key,
            season=season,
            event_kind=event_kind,
            gender=gender,
            stage=stage,
        )
        promoted.append(
            CatalogEvent(
                event_id=event_id,
                start_date=event.start_date,
                end_date_exclusive=event.end_date_exclusive,
                title=event.title,
                sport=event.sport,
                location=event.location,
                competition_key=competition_key,
                season=season,
                sport_key=sport_key,
                coverage=("not_tagged" if competition_key.startswith("catalog_") else
                          "national" if len(competition.audience_countries) == 1 else "shared_major"),
                audience_countries=() if competition_key.startswith("catalog_") else competition.audience_countries,
                event_kind=event_kind,
                gender=gender,
                stage=stage,
                source_row=event.source_row,
            )
        )
    unique_events: dict[str, CatalogEvent] = {}
    for event in promoted:
        unique_events.setdefault(event.event_id, event)
    return tuple(unique_events.values())


def repair_known_legacy_range(event: CatalogEvent, catalog_year: int) -> CatalogEvent:
    title = normalize_key(event.title)
    if "ashes" in title and event.start_date.year == catalog_year and event.end_date_exclusive <= event.start_date:
        return replace(
            event,
            start_date=date(catalog_year - 1, event.start_date.month, event.start_date.day),
            end_date_exclusive=date(catalog_year, event.end_date_exclusive.month, event.end_date_exclusive.day) + timedelta(days=1),
        )
    if "nfl" in title and "season" in title and event.end_date_exclusive <= event.start_date:
        end_date = event.end_date_exclusive - timedelta(days=1)
        return replace(event, end_date_exclusive=date(end_date.year + 1, end_date.month, end_date.day) + timedelta(days=1))
    return event


def resolve_competition_key(title: str, registry: CatalogRegistry, *, sport_key: str) -> str | None:
    normalized_title = normalize_key(title)
    matches = [
        (alias, key)
        for alias, key in registry.competitions_by_alias.items()
        if not alias.startswith("catalog_")
        and alias_matches_title(alias, normalized_title)
        and registry.competitions[key].sport_key == sport_key
    ]
    if not matches:
        return None
    return max(matches, key=lambda item: len(item[0]))[1]


def alias_matches_title(alias: str, normalized_title: str) -> bool:
    if len(alias) <= 4 and alias.replace("_", "").isalnum():
        return bool(re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", normalized_title))
    return alias in normalized_title


def infer_season(title: str, catalog_year: int) -> str:
    matches = list(YEAR_PATTERN.finditer(title))
    if not matches:
        return str(catalog_year)
    match = matches[0]
    start_year = int(match.group(1))
    end_year = match.group(2)
    if not end_year:
        return str(start_year)
    normalized_end = int(end_year)
    if normalized_end < 100:
        normalized_end += (start_year // 100) * 100
    return f"{start_year}-{normalized_end % 100:02d}"


def infer_event_kind(title: str) -> str:
    normalized = normalize_key(title)
    if "final" in normalized or "super bowl" in normalized:
        return "cup_final"
    if "season" in normalized or "league" in normalized:
        return "season"
    if "championship" in normalized or "championships" in normalized:
        return "national_championship"
    return "tournament"


def infer_gender(title: str) -> str:
    normalized = normalize_key(title)
    if any(token in normalized for token in ("women", "woman", "ladies", "female", "womens")):
        return "female"
    if any(token in normalized for token in ("men", "male", "mens")):
        return "male"
    return "mixed"
