from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path

from sportkalender.catalog_ids import stable_event_id
from sportkalender.catalog_evidence import has_verified_audience
from sportkalender.catalog_model import CatalogEvent, normalize_code_list, normalize_key, normalize_text
from sportkalender.catalog_registry import CatalogRegistry
from sportkalender.catalog_tsv import read_catalog_tsv


ENRICHMENT_FIELDS = frozenset(
    {
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
        "evidence",
    }
)


@dataclass(frozen=True, slots=True)
class EnrichmentIssue:
    row: int | None
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class CatalogEnrichmentResult:
    events: tuple[CatalogEvent, ...]
    issues: tuple[EnrichmentIssue, ...]
    evidence: dict[str, object]

    @property
    def valid(self) -> bool:
        return not self.issues


def _read_rows(path: Path) -> tuple[dict[int, dict[str, object]], tuple[EnrichmentIssue, ...]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {}, (EnrichmentIssue(None, "enrichment_read_error", str(error)),)
    if not isinstance(raw, dict) or not isinstance(raw.get("rows"), dict):
        return {}, (EnrichmentIssue(None, "enrichment_shape", "enrichment must contain a rows object"),)

    rows: dict[int, dict[str, object]] = {}
    issues: list[EnrichmentIssue] = []
    for raw_row, value in raw["rows"].items():
        try:
            row = int(raw_row)
        except (TypeError, ValueError):
            issues.append(EnrichmentIssue(None, "enrichment_row", f"row key {raw_row!r} is not an integer"))
            continue
        if row <= 0 or not isinstance(value, dict):
            issues.append(EnrichmentIssue(row, "enrichment_row", "row value must be an object with a positive row number"))
            continue
        unknown = sorted(set(value) - ENRICHMENT_FIELDS)
        if unknown:
            issues.append(EnrichmentIssue(row, "enrichment_field", f"unknown fields: {', '.join(unknown)}"))
            continue
        rows[row] = value
    return rows, tuple(issues)


def _metadata_text(value: object) -> str:
    return normalize_text(value)


def _metadata_list(value: object, field_name: str, row: int | None) -> tuple[tuple[str, ...], EnrichmentIssue | None]:
    if value is None:
        return (), None
    if isinstance(value, list):
        return tuple(normalize_text(item).upper() for item in value if normalize_text(item)), None
    if isinstance(value, str):
        return normalize_code_list(value), None
    return (), EnrichmentIssue(row, "enrichment_field", f"{field_name} must be a list or semicolon-separated string")


def enrich_events(
    events: tuple[CatalogEvent, ...] | list[CatalogEvent],
    metadata_by_row: dict[int, dict[str, object]],
    registry: CatalogRegistry,
) -> CatalogEnrichmentResult:
    enriched: list[CatalogEvent] = []
    issues: list[EnrichmentIssue] = []
    evidence: dict[str, object] = {}
    for event in events:
        row = event.source_row
        metadata = metadata_by_row.get(row or -1)
        if metadata is None:
            issues.append(EnrichmentIssue(row, "missing_enrichment", "no enrichment record exists for this row"))
            enriched.append(event)
            continue

        raw_sport_key = _metadata_text(metadata.get("sport_key"))
        sport_key = registry.sports_by_alias.get(normalize_key(raw_sport_key or event.sport))
        if sport_key is None:
            issues.append(EnrichmentIssue(row, "unknown_sport", f"no registry alias matches sport {event.sport!r}"))
            enriched.append(event)
            continue

        raw_competition_key = _metadata_text(metadata.get("competition_key"))
        competition_key = registry.competitions_by_alias.get(normalize_key(raw_competition_key))
        if competition_key is None:
            issues.append(EnrichmentIssue(row, "unknown_competition", "competition_key is required and must be registered"))
            enriched.append(event)
            continue
        competition = registry.competitions[competition_key]
        if competition.sport_key != sport_key:
            issues.append(EnrichmentIssue(row, "competition_sport_mismatch", "competition and sport do not match"))
            enriched.append(event)
            continue

        values: dict[str, object] = {
            "competition_key": competition_key,
            "season": _metadata_text(metadata.get("season")),
            "sport_key": sport_key,
            "discipline_key": normalize_key(metadata.get("discipline_key")),
            "coverage": normalize_key(metadata.get("coverage")),
            "event_kind": normalize_key(metadata.get("event_kind")),
            "division": _metadata_text(metadata.get("division")),
            "gender": normalize_key(metadata.get("gender")),
            "stage": normalize_key(metadata.get("stage")),
        }
        for field_name in ("audience_countries", "uk_home_nations", "host_countries"):
            values[field_name], list_issue = _metadata_list(metadata.get(field_name), field_name, row)
            if list_issue:
                issues.append(list_issue)
        if not values["audience_countries"]:
            values["audience_countries"] = competition.audience_countries
        if not values["season"] or not values["coverage"] or not values["event_kind"]:
            issues.append(EnrichmentIssue(row, "missing_metadata", "season, coverage, and event_kind are required"))
            enriched.append(event)
            continue

        canonical = replace(
            event,
            event_id=stable_event_id(
                competition_key=competition_key,
                season=str(values["season"]),
                event_kind=str(values["event_kind"]),
                division=str(values["division"]),
                gender=str(values["gender"]),
                stage=str(values["stage"]),
            ),
            sport=registry.sports[sport_key].display_name,
            competition_key=str(values["competition_key"]),
            season=str(values["season"]),
            sport_key=str(values["sport_key"]),
            discipline_key=str(values["discipline_key"]),
            coverage=str(values["coverage"]),
            audience_countries=tuple(values["audience_countries"]),
            uk_home_nations=tuple(values["uk_home_nations"]),
            event_kind=str(values["event_kind"]),
            host_countries=tuple(values["host_countries"]),
            division=str(values["division"]),
            gender=str(values["gender"]),
            stage=str(values["stage"]),
        )
        enriched.append(canonical)
        if "evidence" in metadata:
            evidence[canonical.event_id] = metadata["evidence"]
    return CatalogEnrichmentResult(tuple(enriched), tuple(issues), evidence)


def enrich_catalog_file(path: Path, enrichment_path: Path, registry: CatalogRegistry) -> CatalogEnrichmentResult:
    read_result = read_catalog_tsv(path)
    rows, row_issues = _read_rows(enrichment_path)
    issues = list(row_issues)
    issues.extend(EnrichmentIssue(issue.line, "catalog_read_error", issue.message) for issue in read_result.issues)
    result = enrich_events(read_result.events, rows, registry)
    return CatalogEnrichmentResult(result.events, tuple(issues) + result.issues, result.evidence)


def classify_audience(events: tuple[CatalogEvent, ...], evidence: dict[str, object]) -> tuple[CatalogEvent, ...]:
    """Keep unproved audience claims in the Preview review class."""
    return tuple(
        event if has_verified_audience(event, evidence.get(event.event_id))
        else replace(event, coverage="not_tagged", audience_countries=(), uk_home_nations=())
        for event in events
    )
