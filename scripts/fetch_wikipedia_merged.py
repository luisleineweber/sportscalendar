from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime
from io import StringIO
from pathlib import Path
import re
import sys
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from lxml import html
import pandas as pd

SOURCE_URLS = {
    "de": "https://de.wikipedia.org/wiki/Portal:Sport/Sportkalender_{year}",
    "en": "https://en.wikipedia.org/wiki/{year}_in_sports",
}
USER_AGENT = "SportkalenderBot/0.1 (+https://github.com/luisleineweber/sportscalendar)"
FINAL_OUTPUT_COLUMNS = ["Datum", "Ereignis", "Sportart", "Ort"]
MONTH_NAME_TO_NUMBER = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
    "januar": 1,
    "jan": 1,
    "februar": 2,
    "feb": 2,
    "mrz": 3,
    "maerz": 3,
    "m\u00e4rz": 3,
    "märz": 3,
    "april": 4,
    "mai": 5,
    "juni": 6,
    "juli": 7,
    "august": 8,
    "september": 9,
    "oktober": 10,
    "okt": 10,
    "november": 11,
    "dezember": 12,
}
GERMAN_DATE_TOKEN_PATTERN = re.compile(r"(\d{1,2}\.\d{1,2}\.\d{4})")
DASH_PATTERN = re.compile(r"\s*(?:-|–|—|−|‒|―|~|\uFFFD)\s*")
WHITESPACE_PATTERN = re.compile(r"\s+")
LEADING_MARKER_PATTERN = re.compile(r"^(?:[/|]+(?:\s*[/|]+)*)\s*")
DEBUG_OUTPUT_COLUMNS = [
    "date_raw",
    "event_raw",
    "sport_raw",
    "location_raw",
    "status_raw",
    "winner_raw",
    "source",
    "source_url",
    "source_table_index",
    "source_heading",
    "source_month",
    "row_order",
    "date",
    "event",
    "sport",
    "location",
    "sort_start_date",
    "sort_end_date",
    "final_row_key",
    "is_valid_final_row",
    "drop_reason",
    "duplicate_exact",
    "duplicate_exact_preferred",
    "keep_final_row",
]


@dataclass(frozen=True, slots=True)
class TableContext:
    heading: str | None
    month: int | None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch and merge German and English Wikipedia sports tables into final/debug TSV outputs.",
    )
    parser.add_argument("--year", type=int, default=datetime.now().year, help="Year to fetch.")
    parser.add_argument(
        "--output-final",
        type=Path,
        help="Final parser-compatible TSV path. Defaults to data/sportkalender_<year>.tsv.",
    )
    parser.add_argument(
        "--output-debug",
        type=Path,
        help="Debug TSV path. Defaults to data/sportkalender_<year>_debug.tsv.",
    )
    parser.add_argument(
        "--output-source-dir",
        type=Path,
        default=Path("data/sources"),
        help="Optional directory for per-source debug exports.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and normalize data without writing repo-tracked files.",
    )
    parser.add_argument(
        "--keep-source-exports",
        action="store_true",
        help="Write per-source debug TSVs under the configured source output directory.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print table filtering and dedup details.",
    )
    return parser


def build_source_urls(year: int) -> dict[str, str]:
    return {source: template.format(year=year) for source, template in SOURCE_URLS.items()}


def fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_tables(url: str, source: str) -> list[tuple[pd.DataFrame, TableContext]]:
    return parse_tables(fetch_html(url), source)


def parse_tables(html_text: str, source: str) -> list[tuple[pd.DataFrame, TableContext]]:
    document = html.fromstring(html_text)
    tables = document.xpath("//table[contains(concat(' ', normalize-space(@class), ' '), ' wikitable ')]")

    parsed_tables: list[tuple[pd.DataFrame, TableContext]] = []
    for table_index, table_element in enumerate(tables):
        table_html = html.tostring(table_element, encoding="unicode")
        frames = pd.read_html(StringIO(table_html))
        if not frames:
            continue

        frame = prepare_table(frames[0])
        context = TableContext(
            heading=extract_nearest_heading(table_element),
            month=extract_heading_month(extract_nearest_heading(table_element), source),
        )
        parsed_tables.append((frame, context))

    return parsed_tables


