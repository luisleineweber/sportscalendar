from __future__ import annotations

from hashlib import sha256
import json
import unicodedata

from sportkalender.catalog_model import CatalogEvent, normalize_key


EVENT_ID_VERSION = "v1"


def _canonical_identity(values: tuple[str, ...]) -> str:
    return json.dumps(
        {"version": EVENT_ID_VERSION, "identity": values},
        ensure_ascii=True,
        separators=(",", ":"),
    )


def _digest(prefix: str, values: tuple[str, ...]) -> str:
    digest = sha256(_canonical_identity(values).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest}"


def stable_event_id(
    *,
    competition_key: str,
    season: str,
    event_kind: str,
    division: str = "",
    gender: str = "",
    stage: str = "",
) -> str:
    values = tuple(
        normalize_key(value)
        for value in (competition_key, season, event_kind, division, gender, stage)
    )
    if not all(values[:3]):
        raise ValueError("competition_key, season, and event_kind are required for a published ID")
    return _digest("event", values)


def custom_event_id(*, start_date: str, end_date_exclusive: str, title: str, sport: str, location: str) -> str:
    values = tuple(
        unicodedata.normalize("NFC", str(value).strip())
        for value in (start_date, end_date_exclusive, title, sport, location)
    )
    if not all(values[:4]):
        raise ValueError("custom IDs require dates, title, and sport")
    encoded = "\x1f".join(values).encode("utf-8")
    hash_value = 14695981039346656037
    for byte in encoded:
        hash_value = ((hash_value ^ byte) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return f"custom:{hash_value:016x}"


def event_id_for_event(event: CatalogEvent) -> str:
    if event.is_legacy:
        return custom_event_id(
            start_date=event.start_date.isoformat(),
            end_date_exclusive=event.end_date_exclusive.isoformat(),
            title=event.title,
            sport=event.sport,
            location=event.location,
        )
    return stable_event_id(
        competition_key=event.competition_key,
        season=event.season,
        event_kind=event.event_kind,
        division=event.division,
        gender=event.gender,
        stage=event.stage,
    )
