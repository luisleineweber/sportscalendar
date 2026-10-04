from __future__ import annotations

from datetime import datetime
from typing import Mapping

from sportkalender.catalog_model import CatalogEvent


def valid_check_time(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def evidence_records(value: object) -> tuple[dict[str, object], ...]:
    return tuple(item for item in value if isinstance(item, dict)) if isinstance(value, list) else ()


def verified_date_records(
    event: CatalogEvent, value: object, sources: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    if conflicting_date_records(event, value, sources):
        return ()
    records = []
    for item in evidence_records(value):
        source = sources.get(str(item.get("source_id", "")))
        if source is None or source.authority != "official":
            continue
        if event.competition_key not in source.competition_keys or item.get("source_url") not in source.urls_by_year.values():
            continue
        if (
            item.get("date_decision") == "verified"
            and item.get("source_current", True) is True
            and valid_check_time(item.get("date_checked_at"))
            and item.get("date_statement")
            and item.get("competition_key") == event.competition_key
            and item.get("season") == event.season
            and item.get("stage") == event.stage
            and item.get("confirmed_start_date") == event.start_date.isoformat()
            and item.get("confirmed_end_date") == event.inclusive_end_date.isoformat()
        ):
            records.append(item)
    return tuple(records)


def conflicting_date_records(event: CatalogEvent, value: object, sources: Mapping[str, object]) -> bool:
    dates = set()
    for item in evidence_records(value):
        source = sources.get(str(item.get("source_id", "")))
        if source is not None and source.authority == "official" and event.competition_key in source.competition_keys and item.get("source_url") in source.urls_by_year.values():
            if item.get("date_decision") == "verified" and item.get("source_current", True) is True and item.get("competition_key") == event.competition_key and item.get("season") == event.season and item.get("stage") == event.stage and item.get("confirmed_start_date") and item.get("confirmed_end_date"):
                if isinstance(item["confirmed_start_date"], str) and isinstance(item["confirmed_end_date"], str):
                    dates.add((item["confirmed_start_date"], item["confirmed_end_date"]))
    return len(dates) > 1


def has_verified_audience(event: CatalogEvent, value: object, sources: Mapping[str, object] | None = None) -> bool:
    if event.coverage not in {"national", "shared_major"}:
        return False
    return any(
        item.get("audience_decision") == "verified"
        and valid_check_time(item.get("audience_checked_at"))
        and item.get("audience_statement")
        and item.get("source_id")
        and item.get("source_url")
        and item.get("source_current", True) is True
        and (sources is None or (
            (source := sources.get(str(item.get("source_id", "")))) is not None
            and event.competition_key in source.competition_keys
            and item.get("source_url") in source.urls_by_year.values()
        ))
        and item.get("coverage") == event.coverage
        and isinstance(item.get("audience_countries"), list)
        and all(isinstance(country, str) for country in item["audience_countries"])
        and set(item["audience_countries"]) == set(event.audience_countries)
        and (event.coverage != "national" or bool(event.audience_countries))
        for item in evidence_records(value)
    )
