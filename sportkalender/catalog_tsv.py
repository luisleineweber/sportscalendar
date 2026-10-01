from __future__ import annotations

from dataclasses import dataclass
import csv
from pathlib import Path

from sportkalender.catalog_ids import custom_event_id
from sportkalender.catalog_model import (
    CatalogEvent,
    format_catalog_date_range_windows_safe,
    normalize_code_list,
    normalize_key,
    normalize_text,
    parse_catalog_date_range,
)


LEGACY_HEADERS = ("Datum", "Ereignis", "Sportart", "Ort")
CATALOG_HEADERS = (
    "Datum",
    "Ereignis",
    "Sportart",
    "Ort",
    "event_id",
    "competition_key",
    "season",
    "sport_key",
    "discipline_key",
    "coverage",
    "audience_countries",
    "uk_home_nations",
    "event_kind",
    "host_countries",
    "division",
    "gender",
    "stage",
)
_HEADER_ALIASES = {normalize_key(header): header for header in CATALOG_HEADERS}


@dataclass(frozen=True, slots=True)
class CatalogReadIssue:
    line: int | None
    message: str


@dataclass(frozen=True, slots=True)
class CatalogReadResult:
    path: Path
    events: tuple[CatalogEvent, ...]
    issues: tuple[CatalogReadIssue, ...]
    is_published: bool

    @property
    def valid(self) -> bool:
        return not self.issues


def _canonical_headers(row: list[str]) -> tuple[str, ...] | None:
    normalized = tuple(normalize_key(value) for value in row)
    required = {normalize_key(header) for header in LEGACY_HEADERS[:3]}
    if not required.issubset(normalized):
        return None
    if len(set(normalized)) != len(normalized):
        return ()
    return tuple(_HEADER_ALIASES.get(value, value) for value in normalized)


def _value(row: list[str], indexes: dict[str, int], field_name: str) -> str:
    index = indexes.get(field_name)
    if index is None or index >= len(row):
        return ""
    return normalize_text(row[index])


def _legacy_event(row: list[str], line: int | None) -> CatalogEvent:
    date_value = normalize_text(row[0]) if row else ""
    title = normalize_text(row[1]) if len(row) > 1 else ""
    sport = normalize_text(row[2]) if len(row) > 2 else ""
    location = " ".join(normalize_text(value) for value in row[3:] if normalize_text(value))
    start_date, end_date_exclusive = parse_catalog_date_range(date_value)
    event_id = custom_event_id(
        start_date=start_date.isoformat(),
        end_date_exclusive=end_date_exclusive.isoformat(),
        title=title,
        sport=sport,
        location=location,
    )
    return CatalogEvent(
        event_id=event_id,
        start_date=start_date,
        end_date_exclusive=end_date_exclusive,
        title=title,
        sport=sport,
        location=location,
        sport_key=normalize_key(sport).replace(" ", "_"),
        source_row=line,
    )


def _published_event(row: list[str], indexes: dict[str, int], line: int | None) -> CatalogEvent:
    start_date, end_date_exclusive = parse_catalog_date_range(_value(row, indexes, "Datum"))
    return CatalogEvent(
        event_id=_value(row, indexes, "event_id"),
        start_date=start_date,
        end_date_exclusive=end_date_exclusive,
        title=_value(row, indexes, "Ereignis"),
        sport=_value(row, indexes, "Sportart"),
        location=_value(row, indexes, "Ort"),
        competition_key=normalize_key(_value(row, indexes, "competition_key")),
        season=_value(row, indexes, "season"),
        sport_key=normalize_key(_value(row, indexes, "sport_key")),
        discipline_key=normalize_key(_value(row, indexes, "discipline_key")),
        coverage=normalize_key(_value(row, indexes, "coverage")),
        audience_countries=normalize_code_list(_value(row, indexes, "audience_countries")),
        uk_home_nations=normalize_code_list(_value(row, indexes, "uk_home_nations")),
        event_kind=normalize_key(_value(row, indexes, "event_kind")),
        host_countries=normalize_code_list(_value(row, indexes, "host_countries")),
        division=_value(row, indexes, "division"),
        gender=normalize_key(_value(row, indexes, "gender")),
        stage=normalize_key(_value(row, indexes, "stage")),
        source_row=line,
    )