def prepare_table(table: pd.DataFrame) -> pd.DataFrame:
    prepared = table.copy()
    prepared.columns = uniqueify_columns([flatten_column_label(column) for column in prepared.columns])
    return prepared


def flatten_column_label(label: object) -> str:
    if isinstance(label, tuple):
        parts = []
        for part in label:
            if pd.isna(part):
                continue
            text = " ".join(str(part).split())
            if not text or text.startswith("Unnamed:"):
                continue
            parts.append(text)
        if parts:
            return " ".join(parts)
    text = " ".join(str(label).split())
    return text or "column"


def uniqueify_columns(columns: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    unique_columns: list[str] = []
    for column in columns:
        counts[column] = counts.get(column, 0) + 1
        if counts[column] == 1:
            unique_columns.append(column)
        else:
            unique_columns.append(f"{column} [{counts[column]}]")
    return unique_columns


def extract_nearest_heading(table_element: html.HtmlElement) -> str | None:
    heading = table_element.xpath(
        "normalize-space(string(preceding::*[contains(concat(' ', normalize-space(@class), ' '), ' mw-heading ')][1]))"
    )
    if not heading:
        heading = table_element.xpath("normalize-space(string(preceding::*[self::h2 or self::h3][1]))")
    heading = heading.replace("[edit]", "").strip()
    heading = WHITESPACE_PATTERN.sub(" ", heading)
    return heading or None


def extract_heading_month(heading: str | None, source: str) -> int | None:
    if not heading:
        return None

    first_token = heading.split(" ", 1)[0]
    month = parse_month_token(first_token)
    if source == "de" and month is not None:
        return month
    if source == "en" and month is not None:
        return month
    return None


def is_de_sport_table(table: pd.DataFrame) -> bool:
    headers = {normalize_header_name(column) for column in table.columns}
    required = {"datum", "ereignis", "sportart", "ort"}
    return len(headers & required) >= 2


def is_en_sport_table(table: pd.DataFrame) -> bool:
    date_column = find_column_name(table, ["Date", "Dates"])
    event_column = find_column_name(table, ["Event", "Venue/Event", "Tournament", "Competition"])
    sport_or_eventish = find_column_name(
        table,
        ["Sport", "Discipline", "Event", "Venue/Event", "Tournament", "Competition"],
    )
    return date_column is not None and event_column is not None and sport_or_eventish is not None


def find_column_name(table: pd.DataFrame, candidates: list[str]) -> str | None:
    normalized_candidates = {normalize_header_name(candidate) for candidate in candidates}
    for column in table.columns:
        if normalize_header_name(column).split(" [", 1)[0] in normalized_candidates:
            return column
    return None


def normalize_header_name(value: object) -> str:
    text = " ".join(str(value).replace("\n", " ").split())
    return text.casefold()


def empty_text_series(length: int) -> pd.Series:
    return pd.Series([pd.NA] * length, dtype="object")


def get_column_series(table: pd.DataFrame, column_name: str | None) -> pd.Series:
    if column_name is None:
        return empty_text_series(len(table))
    series = table[column_name]
    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]
    return series.astype("object")


def normalize_de_table(
    table: pd.DataFrame,
    table_index: int,
    source_url: str,
    context: TableContext,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date_raw": get_column_series(table, find_column_name(table, ["Datum"])),
            "event_raw": get_column_series(table, find_column_name(table, ["Ereignis"])),
            "sport_raw": get_column_series(table, find_column_name(table, ["Sportart"])),
            "location_raw": get_column_series(table, find_column_name(table, ["Ort"])),
            "status_raw": empty_text_series(len(table)),
            "winner_raw": empty_text_series(len(table)),
            "source": pd.Series(["de"] * len(table), dtype="object"),
            "source_url": pd.Series([source_url] * len(table), dtype="object"),
            "source_table_index": pd.Series([table_index] * len(table), dtype="Int64"),
            "source_heading": pd.Series([context.heading] * len(table), dtype="object"),
            "source_month": pd.Series([context.month] * len(table), dtype="Int64"),
        }
    )


