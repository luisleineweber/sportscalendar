from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from pathlib import Path

from icalendar import Calendar, Event

from sportkalender.catalog_ids import custom_event_id
from sportkalender.catalog_model import parse_catalog_date_range
from sportkalender.catalog_registry import load_registry
from sportkalender.catalog_tsv import read_catalog_tsv
from sportkalender.catalog_validation import validate_events

_SPORT_PREFIX_EXCEPTIONS = {"diverse", "multisportveranstaltung", "marathon"}


@dataclass(frozen=True, slots=True)
class SportEvent:
    start_date: date
    end_date_exclusive: date
    title: str
    sport: str
    location: str
    event_id: str = ""

    @property
    def summary(self) -> str:
        if not self.sport:
            return self.title
        if self.sport.casefold() in _SPORT_PREFIX_EXCEPTIONS:
            return self.title
        return f"{self.sport} - {self.title}"


def parse_date_range(raw_value: str) -> tuple[date, date] | None:
    try:
        return parse_catalog_date_range(raw_value)
    except (TypeError, ValueError):
        return None


def load_events_from_tsv(
    input_path: Path, include_sports: set[str] | None = None
) -> list[SportEvent]:
    normalized_filters = None
    if include_sports:
        normalized_filters = {item.strip().casefold() for item in include_sports if item.strip()}

    read_result = read_catalog_tsv(input_path)
    if not read_result.valid:
        messages = "; ".join(issue.message for issue in read_result.issues[:3])
        raise ValueError(f"could not read catalog {input_path}: {messages}")
    registry = None
    if read_result.is_published:
        data_dir = Path(__file__).resolve().parents[1] / "data"
        registry = load_registry(data_dir / "sports.json", data_dir / "competitions.json")
    validation = validate_events(
        read_result.events,
        registry=registry,
        require_published=read_result.is_published,
    )
    if not validation.valid:
        messages = "; ".join(issue.message for issue in validation.issues[:3])
        raise ValueError(f"catalog {input_path} failed validation: {messages}")

    events: list[SportEvent] = []
    for catalog_event in read_result.events:
        if normalized_filters and catalog_event.sport.casefold() not in normalized_filters:
            continue
        events.append(
            SportEvent(
                start_date=catalog_event.start_date,
                end_date_exclusive=catalog_event.end_date_exclusive,
                title=catalog_event.title,
                sport=catalog_event.sport,
                location=catalog_event.location,
                event_id=catalog_event.event_id,
            )
        )

    events.sort(
        key=lambda event: (
            event.start_date,
            event.end_date_exclusive,
            event.event_id,
        )
    )
    return events


def available_sports(events: list[SportEvent]) -> list[str]:
    return sorted({event.sport for event in events if event.sport}, key=str.casefold)


def write_ics(events: list[SportEvent], output_path: Path) -> None:
    calendar = Calendar()
    calendar.add("prodid", "-//Sportkalender//Calendar Export//DE")
    calendar.add("version", "2.0")
    calendar.add("calscale", "GREGORIAN")
    calendar.add("x-wr-calname", "Sportkalender")

    dtstamp = datetime.combine(date(2000, 1, 1), time.min, timezone.utc)

    for event in sorted(events, key=lambda item: (item.start_date, item.end_date_exclusive, item.event_id)):
        ics_event = Event()
        ics_event.add("summary", event.summary)
        ics_event.add("dtstart", event.start_date)
        ics_event.add("dtend", event.end_date_exclusive)
        if event.location:
            ics_event.add("location", event.location)

        event_id = event.event_id or custom_event_id(
            start_date=event.start_date.isoformat(),
            end_date_exclusive=event.end_date_exclusive.isoformat(),
            title=event.title,
            sport=event.sport,
            location=event.location,
        )
        uid = f"{event_id}@sportkalender"
        ics_event.add("uid", uid)
        ics_event.add("dtstamp", dtstamp)

        calendar.add_component(ics_event)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as target:
        target.write(calendar.to_ical())