def read_catalog_tsv(path: Path, *, allow_legacy: bool = True) -> CatalogReadResult:
    issues: list[CatalogReadIssue] = []
    events: list[CatalogEvent] = []
    try:
        source = path.open("r", encoding="utf-8-sig", newline="")
    except OSError as error:
        return CatalogReadResult(path, (), (CatalogReadIssue(None, str(error)),), False)

    with source:
        rows: list[tuple[int, list[str]]] = []
        reader = csv.reader(source, delimiter="\t", strict=True)
        try:
            for row in reader:
                if not row or not any(normalize_text(value) for value in row):
                    continue
                if normalize_text(row[0]).startswith("###"):
                    continue
                rows.append((reader.line_num, row))
        except csv.Error as error:
            return CatalogReadResult(path, (), (CatalogReadIssue(reader.line_num, f"invalid TSV: {error}"),), False)

    if not rows:
        return CatalogReadResult(path, (), (CatalogReadIssue(None, "catalog is empty"),), False)

    header = _canonical_headers(rows[0][1])
    if header == ():
        return CatalogReadResult(path, (), (CatalogReadIssue(rows[0][0], "header contains duplicate columns"),), False)

    is_header = header is not None
    is_published = False
    if is_header:
        header_row_number, _ = rows[0]
        indexes = {name: index for index, name in enumerate(header)}
        missing = [name for name in LEGACY_HEADERS[:3] if name not in indexes]
        if missing:
            issues.append(CatalogReadIssue(header_row_number, f"missing required columns: {', '.join(missing)}"))
        is_published = "event_id" in indexes
        if is_published and not {"competition_key", "season", "sport_key", "coverage", "audience_countries", "event_kind"}.issubset(indexes):
            missing_catalog = [
                name
                for name in ("competition_key", "season", "sport_key", "coverage", "audience_countries", "event_kind")
                if name not in indexes
            ]
            issues.append(CatalogReadIssue(header_row_number, f"published catalog is missing columns: {', '.join(missing_catalog)}"))
        data_rows = rows[1:]
    else:
        if not allow_legacy:
            return CatalogReadResult(path, (), (CatalogReadIssue(rows[0][0], "catalog has no header"),), False)
        indexes = {}
        data_rows = rows

    for line, row in data_rows:
        try:
            if is_header:
                if len(row) > len(header):
                    issues.append(CatalogReadIssue(line, "row has more fields than the header"))
                    continue
                event = _published_event(row, indexes, line) if is_published else _legacy_event(
                    [_value(row, indexes, header_name) for header_name in LEGACY_HEADERS], line
                )
            else:
                event = _legacy_event(row, line)
            events.append(event)
        except (TypeError, ValueError, IndexError) as error:
            issues.append(CatalogReadIssue(line, str(error)))

    return CatalogReadResult(path, tuple(events), tuple(issues), is_published)


def catalog_event_to_row(event: CatalogEvent) -> dict[str, str]:
    return {
        "Datum": format_catalog_date_range_windows_safe(event.start_date, event.end_date_exclusive),
        "Ereignis": event.title,
        "Sportart": event.sport,
        "Ort": event.location,
        "event_id": event.event_id,
        "competition_key": event.competition_key,
        "season": event.season,
        "sport_key": event.sport_key,
        "discipline_key": event.discipline_key,
        "coverage": event.coverage,
        "audience_countries": ";".join(event.audience_countries),
        "uk_home_nations": ";".join(event.uk_home_nations),
        "event_kind": event.event_kind,
        "host_countries": ";".join(event.host_countries),
        "division": event.division,
        "gender": event.gender,
        "stage": event.stage,
    }


def write_catalog_tsv(events: list[CatalogEvent] | tuple[CatalogEvent, ...], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=CATALOG_HEADERS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for event in events:
            writer.writerow(catalog_event_to_row(event))