def normalize_en_table(
    table: pd.DataFrame,
    table_index: int,
    source_url: str,
    context: TableContext,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date_raw": get_column_series(table, find_column_name(table, ["Date", "Dates"])),
            "event_raw": get_column_series(
                table,
                find_column_name(table, ["Event", "Venue/Event", "Tournament", "Competition"]),
            ),
            "sport_raw": get_column_series(table, find_column_name(table, ["Sport", "Discipline"])),
            "location_raw": get_column_series(table, find_column_name(table, ["Venue", "Location"])),
            "status_raw": get_column_series(table, find_column_name(table, ["Status"])),
            "winner_raw": get_column_series(
                table,
                find_column_name(table, ["Winner(s)", "Winner/s", "Champions / Winners"]),
            ),
            "source": pd.Series(["en"] * len(table), dtype="object"),
            "source_url": pd.Series([source_url] * len(table), dtype="object"),
            "source_table_index": pd.Series([table_index] * len(table), dtype="Int64"),
            "source_heading": pd.Series([context.heading] * len(table), dtype="object"),
            "source_month": pd.Series([context.month] * len(table), dtype="Int64"),
        }
    )


def normalize_text_fields(dataframe: pd.DataFrame) -> pd.DataFrame:
    normalized = dataframe.copy()
    for column in ["date_raw", "sport_raw", "location_raw", "status_raw", "winner_raw", "source_heading"]:
        normalized[column] = normalized[column].map(clean_text)
    normalized["event_raw"] = normalized["event_raw"].map(clean_event_text)

    normalized["event"] = normalized["event_raw"]
    normalized["sport"] = normalized["sport_raw"]
    normalized["location"] = normalized["location_raw"]
    normalized["date"] = pd.Series([pd.NA] * len(normalized), dtype="object")
    normalized["sort_start_date"] = pd.Series([pd.NA] * len(normalized), dtype="object")
    normalized["sort_end_date"] = pd.Series([pd.NA] * len(normalized), dtype="object")
    normalized["final_row_key"] = pd.Series([pd.NA] * len(normalized), dtype="object")
    normalized["is_valid_final_row"] = False
    normalized["drop_reason"] = pd.Series([pd.NA] * len(normalized), dtype="object")
    normalized["duplicate_exact"] = False
    normalized["duplicate_exact_preferred"] = False
    normalized["keep_final_row"] = False
    return normalized


def clean_text(value: object) -> object:
    if pd.isna(value):
        return pd.NA

    text = str(value).replace("\xa0", " ").replace("\u202f", " ").replace("\n", " ")
    text = re.sub(r"\[[^\]]+\]", "", text)
    text = WHITESPACE_PATTERN.sub(" ", text).strip()
    if not text or text.casefold() in {"nan", "none", "nat"}:
        return pd.NA
    return text


def clean_event_text(value: object) -> object:
    cleaned = clean_text(value)
    if pd.isna(cleaned):
        return pd.NA

    text = LEADING_MARKER_PATTERN.sub("", str(cleaned)).strip()
    return text if text else pd.NA


