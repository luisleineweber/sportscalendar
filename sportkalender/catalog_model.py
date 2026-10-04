from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
import re
import unicodedata


DATE_TOKEN_PATTERN = re.compile(r"(?:\d{1,2}\.\d{1,2}\.\d{4}|\d{4}-\d{2}-\d{2})")
SEASON_PATTERN = re.compile(r"^\d{4}(?:-\d{2,4})?$")
EVENT_ID_PATTERN = re.compile(r"^(?:event|custom)-[0-9a-f]{64}$")
ALLOWED_COVERAGE = frozenset({"shared_major", "national", "not_tagged"})
ALLOWED_EVENT_KINDS = frozenset({"season", "tournament", "cup_final", "national_championship"})
MAX_SEASON_EVENT_DAYS = 14
TARGET_COUNTRIES = frozenset({"DE", "US", "GB", "FR", "IT"})
UK_HOME_NATIONS = frozenset({"ENG", "SCO", "WAL", "NIR"})


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    normalized = unicodedata.normalize("NFKC", str(value))
    normalized = normalized.replace("\xa0", " ")
    return " ".join(normalized.split()).strip()


def normalize_key(value: object) -> str:
    return normalize_text(value).casefold()


def normalize_code_list(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(
        item
        for item in (normalize_text(part).upper() for part in str(value).split(";"))
        if item
    )


def _parse_date_token(token: str) -> date:
    if "." in token:
        day, month, year = (int(part) for part in token.split("."))
        return date(year, month, day)
    year, month, day = (int(part) for part in token.split("-"))
    return date(year, month, day)


def parse_catalog_date_range(raw_value: object) -> tuple[date, date]:
    normalized = normalize_text(raw_value)
    matches = DATE_TOKEN_PATTERN.findall(normalized)
    if not matches:
        raise ValueError("date contains no supported date token")
    start = _parse_date_token(matches[0])
    end = _parse_date_token(matches[1]) if len(matches) > 1 else start
    return start, end + timedelta(days=1)


def format_catalog_date_range(start_date: date, end_date_exclusive: date) -> str:
    return format_catalog_date_range_windows_safe(start_date, end_date_exclusive)


def format_catalog_date_range_windows_safe(start_date: date, end_date_exclusive: date) -> str:
    def format_date(value: date) -> str:
        return f"{value.day}.{value.month}.{value.year}"

    end_date = end_date_exclusive - timedelta(days=1)
    if start_date == end_date:
        return format_date(start_date)
    return f"{format_date(start_date)} - {format_date(end_date)}"


@dataclass(frozen=True, slots=True)
class CatalogEvent:
    event_id: str
    start_date: date
    end_date_exclusive: date
    title: str
    sport: str
    location: str = ""
    competition_key: str = ""
    season: str = ""
    sport_key: str = ""
    discipline_key: str = ""
    coverage: str = ""
    audience_countries: tuple[str, ...] = field(default_factory=tuple)
    uk_home_nations: tuple[str, ...] = field(default_factory=tuple)
    event_kind: str = ""
    host_countries: tuple[str, ...] = field(default_factory=tuple)
    division: str = ""
    gender: str = ""
    stage: str = ""
    source_row: int | None = field(default=None, compare=False)

    @property
    def inclusive_end_date(self) -> date:
        return self.end_date_exclusive - timedelta(days=1)

    @property
    def is_legacy(self) -> bool:
        return self.event_id.startswith("custom:")

    def identity_values(self) -> tuple[str, ...]:
        return (
            normalize_key(self.competition_key),
            normalize_key(self.season),
            normalize_key(self.event_kind),
            normalize_key(self.division),
            normalize_key(self.gender),
            normalize_key(self.stage),
        )

    def exact_values(self) -> tuple[object, ...]:
        return (
            self.start_date,
            self.end_date_exclusive,
            normalize_text(self.title),
            normalize_key(self.sport),
            normalize_text(self.location),
            self.sport_key, self.discipline_key, self.coverage,
            tuple(sorted(self.audience_countries)), tuple(sorted(self.uk_home_nations)),
            tuple(sorted(self.host_countries)),
            *self.identity_values(),
        )


def is_valid_event_id(value: str) -> bool:
    return bool(EVENT_ID_PATTERN.fullmatch(normalize_text(value)))


def is_valid_season(value: str) -> bool:
    return bool(SEASON_PATTERN.fullmatch(normalize_text(value)))
