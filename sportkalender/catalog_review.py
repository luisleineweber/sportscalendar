from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

from sportkalender.catalog_ids import event_id_for_event
from sportkalender.catalog_model import is_valid_event_id


def load_event_reviews(path: Path) -> dict[str, dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1 or not isinstance(payload.get("events"), dict):
        raise ValueError(f"invalid event reviews: {path}")
    for event_id, record in payload["events"].items():
        if not is_valid_event_id(event_id) or not isinstance(record, dict) or not record.get("reason") or record.get("event_kind") not in {"tournament", "season", "cup_final", "national_championship"}:
            raise ValueError(f"invalid event review for {event_id}")
    return payload["events"]


def apply_event_reviews(events, evidence, reviews):
    reviewed = []
    for event in events:
        record = reviews.get(event.event_id)
        if record:
            corrected = replace(event, event_kind=record["event_kind"])
            corrected = replace(corrected, event_id=event_id_for_event(corrected))
            evidence[corrected.event_id] = evidence.pop(event.event_id, [])
            event = corrected
        reviewed.append(event)
    return tuple(reviewed)