def build_final_candidates(dataframe: pd.DataFrame, year: int) -> pd.DataFrame:
    final_candidates = dataframe.copy()

    for index, row in final_candidates.iterrows():
        event = row["event"]
        sport = row["sport"]
        raw_date = row["date_raw"]

        if pd.isna(raw_date):
            final_candidates.at[index, "drop_reason"] = "missing_date"
            continue
        if pd.isna(event):
            final_candidates.at[index, "drop_reason"] = "missing_event"
            continue
        if pd.isna(sport):
            final_candidates.at[index, "drop_reason"] = "missing_sport"
            continue

        context_month = None
        source_month = row["source_month"]
        if not pd.isna(source_month):
            context_month = int(source_month)

        normalized_date, sort_start, sort_end = normalize_date_value(
            str(raw_date),
            row["source"],
            year=year,
            context_month=context_month,
        )
        if normalized_date is None or sort_start is None or sort_end is None:
            final_candidates.at[index, "drop_reason"] = "unparseable_date"
            continue
        if sort_end < sort_start:
            final_candidates.at[index, "drop_reason"] = "reversed_date_range"
            continue

        location = row["location"] if not pd.isna(row["location"]) else ""
        key = "|".join(
            [
                normalize_key_part(normalized_date),
                normalize_key_part(str(event)),
                normalize_key_part(str(sport)),
                normalize_key_part(location),
            ]
        )

        final_candidates.at[index, "date"] = normalized_date
        final_candidates.at[index, "sort_start_date"] = sort_start
        final_candidates.at[index, "sort_end_date"] = sort_end
        final_candidates.at[index, "final_row_key"] = key
        final_candidates.at[index, "drop_reason"] = pd.NA
        final_candidates.at[index, "is_valid_final_row"] = True

    return final_candidates


def normalize_date_value(
    raw_date: str,
    source: str,
    *,
    year: int,
    context_month: int | None,
) -> tuple[str | None, str | None, str | None]:
    if source == "de":
        return normalize_german_date(raw_date, year=year, context_month=context_month)
    if source == "en":
        return normalize_english_date(raw_date, year=year, context_month=context_month)
    return None, None, None


def normalize_german_date(
    raw_date: str,
    *,
    year: int,
    context_month: int | None,
) -> tuple[str | None, str | None, str | None]:
    text = clean_text(raw_date)
    if pd.isna(text):
        return None, None, None
    normalized = DASH_PATTERN.sub(" - ", unicodedata.normalize("NFKC", str(text)))
    normalized = WHITESPACE_PATTERN.sub(" ", normalized).strip()
    pieces = normalized.split(" - ", 1)
    start_piece = parse_german_date_piece(pieces[0])
    end_piece = parse_german_date_piece(pieces[1]) if len(pieces) == 2 else start_piece
    if start_piece is None or end_piece is None:
        return None, None, None
    start_date, end_date = resolve_german_range(start_piece, end_piece, year=year, context_month=context_month)
    if start_date is None or end_date is None:
        return None, None, None
    return format_final_date_range(start_date, end_date), start_date.isoformat(), end_date.isoformat()


def parse_german_date_piece(piece: str) -> tuple[int, int | None, int | None] | None:
    numeric_match = GERMAN_DATE_TOKEN_PATTERN.fullmatch(piece.strip())
    if numeric_match:
        parsed = parse_german_date_token(numeric_match.group(1))
        if parsed is not None:
            return parsed.day, parsed.month, parsed.year
    tokens = piece.strip().replace(".", " ").split()
    if not tokens or not tokens[0].isdigit():
        return None
    day = int(tokens[0])
    month = parse_month_token(tokens[1]) if len(tokens) >= 2 else None
    explicit_year = int(tokens[2]) if len(tokens) >= 3 and tokens[2].isdigit() else None
    if len(tokens) > 3 or (len(tokens) >= 2 and month is None):
        return None
    return day, month, explicit_year


