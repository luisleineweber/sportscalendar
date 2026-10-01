from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import os
import uuid

from sportkalender.catalog_model import CatalogEvent
from sportkalender.catalog_coverage import CoverageContract, build_coverage_report
from sportkalender.catalog_sources import SourceDefinition
from sportkalender.catalog_tsv import catalog_event_to_row, write_catalog_tsv
from sportkalender.catalog_validation import CatalogValidationResult
from sportkalender.catalog_validation import validate_manifest, validate_manifest_payload
from sportkalender.catalog_registry import load_registry


@dataclass(frozen=True, slots=True)
class ReleaseCandidate:
    year: int
    source_path: Path
    validation: CatalogValidationResult
    status: str = "ready"
    evidence: dict[str, object] | None = None
    source_summary: str | None = None


def _canonical_events(events: tuple[CatalogEvent, ...]) -> list[dict[str, str]]:
    return [
        {key: row[key] for key in sorted(row)}
        for row in sorted((catalog_event_to_row(event) for event in events), key=lambda row: row["event_id"])
    ]


def calculate_revision(candidates: tuple[ReleaseCandidate, ...], registry_paths: tuple[Path, ...] = ()) -> str:
    payload = {
        "schema_version": 1,
        "release_evidence_schema": 3,
        "catalogs": {
            str(candidate.year): _canonical_events(candidate.validation.events)
            for candidate in sorted(candidates, key=lambda item: item.year)
        },
        "evidence": {
            str(candidate.year): candidate.evidence or {}
            for candidate in sorted(candidates, key=lambda item: item.year)
        },
        "statuses": {str(candidate.year): candidate.status for candidate in candidates},
        "registries": {
            str(index): sha256(path.read_bytes()).hexdigest()
            for index, path in enumerate(registry_paths)
        },
    }
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()[:16]


def _relative_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def build_manifest(
    candidates: tuple[ReleaseCandidate, ...],
    *,
    manifest_path: Path,
    release_root: Path,
    revision: str,
    default_id: str,
    registry_paths: tuple[Path, ...] = (),
    coverage_families: CoverageContract = CoverageContract(),
    sources: dict[str, SourceDefinition] | None = None,
    preserved_entries: tuple[dict[str, object], ...] = (),
) -> dict[str, object]:
    entries_by_id = {str(entry["id"]): dict(entry) for entry in preserved_entries if entry.get("id")}
    updated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    for candidate in sorted(candidates, key=lambda item: item.year):
        catalog_file = release_root / revision / f"catalog_{candidate.year}.tsv"
        evidence_file = release_root / revision / f"catalog_{candidate.year}.json"
        entries_by_id[str(candidate.year)] = {
            "id": str(candidate.year),
            "year": candidate.year,
            "file": _relative_path(catalog_file, manifest_path.parent),
            "status": candidate.status,
            "revision": revision,
            "updated_at": updated_at,
            "event_count": candidate.validation.summary["stored_rows"],
            "evidence": _relative_path(evidence_file, manifest_path.parent),
            "summary": candidate.validation.summary,
            "source_summary": candidate.source_summary or "Source checks not supplied for this catalog.",
            "coverage": build_coverage_report(
                candidate.validation.events,
                candidate.evidence or {},
                candidate.year,
                coverage_families,
                sources,
            ),
        }
    entries = sorted(entries_by_id.values(), key=lambda item: int(item["year"]))
    manifest: dict[str, object] = {"schema_version": 1, "default": default_id, "catalogs": entries}
    manifest.update(load_web_registry(registry_paths))
    return manifest


