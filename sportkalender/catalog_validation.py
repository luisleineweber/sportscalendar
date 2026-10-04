from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path

from sportkalender.catalog_ids import event_id_for_event
from sportkalender.catalog_evidence import has_verified_audience
from sportkalender.catalog_model import (
    ALLOWED_COVERAGE,
    ALLOWED_EVENT_KINDS,
    CatalogEvent,
    MAX_SEASON_EVENT_DAYS,
    TARGET_COUNTRIES,
    UK_HOME_NATIONS,
    is_valid_event_id,
    is_valid_season,
)
from sportkalender.catalog_registry import CatalogRegistry
from sportkalender.catalog_tsv import CatalogReadIssue, read_catalog_tsv


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    message: str
    row: int | None = None
    event_id: str | None = None


@dataclass(frozen=True, slots=True)
class CatalogValidationResult:
    path: Path | None
    events: tuple[CatalogEvent, ...]
    issues: tuple[ValidationIssue, ...]
    summary: dict[str, object]

    @property
    def valid(self) -> bool:
        return not self.issues


def _issue_from_read_issue(issue: CatalogReadIssue) -> ValidationIssue:
    return ValidationIssue("read_error", issue.message, issue.line)


def _validate_event(
    event: CatalogEvent,
    *,
    catalog_year: int | None,
    registry: CatalogRegistry | None,
    require_published: bool,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    row = event.source_row
    event_id = event.event_id or None

    if not event.title:
        issues.append(ValidationIssue("missing_title", "event title is required", row, event_id))
    if not event.sport:
        issues.append(ValidationIssue("missing_sport", "sport display name is required", row, event_id))
    if event.end_date_exclusive <= event.start_date:
        issues.append(ValidationIssue("reversed_date_range", "end date must be on or after start date", row, event_id))
    elif event.event_kind == "season" and event.stage not in {"playoff_final", "final_tournament"} and (event.end_date_exclusive - event.start_date).days > MAX_SEASON_EVENT_DAYS:
        issues.append(ValidationIssue(
            "season_range_too_long",
            f"season events must be highlights no longer than {MAX_SEASON_EVENT_DAYS} days",
            row,
            event_id,
        ))

    if require_published:
        required_fields = {
            "event_id": event.event_id,
            "competition_key": event.competition_key,
            "season": event.season,
            "sport_key": event.sport_key,
            "coverage": event.coverage,
            "event_kind": event.event_kind,
        }
        for field_name, value in required_fields.items():
            if not value:
                issues.append(ValidationIssue("missing_metadata", f"{field_name} is required", row, event_id))
        if event.event_id.startswith("custom:"):
            issues.append(ValidationIssue("custom_id", "published catalogs cannot use custom event IDs", row, event_id))
        elif not is_valid_event_id(event.event_id) or not event.event_id.startswith("event-"):
            issues.append(ValidationIssue("invalid_event_id", "event_id must use the generated event ID format", row, event_id))
        if event.event_id and event.competition_key and event.season and event.event_kind:
            try:
                expected_id = event_id_for_event(event)
            except ValueError:
                expected_id = ""
            if expected_id and event.event_id != expected_id:
                issues.append(ValidationIssue("unstable_event_id", "event_id does not match its identity fields", row, event_id))
        if event.season and not is_valid_season(event.season):
            issues.append(ValidationIssue("invalid_season", "season must be YYYY or YYYY-YY", row, event_id))
        if event.coverage and event.coverage not in ALLOWED_COVERAGE:
            issues.append(ValidationIssue("invalid_coverage", f"unknown coverage {event.coverage!r}", row, event_id))
        if event.event_kind and event.event_kind not in ALLOWED_EVENT_KINDS:
            issues.append(ValidationIssue("invalid_event_kind", f"unknown event_kind {event.event_kind!r}", row, event_id))
        if event.event_kind == "season" and not event.stage:
            issues.append(ValidationIssue("missing_stage", "league highlights require a stage", row, event_id))
        if event.coverage == "national" and not event.audience_countries:
            issues.append(ValidationIssue("missing_audience", "national events require an audience country", row, event_id))

    for country in event.audience_countries:
        if country not in TARGET_COUNTRIES:
            issues.append(ValidationIssue("invalid_audience_country", f"unknown audience country {country!r}", row, event_id))
    for country in event.host_countries:
        if len(country) != 2 or not country.isascii() or not country.isalpha():
            issues.append(ValidationIssue("invalid_host_country", f"invalid host country {country!r}", row, event_id))
    for nation in event.uk_home_nations:
        if nation not in UK_HOME_NATIONS:
            issues.append(ValidationIssue("invalid_home_nation", f"unknown UK home nation {nation!r}", row, event_id))
    if event.uk_home_nations and "GB" not in event.audience_countries:
        issues.append(ValidationIssue("home_nation_without_gb", "uk_home_nations requires GB audience", row, event_id))

    if catalog_year is not None:
        year_start = date(catalog_year, 1, 1)
        year_end = date(catalog_year + 1, 1, 1)
        if not (event.start_date < year_end and event.end_date_exclusive > year_start):
            issues.append(ValidationIssue("outside_catalog_year", f"event does not overlap catalog year {catalog_year}", row, event_id))

    if registry is not None and require_published:
        sport_definition = registry.sports.get(event.sport_key)
        if sport_definition is None:
            issues.append(ValidationIssue("unknown_sport_key", f"unknown sport_key {event.sport_key!r}", row, event_id))
        competition_definition = registry.competitions.get(event.competition_key)
        if competition_definition is None:
            issues.append(ValidationIssue("unknown_competition_key", f"unknown competition_key {event.competition_key!r}", row, event_id))
        elif competition_definition.sport_key != event.sport_key:
            issues.append(
                ValidationIssue(
                    "competition_sport_mismatch",
                    f"competition {event.competition_key!r} belongs to {competition_definition.sport_key!r}",
                    row,
                    event_id,
                )
            )
        elif event.event_kind == "season" and competition_definition.closing_stage in {"playoff_final", "final_tournament"} and event.stage == "final_matchday":
            issues.append(ValidationIssue("regular_season_closing", "playoffs decide the title; the last regular-season matchday is outside scope", row, event_id))

    return issues


def validate_ready_events(events: tuple[CatalogEvent, ...], evidence: dict[str, object], sources=None) -> tuple[ValidationIssue, ...]:
    return tuple(
        ValidationIssue("unresolved_audience", "Ready events require reviewed audience scope evidence", event.source_row, event.event_id)
        for event in events if not has_verified_audience(event, evidence.get(event.event_id), sources)
    )


def validate_events(
    events: tuple[CatalogEvent, ...] | list[CatalogEvent],
    *,
    path: Path | None = None,
    catalog_year: int | None = None,
    registry: CatalogRegistry | None = None,
    require_published: bool = True,
    read_issues: tuple[ValidationIssue, ...] = (),
) -> CatalogValidationResult:
    issues = list(read_issues)
    ids: dict[str, CatalogEvent] = {}
    exact_values: dict[tuple[object, ...], CatalogEvent] = {}
    for event in events:
        issues.extend(
            _validate_event(
                event,
                catalog_year=catalog_year,
                registry=registry,
                require_published=require_published,
            )
        )
        if not event.event_id:
            continue
        previous = ids.get(event.event_id)
        if previous is not None:
            issues.append(ValidationIssue("duplicate_event_id", "event_id is not unique", event.source_row, event.event_id))
        else:
            ids[event.event_id] = event

        exact_key = event.exact_values()
        previous_exact = exact_values.get(exact_key)
        if previous_exact is not None and previous_exact.event_id != event.event_id:
            issues.append(ValidationIssue("duplicate_event", "exact duplicate has more than one event_id", event.source_row, event.event_id))
        else:
            exact_values[exact_key] = event

    summary = build_catalog_summary(events)
    return CatalogValidationResult(path, tuple(events), tuple(issues), summary)


def build_catalog_summary(events: tuple[CatalogEvent, ...] | list[CatalogEvent]) -> dict[str, object]:
    by_sport = Counter(event.sport_key or event.sport for event in events)
    by_competition = Counter(event.competition_key for event in events if event.competition_key)
    by_kind = Counter(event.event_kind for event in events if event.event_kind)
    by_country = Counter(country for event in events for country in event.audience_countries)
    unrecognized_sports = Counter(event.sport.casefold() for event in events if event.sport_key == "other")
    return {
        "stored_rows": len(events),
        "date_valid_rows": sum(event.end_date_exclusive > event.start_date for event in events),
        "unique_event_ids": len({event.event_id for event in events if event.event_id}),
        "by_sport": dict(sorted(by_sport.items())),
        "by_competition": dict(sorted(by_competition.items())),
        "by_event_kind": dict(sorted(by_kind.items())),
        "by_audience_country": dict(sorted(by_country.items())),
        "location_rows": sum(bool(event.location) for event in events),
        "not_tagged_rows": sum(event.coverage == "not_tagged" for event in events),
        "unrecognized_sport_labels": dict(sorted(unrecognized_sports.items())),
    }


def validate_catalog_file(
    path: Path,
    *,
    catalog_year: int | None = None,
    registry: CatalogRegistry | None = None,
    require_published: bool = True,
    excluded_event_ids: frozenset[str] = frozenset(),
) -> CatalogValidationResult:
    read_result = read_catalog_tsv(path, allow_legacy=True)
    read_issues = tuple(_issue_from_read_issue(issue) for issue in read_result.issues)
    if require_published and not read_result.is_published:
        read_issues += (ValidationIssue("legacy_catalog", "published validation requires named catalog metadata columns"),)
    return validate_events(
        tuple(event for event in read_result.events if event.event_id not in excluded_event_ids),
        path=path,
        catalog_year=catalog_year,
        registry=registry,
        require_published=require_published,
        read_issues=read_issues,
    )


def validate_manifest(manifest_path: Path, registry: CatalogRegistry | None = None, *, coverage_contract=None, sources=None) -> tuple[dict[str, object], tuple[ValidationIssue, ...]]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {}, (ValidationIssue("manifest_read_error", str(error)),)
    return validate_manifest_payload(manifest, manifest_path, registry, coverage_contract=coverage_contract, sources=sources)


def validate_manifest_payload(
    manifest: object, manifest_path: Path, registry: CatalogRegistry | None = None,
    *, coverage_contract=None, sources=None,
    catalog_overrides: dict[str, tuple[CatalogValidationResult, dict[str, object]]] | None = None,
) -> tuple[dict[str, object], tuple[ValidationIssue, ...]]:
    issues: list[ValidationIssue] = []
    if not isinstance(manifest, dict):
        return {}, (ValidationIssue("manifest_shape", "manifest must be an object"),)
    if manifest.get("schema_version") != 1:
        issues.append(ValidationIssue("manifest_schema", "manifest schema_version must be 1"))
    entries = manifest.get("catalogs")
    if not isinstance(entries, list):
        return manifest, (ValidationIssue("manifest_shape", "manifest catalogs must be an array"),)
    if not isinstance(manifest.get("default"), str):
        issues.append(ValidationIssue("manifest_default", "manifest default must be a catalog ID"))
    seen_ids: set[str] = set()
    loaded: dict[str, CatalogValidationResult] = {}
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            issues.append(ValidationIssue("manifest_entry", f"catalog entry {index} is not an object"))
            continue
        catalog_id = str(entry.get("id", ""))
        if not catalog_id or catalog_id in seen_ids:
            issues.append(ValidationIssue("manifest_id", f"catalog entry {index} has a missing or duplicate id"))
            continue
        seen_ids.add(catalog_id)
        if entry.get("status") not in {"ready", "preview"}:
            issues.append(ValidationIssue("manifest_status", f"catalog {catalog_id!r} has an invalid status"))
        for field_name in ("revision", "updated_at", "file", "evidence", "event_count"):
            if field_name not in entry:
                issues.append(ValidationIssue("manifest_entry", f"catalog {catalog_id!r} is missing {field_name}"))
        try:
            year = int(entry["year"])
            catalog_path = (manifest_path.parent / str(entry["file"])).resolve()
            evidence_path = (manifest_path.parent / str(entry["evidence"])).resolve()
        except (KeyError, TypeError, ValueError) as error:
            issues.append(ValidationIssue("manifest_entry", f"catalog {catalog_id!r} has invalid year or file: {error}"))
            continue
        try:
            catalog_path.relative_to(manifest_path.parent.resolve())
            evidence_path.relative_to(manifest_path.parent.resolve())
        except ValueError:
            issues.append(ValidationIssue("manifest_path", f"catalog {catalog_id!r} points outside the manifest directory"))
            continue
        event_evidence: object = None
        candidate = (catalog_overrides or {}).get(catalog_id)
        if candidate is not None:
            result, event_evidence = candidate
        elif not evidence_path.exists():
            issues.append(ValidationIssue("manifest_evidence", f"catalog {catalog_id!r} evidence file is missing"))
        else:
            try:
                evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                issues.append(ValidationIssue("manifest_evidence", f"catalog {catalog_id!r} evidence is invalid: {error}"))
            else:
                event_evidence = evidence.get("event_evidence") if isinstance(evidence, dict) else None
                if not isinstance(event_evidence, dict):
                    issues.append(ValidationIssue("manifest_evidence", f"catalog {catalog_id!r} evidence must contain event_evidence"))
        if candidate is None:
            result = validate_catalog_file(catalog_path, catalog_year=year, registry=registry, require_published=True)
        loaded[catalog_id] = result
        issues.extend(result.issues)
        if entry.get("event_count") != result.summary["stored_rows"]:
            issues.append(ValidationIssue("manifest_count", f"catalog {catalog_id!r} event_count does not match the file"))
        if isinstance(event_evidence, dict):
            expected_event_ids = {event.event_id for event in result.events}
            if set(event_evidence) != expected_event_ids:
                issues.append(ValidationIssue("manifest_evidence", f"catalog {catalog_id!r} evidence IDs do not match the catalog"))
            if entry.get("status") == "ready":
                from sportkalender.catalog_coverage import build_coverage_report, load_coverage_families
                from sportkalender.catalog_sources import load_sources
                if registry is None:
                    issues.append(ValidationIssue("ready_configuration", "Ready validation needs the competition registry"))
                else:
                    try:
                        contract = coverage_contract if coverage_contract is not None else load_coverage_families(manifest_path.parent / "coverage.json", registry)
                        source_registry = sources if sources is not None else load_sources(manifest_path.parent / "sources.json", registry)
                        issues.extend(validate_ready_events(result.events, event_evidence, source_registry))
                        coverage = build_coverage_report(result.events, event_evidence, year, contract, source_registry)
                        if coverage["pending_count"]:
                            issues.append(ValidationIssue("pending_required_highlights", f"catalog {catalog_id!r} has pending required highlights"))
                    except (OSError, ValueError) as error:
                        issues.append(ValidationIssue("ready_configuration", str(error)))
    default_id = manifest.get("default")
    if isinstance(default_id, str) and default_id not in seen_ids:
        issues.append(ValidationIssue("manifest_default", f"default catalog {default_id!r} is not present"))

    catalog_items = list(loaded.items())
    for left_index, (left_id, left_result) in enumerate(catalog_items):
        for right_id, right_result in catalog_items[left_index + 1 :]:
            left_by_id = {event.event_id: event for event in left_result.events}
            right_by_id = {event.event_id: event for event in right_result.events}
            for event_id in left_by_id.keys() & right_by_id.keys():
                if left_by_id[event_id].exact_values() != right_by_id[event_id].exact_values():
                    issues.append(ValidationIssue("cross_catalog_conflict", f"event_id {event_id!r} differs between catalogs {left_id!r} and {right_id!r}"))
    loaded_years = {
        int(entry["year"]): str(entry["id"])
        for entry in entries
        if isinstance(entry, dict)
        and str(entry.get("id")) in loaded
        and str(entry.get("year", "")).isdigit()
    }
    ids_by_catalog = {
        catalog_id: {event.event_id for event in result.events}
        for catalog_id, result in loaded.items()
    }
    for source_id, result in loaded.items():
        for event in result.events:
            for year, target_id in loaded_years.items():
                if target_id == source_id:
                    continue
                if event.start_date < date(year + 1, 1, 1) and event.end_date_exclusive > date(year, 1, 1):
                    if event.event_id not in ids_by_catalog[target_id]:
                        issues.append(ValidationIssue("cross_catalog_missing", f"event_id {event.event_id!r} also overlaps catalog {target_id!r}"))
    return manifest, tuple(issues)