def resolve_german_range(
    start_piece: tuple[int, int | None, int | None],
    end_piece: tuple[int, int | None, int | None],
    *,
    year: int,
    context_month: int | None,
) -> tuple[date | None, date | None]:
    start_day, start_month, start_year = start_piece
    end_day, end_month, end_year = end_piece
    if start_month is None and end_month is None:
        if context_month is None:
            return None, None
        start_month = end_month = context_month
    elif start_month is None:
        start_month = context_month or (previous_month(end_month) if start_day > end_day else end_month)
    elif end_month is None:
        end_month = context_month or (next_month(start_month) if start_day > end_day else start_month)
    if start_month is None or end_month is None:
        return None, None

    resolved_start_year = start_year or year
    resolved_end_year = end_year or resolved_start_year
    if start_year is None and context_month is not None and start_month > context_month:
        resolved_start_year = year - 1
        if end_year is None:
            resolved_end_year = year
    if end_year is None and end_month < start_month:
        resolved_end_year = resolved_start_year + 1
    start_date = safe_date(resolved_start_year, start_month, start_day)
    end_date = safe_date(resolved_end_year, end_month, end_day)
    return start_date, end_date


def parse_german_date_token(value: str) -> date | None:
    try:
        day, month, year = (int(part) for part in value.split("."))
        return date(year, month, day)
    except (TypeError, ValueError):
        return None


def normalize_english_date(
    raw_date: str,
    *,
    year: int,
    context_month: int | None,
) -> tuple[str | None, str | None, str | None]:
    text = normalize_english_date_text(raw_date)
    if not text:
        return None, None, None

    if " - " in text:
        start_part, end_part = text.split(" - ", 1)
        start_piece = parse_english_date_piece(start_part)
        end_piece = parse_english_date_piece(end_part)
        if start_piece is None or end_piece is None:
            return None, None, None
        start_date, end_date = resolve_english_range(start_piece, end_piece, year=year, context_month=context_month)
        if start_date is None or end_date is None:
            return None, None, None
        return format_final_date_range(start_date, end_date), start_date.isoformat(), end_date.isoformat()

    piece = parse_english_date_piece(text)
    if piece is None:
        return None, None, None
    parsed_date = resolve_english_single(piece, year=year, context_month=context_month)
    if parsed_date is None:
        return None, None, None
    return format_final_date_range(parsed_date, parsed_date), parsed_date.isoformat(), parsed_date.isoformat()


def normalize_english_date_text(raw_date: str) -> str:
    text = clean_text(raw_date)
    if pd.isna(text):
        return ""

    normalized = unicodedata.normalize("NFKC", str(text))
    normalized = DASH_PATTERN.sub(" - ", normalized)
    normalized = normalized.replace(",", " ")
    normalized = WHITESPACE_PATTERN.sub(" ", normalized).strip()
    return normalized


def parse_english_date_piece(piece: str) -> tuple[int, int | None, int | None] | None:
    tokens = piece.strip().split()
    if len(tokens) == 1 and tokens[0].isdigit():
        return int(tokens[0]), None, None
    if len(tokens) in {2, 3}:
        first, second = tokens[:2]
        explicit_year = int(tokens[2]) if len(tokens) == 3 and tokens[2].isdigit() else None
        if len(tokens) == 3 and explicit_year is None:
            return None
        if first.isdigit():
            month = parse_month_token(second)
            if month is not None:
                return int(first), month, explicit_year
        if second.isdigit():
            month = parse_month_token(first)
            if month is not None:
                return int(second), month, explicit_year
    return None


def parse_month_token(token: str | None) -> int | None:
    if token is None:
        return None
    normalized = unicodedata.normalize("NFKC", token).casefold().replace(".", "")
    return MONTH_NAME_TO_NUMBER.get(normalized)


def resolve_english_single(
    piece: tuple[int, int | None, int | None],
    *,
    year: int,
    context_month: int | None,
) -> date | None:
    day, month, explicit_year = piece
    if month is None:
        month = context_month
    if month is None:
        return None
    return safe_date(explicit_year or year, month, day)


