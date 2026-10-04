from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Mapping

from sportkalender.catalog_evidence import has_verified_audience, verified_date_records
from sportkalender.catalog_ids import stable_event_id
from sportkalender.catalog_model import ALLOWED_EVENT_KINDS, CatalogEvent, TARGET_COUNTRIES, UK_HOME_NATIONS, is_valid_season
from sportkalender.catalog_registry import CatalogRegistry


@dataclass(frozen=True, slots=True)
class CoverageContract:
    goals: tuple[dict[str, object], ...] = ()
    highlights: tuple[dict[str, object], ...] = ()


def load_coverage_families(path: Path, registry: CatalogRegistry) -> CoverageContract:
    source = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(source, dict) or source.get("schema_version") != 2:
        raise ValueError(f"invalid coverage contract: {path}; schema_version must be 2")
    goals, highlights = source.get("goals"), source.get("highlights")
    if not isinstance(goals, list) or not isinstance(highlights, list):
        raise ValueError("coverage contract needs goals and highlights arrays")
    seen_goals = set()
    for goal in goals:
        if not isinstance(goal, dict) or goal.get("country") not in TARGET_COUNTRIES:
            raise ValueError("coverage goal has an unknown country")
        if goal.get("sport_key") not in {*registry.sports, "other_national"}:
            raise ValueError("coverage goal has an unknown sport")
        key = (goal["country"], goal["sport_key"])
        if key in seen_goals:
            raise ValueError(f"duplicate coverage goal: {key}")
        seen_goals.add(key)
    seen = set()
    league_stages: dict[tuple[object, ...], set[str]] = {}
    normalized = []
    for index, record in enumerate(highlights, 1):
        if not isinstance(record, dict):
            raise ValueError(f"coverage highlight {index} is not an object")
        item = dict(record)
        competition = registry.competitions.get(str(item.get("competition_key", "")))
        if competition is None or competition.sport_key != item.get("sport_key"):
            raise ValueError(f"coverage highlight {index} has an unknown competition or sport")
        if item.get("country") not in TARGET_COUNTRIES | {"International"}:
            raise ValueError(f"coverage highlight {index} has an unknown country")
        home_nation = item.get("uk_home_nation", "")
        if home_nation and (item["country"] != "GB" or home_nation not in UK_HOME_NATIONS):
            raise ValueError(f"coverage highlight {index} has an invalid UK home nation")
        if type(item.get("catalog_year")) is not int or not 1900 <= item["catalog_year"] <= 9998:
            raise ValueError(f"coverage highlight {index} needs a catalog year")
        if type(item.get("required")) is not bool or not is_valid_season(str(item.get("season", ""))):
            raise ValueError(f"coverage highlight {index} needs an explicit season and required flag")
        if item.get("event_kind") not in ALLOWED_EVENT_KINDS or not item.get("stage"):
            raise ValueError(f"coverage highlight {index} needs an event kind and stage")
        if item["event_kind"] == "season" and item["stage"] not in {"season_opener", "final_matchday", "playoff_final", "final_tournament", "all_star"}:
            raise ValueError(f"coverage highlight {index} has an invalid league stage")
        source_ids = item.get("source_ids", [])
        if not isinstance(source_ids, list) or any(not isinstance(value, str) or not value for value in source_ids):
            raise ValueError(f"coverage highlight {index} has invalid source IDs")
        start, end = item.get("expected_start_date"), item.get("expected_end_date")
        if start is not None or end is not None:
            try:
                start_date, end_date = date.fromisoformat(start), date.fromisoformat(end)
            except (ValueError, TypeError) as error:
                raise ValueError(f"coverage highlight {index} has an invalid date window") from error
            if end_date < start_date or start_date.year > item["catalog_year"] or end_date.year < item["catalog_year"]:
                raise ValueError(f"coverage highlight {index} does not overlap its catalog year")
            if not item.get("date_statement") or not source_ids:
                raise ValueError(f"coverage highlight {index} needs date window evidence")
        item["expected_event_id"] = stable_event_id(
            competition_key=competition.key, season=item["season"], event_kind=item["event_kind"],
            division=str(item.get("division", "")), gender=str(item.get("gender", "")), stage=item["stage"],
        )
        identity = (item["catalog_year"], item["expected_event_id"], item["country"], home_nation)
        if identity in seen:
            raise ValueError(f"duplicate coverage highlight: {identity}")
        seen.add(identity)
        if item["required"] and competition.kind == "league":
            key = (competition.key, item["season"], item.get("division", ""), item.get("gender", ""), item["country"])
            league_stages.setdefault(key, set()).add(item["stage"])
        normalized.append(item)
    for key, stages in league_stages.items():
        if "season_opener" not in stages or not stages & {"final_matchday", "playoff_final", "final_tournament"}:
            raise ValueError(f"required league {key} needs separate opener and closing records")
        closing = registry.competitions[key[0]].closing_stage
        if closing and closing not in stages:
            raise ValueError(f"required league {key} must use its title-deciding {closing}")
    return CoverageContract(tuple(goals), tuple(normalized))