def load_web_registry(registry_paths: tuple[Path, ...]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for path in registry_paths:
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if path.name == "sports.json" and isinstance(source, dict):
            groups = {
                str(item.get("key")): str(item.get("display_name", item.get("key", "")))
                for item in source.get("groups", [])
                if isinstance(item, dict)
            }
            payload["sports"] = [
                {
                    "key": item.get("key"),
                    "label": item.get("display_name", item.get("key")),
                    "group": groups.get(str(item.get("group_key")), "Other Sports"),
                    "order": item.get("order", 0),
                    "aliases": item.get("aliases", []),
                }
                for item in source.get("sports", [])
                if isinstance(item, dict)
            ]
        if path.name == "competitions.json" and isinstance(source, dict):
            payload["competitions"] = [
                {
                    "key": item.get("key"),
                    "label": item.get("display_name", item.get("key")),
                    "sportKey": item.get("sport_key"),
                    "kind": item.get("kind", "competition"),
                    "primaryDisplayGroup": _web_display_group(item.get("primary_display_group")),
                    "audienceCountries": item.get("audience_countries", []),
                    "aliases": item.get("aliases", []),
                }
                for item in source.get("competitions", [])
                if isinstance(item, dict)
            ]
    existing_keys = {item["key"] for item in payload.get("competitions", [])}
    for sport in payload.get("sports", []):
        key = f"catalog_{sport['key']}"
        if key not in existing_keys:
            payload.setdefault("competitions", []).append({
                "key": key,
                "label": f"Other {sport['label']} events",
                "sportKey": sport["key"],
                "kind": "competition",
                "primaryDisplayGroup": "unassigned",
                "audienceCountries": [],
                "aliases": [],
            })
    return payload


def _web_display_group(value: object) -> str:
    text = str(value or "").strip()
    if text.casefold() == "international":
        return "international"
    if len(text) == 2 and text.isalpha():
        return f"country:{text.upper()}"
    return text


def write_release_batch(
    candidates: tuple[ReleaseCandidate, ...],
    *,
    manifest_path: Path,
    release_root: Path,
    registry_paths: tuple[Path, ...],
    coverage_families: CoverageContract = CoverageContract(),
    sources: dict[str, SourceDefinition] | None = None,
    default_id: str,
    dry_run: bool = False,
    preserved_entries: tuple[dict[str, object], ...] = (),
) -> tuple[str, dict[str, object]]:
    revision = calculate_revision(candidates, registry_paths)
    manifest = build_manifest(
        candidates,
        manifest_path=manifest_path,
        release_root=release_root,
        revision=revision,
        default_id=default_id,
        registry_paths=registry_paths,
        coverage_families=coverage_families,
        sources=sources,
        preserved_entries=preserved_entries,
    )
    registry = load_registry(registry_paths[0], registry_paths[1])
    _, issues = validate_manifest_payload(
        manifest, manifest_path, registry,
        coverage_contract=coverage_families, sources=sources or {},
        catalog_overrides={
            str(candidate.year): (
                candidate.validation,
                {event.event_id: (candidate.evidence or {}).get(event.event_id, []) for event in candidate.validation.events},
            )
            for candidate in candidates
        },
    )
    if issues:
        raise ValueError("Release checks failed: " + "; ".join(issue.message for issue in issues))
    if dry_run:
        return revision, manifest

    if manifest_path.exists():
        current = json.loads(manifest_path.read_text(encoding="utf-8"))
        def without_update_times(value):
            return {**value, "catalogs": [{key: item for key, item in entry.items() if key != "updated_at"} for entry in value.get("catalogs", [])]}
        if without_update_times(current) == without_update_times(manifest):
            _, issues = validate_manifest(manifest_path, registry, coverage_contract=coverage_families, sources=sources or {})
            if issues:
                raise ValueError("Active release checks failed: " + "; ".join(issue.message for issue in issues))
            return revision, current

    release_root.mkdir(parents=True, exist_ok=True)
    final_dir = release_root / revision
    if not final_dir.exists():
        staging_dir = release_root / f".staging-{revision}-{uuid.uuid4().hex}"
        staging_dir.mkdir()
        try:
            for candidate in candidates:
                write_catalog_tsv(list(candidate.validation.events), staging_dir / f"catalog_{candidate.year}.tsv")
                evidence = {
                    "schema_version": 1,
                    "catalog_id": str(candidate.year),
                    "year": candidate.year,
                    "revision": revision,
                    "summary": candidate.validation.summary,
                    "event_ids": sorted(event.event_id for event in candidate.validation.events),
                    "event_evidence": {
                        event.event_id: (candidate.evidence or {}).get(event.event_id, [])
                        for event in candidate.validation.events
                    },
                }
                (staging_dir / f"catalog_{candidate.year}.json").write_text(
                    json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            os.replace(staging_dir, final_dir)
        except Exception:
            for child in staging_dir.glob("*"):
                child.unlink(missing_ok=True)
            staging_dir.rmdir()
            raise

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_manifest = manifest_path.with_name(f".{manifest_path.name}.{uuid.uuid4().hex}.tmp")
    temporary_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _, issues = validate_manifest(temporary_manifest, registry, coverage_contract=coverage_families, sources=sources or {})
    if issues:
        raise ValueError("Release references failed validation: " + "; ".join(issue.message for issue in issues))
    os.replace(temporary_manifest, manifest_path)
    return revision, manifest