def resolve_english_range(
    start_piece: tuple[int, int | None, int | None],
    end_piece: tuple[int, int | None, int | None],
    *,
    year: int,
    context_month: int | None,
) -> tuple[date | None, date | None]:
    start_day, start_month, start_explicit_year = start_piece
    end_day, end_month, end_explicit_year = end_piece

    if start_month is None and end_month is None:
        if context_month is None:
            return None, None
        start_month = context_month
        end_month = context_month
    elif start_month is None:
        if context_month is not None:
            start_month = context_month
        elif end_month is not None and start_day > end_day:
            start_month = previous_month(end_month)
        else:
            start_month = end_month
    elif end_month is None:
        if context_month is not None:
            end_month = context_month
        elif start_day > end_day:
            end_month = next_month(start_month)
        else:
            end_month = start_month

    if start_month is None or end_month is None:
        return None, None

    start_year = start_explicit_year or year
    end_year = end_explicit_year or start_year
    if start_explicit_year is None and context_month is not None and start_month > context_month:
        start_year = year - 1
        if end_explicit_year is None:
            end_year = year
    if end_explicit_year is None and end_month < start_month:
        end_year = start_year + 1

    start_date = safe_date(start_year, start_month, start_day)
    end_date = safe_date(end_year, end_month, end_day)
    return start_date, end_date


def previous_month(month: int) -> int:
    return 12 if month == 1 else month - 1


def next_month(month: int) -> int:
    return 1 if month == 12 else month + 1


def safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def format_final_date_range(start: date, end: date) -> str:
    if start == end:
        return format_repo_date(start)
    return f"{format_repo_date(start)} - {format_repo_date(end)}"


def format_repo_date(value: date) -> str:
    return f"{value.day}.{value.month}.{value.year}"


