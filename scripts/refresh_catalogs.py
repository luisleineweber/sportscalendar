from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import date
import json
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sportkalender.catalog_registry import RegistryError, load_registry
from sportkalender.catalog_coverage import build_coverage_report, load_coverage_families
from sportkalender.catalog_enrichment import classify_audience, enrich_catalog_file
from sportkalender.catalog_sources import load_sources
from sportkalender.catalog_source_refresh import refresh_sources
from sportkalender.catalog_changes import compare_catalogs
from sportkalender.catalog_review import apply_event_reviews, load_event_reviews
from sportkalender.catalog_evidence import conflicting_date_records, evidence_records
from sportkalender.catalog_release import ReleaseCandidate, write_release_batch
from sportkalender.catalog_migration import promote_legacy_catalog
from sportkalender.catalog_seeds import load_catalog_seeds
from sportkalender.catalog_tsv import read_catalog_tsv
from sportkalender.catalog_validation import build_catalog_summary, validate_catalog_file, validate_events


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and publish local catalog candidates as one release batch.")
    parser.add_argument("--years", nargs="+", type=int, required=True)
    parser.add_argument("--input", action="append", default=[], metavar="YEAR=PATH", help="Candidate TSV for a year.")
    parser.add_argument("--input-dir", type=Path, default=Path("data/catalog-candidates"))
    parser.add_argument("--enrichment", action="append", default=[], metavar="YEAR=PATH", help="Metadata sidecar for a legacy candidate.")
    parser.add_argument("--enrichment-dir", type=Path, default=Path("data/catalog-enrichment"))
    parser.add_argument("--manifest", type=Path, default=Path("data/catalogs.json"))
    parser.add_argument("--release-root", type=Path, default=Path("data/releases"))
    parser.add_argument("--sports-registry", type=Path, default=Path("data/sports.json"))
    parser.add_argument("--competitions-registry", type=Path, default=Path("data/competitions.json"))
    parser.add_argument("--coverage", type=Path, default=Path("data/coverage.json"))
    parser.add_argument("--sources", type=Path, default=Path("data/sources.json"))
    parser.add_argument("--fetch-sources", action="store_true", help="Also check sources when explicit candidates are supplied.")
    parser.add_argument("--offline", action="store_true", help="Use saved source snapshots.")
    parser.add_argument("--source-cache", type=Path, default=Path(".cache/catalog-sources"))
    parser.add_argument("--report", type=Path, help="Save the monthly review report, including failed checks.")
    parser.add_argument("--event-reviews", type=Path, default=Path("data/event-reviews.json"))
    parser.add_argument("--seeds", type=Path, default=Path("data/catalog-seeds.json"))
    parser.add_argument("--default", dest="default_id", help="Catalog ID to keep as the manifest default.")
    parser.add_argument("--preview-years", nargs="*", type=int, default=[])
    parser.add_argument(
        "--bootstrap-legacy",
        action="store_true",
        help="Promote an existing four-column TSV into the published catalog schema.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def _parse_input_overrides(values: list[str], option_name: str) -> dict[int, Path]:
    overrides: dict[int, Path] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"invalid {option_name} value {value!r}; expected YEAR=PATH")
        year_text, path_text = value.split("=", 1)
        year = int(year_text)
        if year in overrides:
            raise ValueError(f"duplicate input for year {year}")
        overrides[year] = Path(path_text)
    return overrides


def _candidate_path(year: int, input_dir: Path, overrides: dict[int, Path]) -> Path:
    if year in overrides:
        return overrides[year]
    for name in (f"catalog_{year}.tsv", f"sportkalender_{year}.tsv", f"{year}.tsv"):
        path = input_dir / name
        if path.exists():
            return path
    return input_dir / f"catalog_{year}.tsv"


def _enrichment_path(year: int, enrichment_dir: Path, overrides: dict[int, Path]) -> Path:
    if year in overrides:
        return overrides[year]
    for name in (f"catalog_{year}.json", f"sportkalender_{year}.json", f"{year}.json"):
        path = enrichment_dir / name
        if path.exists():
            return path
    return enrichment_dir / f"catalog_{year}.json"


def _save_report(path: Path | None, report: dict[str, object]) -> None:
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _save_failure_report(path, source_rows, year, reason) -> None:
    _save_report(path, {"source_checks": source_rows, "catalogs": [{"catalog_year": year, "status": "rejected"}], "blockers": [reason]})