def build_coverage_report(
    events: tuple[CatalogEvent, ...], evidence: dict[str, object], year: int,
    families: CoverageContract, sources: Mapping[str, object] | None = None,
) -> dict[str, object]:
    by_id = {event.event_id: event for event in events}
    rows = []
    for highlight in families.highlights:
        if highlight["catalog_year"] != year:
            continue
        event = by_id.get(highlight["expected_event_id"])
        matching = event is not None and (
            event.sport_key == highlight["sport_key"]
            and event.season == highlight["season"] and event.stage == highlight["stage"]
            and event.start_date < date(year + 1, 1, 1) and event.end_date_exclusive > date(year, 1, 1)
            and (event.coverage == "shared_major" if highlight["country"] == "International" else highlight["country"] in event.audience_countries)
            and (not highlight.get("uk_home_nation") or highlight["uk_home_nation"] in event.uk_home_nations)
        )
        records = verified_date_records(event, evidence.get(event.event_id), sources or {}) if matching else ()
        if highlight.get("source_ids"):
            records = tuple(item for item in records if item["source_id"] in highlight["source_ids"])
        if highlight.get("rejection_reason"):
            status, reason = "rejected", str(highlight["rejection_reason"])
        elif records:
            status, reason = "verified", ""
        elif matching:
            status, reason = "pending_date_check", "Official evidence must confirm this edition, stage, and full date range."
        else:
            status, reason = "missing_source", "The expected highlight has no published event."
        blocking = bool(highlight["required"] and status != "verified")
        rows.append({
            **highlight, "status": status, "available_count": int(bool(matching)),
            "blocks_ready": blocking, "blocking_reason": reason if blocking else "",
            "date_evidence": list(records),
            "actual_start_date": event.start_date.isoformat() if matching else None,
            "actual_end_date": event.inclusive_end_date.isoformat() if matching else None,
        })
    required = [row for row in rows if row["required"]]
    optional = [row for row in rows if not row["required"]]
    goals = []
    for goal in families.goals:
        national = {
            event.event_id for event in events
            if event.coverage == "national" and goal["country"] in event.audience_countries
            and (event.sport_key == goal["sport_key"] if goal["sport_key"] != "other_national" else event.sport_key not in {"football", "basketball", "athletics"})
        }
        goals.append({**goal, "catalog_year": year, "available_count": len(national), "status": "available" if national else "gap", "blocks_ready": False})
    audience = [
        {"event_id": event.event_id, "title": event.title, "coverage": event.coverage,
         "status": "unresolved", "blocks_ready": True,
         "blocking_reason": "Audience scope needs reviewed evidence."}
        for event in events if not has_verified_audience(event, evidence.get(event.event_id), sources or {})
    ]
    counts = Counter(row["status"] for row in required)
    return {
        "catalog_year": year, "expected_count": len(required),
        "verified_count": counts["verified"], "pending_count": len(required) - counts["verified"],
        "optional_pending_count": sum(row["status"] != "verified" for row in optional),
        "by_status": dict(sorted(counts.items())), "rows": rows, "goals": goals,
        "audience_review": audience, "unresolved_audience_count": len(audience),
        "published_event_count": len(by_id),
    }