def normalize_key_part(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = WHITESPACE_PATTERN.sub(" ", normalized).strip()
    return normalized


def deduplicate_final_rows(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    annotated = dataframe.copy()
    valid_rows = annotated.loc[annotated["is_valid_final_row"]].copy()
    if valid_rows.empty:
        return annotated, valid_rows

    valid_rows["source_priority"] = valid_rows["source"].map({"de": 0, "en": 1}).fillna(99)
    duplicate_counts = valid_rows.groupby("final_row_key")["final_row_key"].transform("size")
    valid_rows["duplicate_exact"] = duplicate_counts > 1
    valid_rows = valid_rows.sort_values(["final_row_key", "source_priority", "row_order"], kind="stable")
    preferred_indices = set(valid_rows.drop_duplicates(subset=["final_row_key"], keep="first").index.tolist())

    valid_rows["duplicate_exact_preferred"] = valid_rows.index.isin(preferred_indices) & valid_rows["duplicate_exact"]
    valid_rows["keep_final_row"] = valid_rows.index.isin(preferred_indices)

    annotated.loc[valid_rows.index, "duplicate_exact"] = valid_rows["duplicate_exact"]
    annotated.loc[valid_rows.index, "duplicate_exact_preferred"] = valid_rows["duplicate_exact_preferred"]
    annotated.loc[valid_rows.index, "keep_final_row"] = valid_rows["keep_final_row"]

    kept_rows = valid_rows.loc[valid_rows["keep_final_row"]].copy()
    kept_rows["sport_sort_key"] = kept_rows["sport"].map(lambda value: normalize_key_part(str(value)))
    kept_rows["event_sort_key"] = kept_rows["event"].map(lambda value: normalize_key_part(str(value)))
    kept_rows["location_sort_key"] = kept_rows["location"].map(
        lambda value: normalize_key_part("" if pd.isna(value) else str(value))
    )
    kept_rows = kept_rows.sort_values(
        ["sort_start_date", "sort_end_date", "sport_sort_key", "event_sort_key", "location_sort_key"],
        kind="stable",
    )

    return annotated, kept_rows


def write_final_tsv(final_rows: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_output = final_rows.loc[:, ["date", "event", "sport", "location"]].rename(
        columns={
            "date": "Datum",
            "event": "Ereignis",
            "sport": "Sportart",
            "location": "Ort",
        }
    )
    final_output.to_csv(output_path, sep="\t", index=False, encoding="utf-8")


def write_debug_tsv(dataframe: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.loc[:, DEBUG_OUTPUT_COLUMNS].to_csv(output_path, sep="\t", index=False, encoding="utf-8")


def print_summary(
    *,
    merged_rows: int,
    valid_rows: int,
    final_rows: int,
    dropped_rows: int,
    duplicate_rows: int,
    source_row_counts: dict[str, int],
) -> None:
    print(f"Merged rows: {merged_rows}")
    for source, count in source_row_counts.items():
        print(f"  {source}: {count}")
    print(f"Valid final candidates: {valid_rows}")
    print(f"Dropped rows: {dropped_rows}")
    print(f"Exact duplicate rows: {duplicate_rows}")
    print(f"Final rows kept: {final_rows}")


def print_verbose(message: str, *, enabled: bool) -> None:
    if enabled:
        print(message)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    output_final = args.output_final or Path("data") / f"sportkalender_{args.year}.tsv"
    output_debug = args.output_debug or Path("data") / f"sportkalender_{args.year}_debug.tsv"

    frames: list[pd.DataFrame] = []
    source_row_counts: dict[str, int] = {"de": 0, "en": 0}
    row_order = 0

    for source, url in build_source_urls(args.year).items():
        print_verbose(f"Fetching {source}: {url}", enabled=args.verbose)
        try:
            tables = fetch_tables(url, source)
        except (HTTPError, URLError, ValueError) as error:
            print(f"Warning: failed to fetch {source} from {url}: {error}", file=sys.stderr)
            continue

        print_verbose(f"  found {len(tables)} wikitable candidates", enabled=args.verbose)
        for table_index, (table, context) in enumerate(tables):
            if source == "de":
                if not is_de_sport_table(table):
                    print_verbose(f"  skip de table {table_index}: headers={list(table.columns)!r}", enabled=args.verbose)
                    continue
                frame = normalize_de_table(table, table_index, url, context)
            else:
                if not is_en_sport_table(table):
                    print_verbose(f"  skip en table {table_index}: headers={list(table.columns)!r}", enabled=args.verbose)
                    continue
                frame = normalize_en_table(table, table_index, url, context)

            if frame.empty:
                continue

            frame["row_order"] = pd.Series(range(row_order, row_order + len(frame)), dtype="Int64")
            row_order += len(frame)
            source_row_counts[source] += len(frame)
            frames.append(frame)

    if not frames:
        raise SystemExit("No source tables could be fetched and normalized.")

    merged = pd.concat(frames, ignore_index=True)
    merged = normalize_text_fields(merged)
    merged = build_final_candidates(merged, year=args.year)
    annotated, final_rows = deduplicate_final_rows(merged)

    valid_rows = int(annotated["is_valid_final_row"].sum())
    duplicate_rows = int(annotated["duplicate_exact"].sum())
    dropped_rows = len(annotated) - valid_rows

    print_summary(
        merged_rows=len(annotated),
        valid_rows=valid_rows,
        final_rows=len(final_rows),
        dropped_rows=dropped_rows,
        duplicate_rows=duplicate_rows,
        source_row_counts=source_row_counts,
    )

    if final_rows.empty:
        raise SystemExit("No valid final rows were produced. Debug output was not written.")

    if args.dry_run:
        return

    write_final_tsv(final_rows, output_final)
    write_debug_tsv(annotated, output_debug)
    print(f"Wrote final TSV to {output_final}")
    print(f"Wrote debug TSV to {output_debug}")

    if args.keep_source_exports:
        args.output_source_dir.mkdir(parents=True, exist_ok=True)
        for source in sorted(annotated["source"].dropna().unique()):
            source_path = args.output_source_dir / f"sportkalender_{args.year}_{source}.tsv"
            write_debug_tsv(annotated.loc[annotated["source"] == source].copy(), source_path)
            print(f"Wrote source debug TSV to {source_path}")


if __name__ == "__main__":
    main()