def _source_summary(events, evidence) -> dict[str, object]:
    by_source = {}
    for event in events:
        for record in evidence_records(evidence.get(event.event_id)):
            source_id = record.get("source_id")
            if isinstance(source_id, str) and source_id:
                by_source.setdefault(source_id, {})[event.event_id] = event
    return {source_id: build_catalog_summary(tuple(records.values())) for source_id, records in sorted(by_source.items())}


def _read_existing_manifest(path: Path) -> tuple[dict[str, object], tuple[dict[str, object], ...]]:
    if not path.exists():
        return {}, ()
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read existing manifest {path}: {error}") from error
    if not isinstance(manifest, dict) or not isinstance(manifest.get("catalogs"), list):
        raise ValueError(f"existing manifest {path} has an invalid shape")
    entries = tuple(entry for entry in manifest["catalogs"] if isinstance(entry, dict))
    return manifest, entries


def _project_overlapping_years(
    candidates: list[ReleaseCandidate], registry: object
) -> list[ReleaseCandidate]:
    canonical = {}
    evidence = {}
    for candidate in candidates:
        for event in candidate.validation.events:
            previous = canonical.get(event.event_id)
            if previous is not None and previous.exact_values() != event.exact_values():
                raise ValueError(f"conflicting copies of event {event.event_id}")
            canonical[event.event_id] = event
            if event.event_id in (candidate.evidence or {}):
                records = evidence.setdefault(event.event_id, [])
                for record in candidate.evidence[event.event_id]:
                    if record not in records:
                        records.append(record)

    projected = []
    for candidate in candidates:
        year = candidate.year
        events = tuple(
            event for event in canonical.values()
            if event.start_date < date(year + 1, 1, 1)
            and event.end_date_exclusive > date(year, 1, 1)
        )
        validation = validate_events(
            events,
            path=candidate.source_path,
            catalog_year=year,
            registry=registry,
            require_published=True,
        )
        if not validation.valid:
            raise ValueError(f"projected catalog {year} has validation errors")
        projected.append(replace(
            candidate,
            validation=validation,
            evidence={event.event_id: evidence.get(event.event_id, []) for event in events},
        ))
    return projected


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    years = tuple(sorted(set(args.years)))
    if not years:
        print("At least one year is required.", file=sys.stderr)
        return 2

    try:
        overrides = _parse_input_overrides(args.input, "--input")
        enrichment_overrides = _parse_input_overrides(args.enrichment, "--enrichment")
        registry = load_registry(args.sports_registry, args.competitions_registry)
        coverage_families = load_coverage_families(args.coverage, registry)
        sources = load_sources(args.sources, registry)
        event_reviews = load_event_reviews(args.event_reviews)
        existing_manifest, existing_entries = _read_existing_manifest(args.manifest)
        seed_events, seed_evidence, superseded_event_ids = load_catalog_seeds(args.seeds, registry)
    except (RegistryError, ValueError, OSError, json.JSONDecodeError) as error:
        print(f"Refresh configuration error: {error}", file=sys.stderr)
        return 2

    source_rows = ()
    if not args.input or args.fetch_sources or args.offline:
        fetched = refresh_sources(sources, years, seed_events, seed_evidence, args.source_cache, offline=args.offline, save=not args.dry_run)
        seed_events, seed_evidence, source_rows = fetched.events, fetched.evidence, fetched.rows
        if fetched.blockers:
            report = {"source_checks": source_rows, "blockers": fetched.blockers}
            _save_report(args.report, report)
            print(json.dumps(report, ensure_ascii=False))
            return 1


    candidates: list[ReleaseCandidate] = []
    requested_ids = {str(year) for year in years}
    for year in years:
        path = _candidate_path(year, args.input_dir, overrides)
        if not path.exists() and not args.input:
            active = next((entry for entry in existing_entries if str(entry.get("id")) == str(year)), None)
            if active:
                path = args.manifest.parent / str(active["file"])
        if not path.exists():
            print(f"Missing candidate for {year}: {path}", file=sys.stderr)
            _save_failure_report(args.report, source_rows, year, f"Missing candidate: {path}")
            return 1
        read_result = read_catalog_tsv(path, allow_legacy=True)
        enrichment_path = _enrichment_path(year, args.enrichment_dir, enrichment_overrides)
        evidence: dict[str, object] = {}
        source_summary = None
        active_entry = next((entry for entry in existing_entries if str(entry.get("id")) == str(year)), None)
        active_file = args.manifest.parent / str(active_entry.get("file", "")) if active_entry else None
        if active_entry and active_file and path.resolve() == active_file.resolve():
            source_summary = str(active_entry.get("source_summary") or "") or None
            evidence_file = args.manifest.parent / str(active_entry.get("evidence", ""))
            if evidence_file.is_file():
                try:
                    active_evidence = json.loads(evidence_file.read_text(encoding="utf-8")).get("event_evidence", {})
                except (OSError, json.JSONDecodeError) as error:
                    print(f"Could not preserve active evidence for {year}: {error}", file=sys.stderr)
                    _save_failure_report(args.report, source_rows, year, f"Could not read active evidence: {error}")
                    return 1
                if isinstance(active_evidence, dict):
                    evidence.update(active_evidence)
        if not read_result.is_published and enrichment_path.exists():
            enrichment = enrich_catalog_file(path, enrichment_path, registry)
            if not enrichment.valid:
                print(f"Candidate enrichment rejected for {year}: {enrichment_path}", file=sys.stderr)
                for issue in enrichment.issues:
                    location = f" line {issue.row}" if issue.row else ""
                    print(f"  ERROR{location} {issue.code}: {issue.message}", file=sys.stderr)
                _save_failure_report(args.report, source_rows, year, "; ".join(issue.message for issue in enrichment.issues))
                return 1
            result = validate_events(
                tuple(event for event in enrichment.events if event.event_id not in superseded_event_ids),
                path=path,
                catalog_year=year,
                registry=registry,
                require_published=True,
            )
            evidence = enrichment.evidence
            source_summary = "Reviewed local enrichment records; source checks are recorded per event."
        elif args.bootstrap_legacy and not read_result.is_published:
            try:
                promoted = promote_legacy_catalog(read_result, catalog_year=year, registry=registry)
            except ValueError as error:
                print(f"Candidate rejected for {year}: {path}: {error}", file=sys.stderr)
                _save_failure_report(args.report, source_rows, year, str(error))
                return 1
            result = validate_events(
                tuple(event for event in promoted if event.event_id not in superseded_event_ids),
                path=path,
                catalog_year=year,
                registry=registry,
                require_published=True,
            )
            evidence = {
                event.event_id: [
                    {
                        "source_id": path.stem,
                        "source_path": path.as_posix(),
                        "source_row": event.source_row,
                        "date_decision": "legacy_bootstrap",
                    }
                ]
                for event in promoted
            }
            source_summary = "Legacy import; source dates and country coverage are not verified."
        else:
            result = validate_catalog_file(
                path,
                catalog_year=year,
                registry=registry,
                require_published=True,
                excluded_event_ids=superseded_event_ids,
            )
        merged_events = {
            event.event_id: event
            for event in result.events
            if event.event_id not in superseded_event_ids
        }
        if result.issues:
            print(f"Candidate {year} failed validation: " + "; ".join(issue.message for issue in result.issues), file=sys.stderr)
            _save_failure_report(args.report, source_rows, year, "; ".join(issue.message for issue in result.issues))
            return 1
        for event_id in superseded_event_ids:
            evidence.pop(event_id, None)
        for seed_event in seed_events:
            if seed_event.start_date < date(year + 1, 1, 1) and seed_event.end_date_exclusive > date(year, 1, 1):
                existing_event = merged_events.get(seed_event.event_id)
                existing_records = evidence.get(seed_event.event_id, [])
                new_records = seed_evidence[seed_event.event_id]
                previous_sources = {item.get("source_id") for item in existing_records if isinstance(item, dict) and item.get("date_decision") == "verified"}
                new_sources = {item.get("source_id") for item in new_records if isinstance(item, dict)}
                if existing_event is not None and existing_event.exact_values() != seed_event.exact_values() and previous_sources and not previous_sources & new_sources:
                    print(f"Catalog seed conflicts with {seed_event.event_id} in {year}.", file=sys.stderr)
                    _save_failure_report(args.report, source_rows, year, f"Seed conflicts with {seed_event.event_id}.")
                    return 1
                merged_events[seed_event.event_id] = seed_event
                evidence[seed_event.event_id] = seed_evidence[seed_event.event_id]
        result = validate_events(
            classify_audience(apply_event_reviews(tuple(merged_events.values()), evidence, event_reviews), evidence),
            path=path,
            catalog_year=year,
            registry=registry,
            require_published=True,
        )
        if not result.valid:
            print(f"Candidate rejected for {year}: {path}", file=sys.stderr)
            for issue in result.issues:
                location = f" line {issue.row}" if issue.row else ""
                print(f"  ERROR{location} {issue.code}: {issue.message}", file=sys.stderr)
            _save_failure_report(args.report, source_rows, year, "; ".join(issue.message for issue in result.issues))
            return 1
        status = "preview" if year in set(args.preview_years) or (not args.input and active_entry and active_entry.get("status") == "preview") else "ready"
        candidates.append(ReleaseCandidate(year, path, result, status, evidence, source_summary))
        print(f"Candidate accepted: {year} rows={result.summary['stored_rows']} status={status}")

    try:
        candidates = _project_overlapping_years(candidates, registry)
    except ValueError as error:
        print(f"Cross-year projection rejected: {error}", file=sys.stderr)
        _save_failure_report(args.report, source_rows, None, str(error))
        return 1

    blocked = False
    report = {"source_checks": source_rows, "catalogs": [], "blockers": []}
    for candidate in candidates:
        coverage = build_coverage_report(candidate.validation.events, candidate.evidence or {}, candidate.year, coverage_families, sources)
        active = next((entry for entry in existing_entries if str(entry.get("id")) == str(candidate.year)), None)
        previous = read_catalog_tsv(args.manifest.parent / str(active["file"])).events if active else ()
        changes = compare_catalogs(previous, candidate.validation.events, superseded_event_ids | frozenset(event_reviews))
        report["catalogs"].append({"catalog_year": candidate.year, "summary": candidate.validation.summary, "by_source": _source_summary(candidate.validation.events, candidate.evidence or {}), "coverage": coverage, "changes": changes})
        conflicts = [event.event_id for event in candidate.validation.events if conflicting_date_records(event, (candidate.evidence or {}).get(event.event_id), sources)]
        if conflicts:
            blocked = True
            report["blockers"].append(f"Official date evidence conflicts in {candidate.year}: {', '.join(conflicts)}")
        required_ids = {row["expected_event_id"] for row in coverage["rows"] if row["required"]}
        missing_required = [change for change in changes if change["status"] == "missing" and change["event_id"] in required_ids]
        if missing_required:
            blocked = True
            report["blockers"].append(f"Established required events disappeared from {candidate.year} without explanation.")
        if candidate.status == "ready" and (coverage["pending_count"] or coverage["unresolved_audience_count"]):
            blocked = True
            report["blockers"].append(f"Catalog {candidate.year} has pending required highlights or audience reviews.")
            print(f"Candidate {candidate.year} cannot be Ready: {coverage['pending_count']} required highlights pending; {coverage['unresolved_audience_count']} events need audience review.", file=sys.stderr)
    _save_report(args.report, report)
    print(json.dumps(report, ensure_ascii=False))
    if blocked:
        return 1

    preserved_entries = tuple(entry for entry in existing_entries if str(entry.get("id")) not in requested_ids)
    default_id = args.default_id or str(existing_manifest.get("default", ""))
    if not default_id:
        default_id = str(years[0])
    all_ids = requested_ids | {str(entry.get("id")) for entry in preserved_entries}
    if default_id not in all_ids:
        print(f"Default catalog {default_id!r} is not in the release batch.", file=sys.stderr)
        return 2

    try:
        revision, manifest = write_release_batch(
            tuple(candidates),
            manifest_path=args.manifest,
            release_root=args.release_root,
            registry_paths=(args.sports_registry, args.competitions_registry, args.coverage, args.sources, args.event_reviews),
            coverage_families=coverage_families,
            sources=sources,
            default_id=default_id,
            dry_run=args.dry_run,
            preserved_entries=preserved_entries,
        )
    except (OSError, ValueError) as error:
        report["blockers"].append(str(error))
        _save_report(args.report, report)
        print(f"Release failed without replacing the manifest: {error}", file=sys.stderr)
        return 1

    print(f"Revision: {revision}")
    print("Dry run: active catalog files unchanged." if args.dry_run else f"Updated local manifest: {args.manifest}")
    print(f"Active catalogs: {', '.join(str(entry['id']) for entry in manifest['catalogs'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
