from __future__ import annotations

from datetime import date, timedelta
import json
from pathlib import Path

from sportkalender.catalog_ids import stable_event_id
from sportkalender.catalog_model import CatalogEvent, is_valid_event_id, normalize_key
from sportkalender.catalog_registry import CatalogRegistry


def load_catalog_seeds(
    path: Path,
    registry: CatalogRegistry,
) -> tuple[tuple[CatalogEvent, ...], dict[str, object], frozenset[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read catalog seeds {path}: {error}") from error
    if not isinstance(payload, dict) or payload.get("schema_version") != 1 or not isinstance(payload.get("events"), list):
        raise ValueError(f"catalog seeds {path} has an invalid shape")

    events: list[CatalogEvent] = []
    evidence: dict[str, object] = {}
    seen_ids: set[str] = set()
    superseded_event_ids: set[str] = set()
    retired_event_ids = payload.get("retired_event_ids", [])
    if not isinstance(retired_event_ids, list) or any(
        not isinstance(event_id, str) or not is_valid_event_id(event_id)
        for event_id in retired_event_ids
    ):
        raise ValueError(f"catalog seeds {path} has invalid retired event IDs")
    superseded_event_ids.update(retired_event_ids)
    for index, record in enumerate(payload["events"], start=1):
        if not isinstance(record, dict):
            raise ValueError(f"catalog seed {index} is not an object")
        competition_key = normalize_key(record.get("competition_key"))
        competition = registry.competitions.get(competition_key)
        if competition is None:
            raise ValueError(f"catalog seed {index} has an unknown competition")
        try:
            start_date = date.fromisoformat(str(record["start_date"]))
            end_date = date.fromisoformat(str(record["end_date"]))
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"catalog seed {index} has invalid dates") from error
        title = str(record.get("title", "")).strip()
        season = str(record.get("season", "")).strip()
        event_kind = normalize_key(record.get("event_kind"))
        gender = normalize_key(record.get("gender"))
        stage = normalize_key(record.get("stage"))
        division = str(record.get("division", "")).strip()
        source_id = str(record.get("source_id", "")).strip()
        source_url = str(record.get("source_url", "")).strip()
        date_checked_at = str(record.get("date_checked_at", "")).strip()
        supersedes = record.get("supersedes", [])
        if not isinstance(supersedes, list) or any(
            not isinstance(event_id, str) or not is_valid_event_id(event_id)
            for event_id in supersedes
        ):
            raise ValueError(f"catalog seed {index} has invalid superseded event IDs")
        if end_date < start_date or not all((title, season, event_kind, gender, stage, source_id, source_url, date_checked_at)):
            raise ValueError(f"catalog seed {index} is missing a required field")
        superseded_event_ids.update(supersedes)

        event_id = stable_event_id(
            competition_key=competition_key,
            season=season,
            event_kind=event_kind,
            gender=gender,
            stage=stage,
            division=division,
        )
        if event_id in seen_ids:
            raise ValueError(f"catalog seed {index} has a duplicate event identity")
        seen_ids.add(event_id)
        for field in ("audience_countries", "host_countries", "uk_home_nations"):
            if field in record and (not isinstance(record[field], list) or any(not isinstance(value, str) for value in record[field])):
                raise ValueError(f"catalog seed {index} has invalid {field}")
        events.append(CatalogEvent(
            event_id=event_id,
            start_date=start_date,
            end_date_exclusive=end_date + timedelta(days=1),
            title=title,
            sport=registry.sports[competition.sport_key].display_name,
            competition_key=competition_key,
            season=season,
            sport_key=competition.sport_key,
            coverage=str(record.get("coverage", "national" if competition.audience_countries else "not_tagged")),
            audience_countries=tuple(record.get("audience_countries", competition.audience_countries)),
            event_kind=event_kind,
            gender=gender,
            stage=stage,
            division=division,
            location=str(record.get("location", "")),
            uk_home_nations=tuple(record.get("uk_home_nations", [])),
            host_countries=tuple(record.get("host_countries", [])),
        ))
        evidence[event_id] = [{
            "source_id": source_id,
            "source_path": path.as_posix(),
            "source_kind": "official_schedule",
            "date_decision": "verified",
            "date_checked_at": date_checked_at,
            "source_url": source_url,
            "source_hash": record.get("source_hash", ""),
            "date_statement": record.get("date_statement", ""),
            "competition_key": competition_key,
            "season": season,
            "source_year": record.get("source_year"),
            "source_season": season,
            "stage": stage,
            "confirmed_start_date": start_date.isoformat(),
            "confirmed_end_date": end_date.isoformat(),
        }]
        if record.get("audience_statement"):
            evidence[event_id][0].update({
                "audience_decision": "verified",
                "audience_checked_at": record.get("audience_checked_at", date_checked_at),
                "audience_statement": record["audience_statement"],
                "coverage": events[-1].coverage,
                "audience_countries": list(events[-1].audience_countries),
            })
    return tuple(events), evidence, frozenset(superseded_event_ids)
