from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sportkalender.catalog_registry import RegistryError, load_registry
from sportkalender.catalog_validation import validate_catalog_file, validate_manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate published Sportkalender catalog files.")
    parser.add_argument("paths", nargs="*", type=Path, help="Catalog TSV files to validate.")
    parser.add_argument("--manifest", type=Path, help="Validate every catalog referenced by a manifest.")
    parser.add_argument("--catalog-year", type=int, help="Expected year for a single catalog file.")
    parser.add_argument("--sports-registry", type=Path, default=Path("data/sports.json"))
    parser.add_argument("--competitions-registry", type=Path, default=Path("data/competitions.json"))
    parser.add_argument("--json", action="store_true", help="Print machine-readable output.")
    return parser


def _load_registry(args: argparse.Namespace):
    try:
        return load_registry(args.sports_registry, args.competitions_registry)
    except RegistryError as error:
        print(f"Registry error: {error}", file=sys.stderr)
        return None


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if bool(args.manifest) == bool(args.paths):
        print("Provide exactly one of --manifest or one or more catalog paths.", file=sys.stderr)
        return 2

    registry = _load_registry(args)
    if registry is None:
        return 2

    if args.manifest:
        manifest, issues = validate_manifest(args.manifest, registry)
        if args.json:
            print(json.dumps({"manifest": manifest, "issues": [asdict(issue) for issue in issues]}, ensure_ascii=False, indent=2))
        else:
            for issue in issues:
                print(f"ERROR {issue.code}: {issue.message}")
            print("Manifest valid." if not issues else f"Manifest invalid: {len(issues)} issue(s).")
        return 0 if not issues else 1

    results = [
        validate_catalog_file(path, catalog_year=args.catalog_year, registry=registry, require_published=True)
        for path in args.paths
    ]
    issues = [issue for result in results for issue in result.issues]
    if args.json:
        payload = {
            "catalogs": [
                {"path": str(result.path), "valid": result.valid, "summary": result.summary, "issues": [asdict(issue) for issue in result.issues]}
                for result in results
            ]
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for result in results:
            print(f"{result.path}: {'valid' if result.valid else 'invalid'}")
            for issue in result.issues:
                location = f" line {issue.row}" if issue.row else ""
                print(f"  ERROR{location} {issue.code}: {issue.message}")
            if result.valid:
                print(f"  rows={result.summary['stored_rows']} ids={result.summary['unique_event_ids']}")
        print("Catalogs valid." if not issues else f"Catalogs invalid: {len(issues)} issue(s).")
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
