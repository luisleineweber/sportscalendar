from __future__ import annotations

from dataclasses import replace
from datetime import date
from pathlib import Path
import json
import tempfile
import unittest

from scripts.refresh_catalogs import main as refresh_main
from scripts.validate_catalog import main as validate_main
from sportkalender.catalog_ids import stable_event_id
from sportkalender.catalog_model import CatalogEvent
from sportkalender.catalog_tsv import read_catalog_tsv, write_catalog_tsv
from sportkalender.catalog_validation import validate_manifest


ROOT = Path(__file__).resolve().parents[1]
SPORTS_REGISTRY = ROOT / "data/sports.json"
COMPETITIONS_REGISTRY = ROOT / "data/competitions.json"


def season_event(start_date: date, end_date_exclusive: date) -> CatalogEvent:
    return CatalogEvent(
        event_id=stable_event_id(competition_key="nfl", season="2026", event_kind="season", stage="season_opener"),
        start_date=start_date,
        end_date_exclusive=end_date_exclusive,
        title="NFL season 2026",
        sport="American Football",
        location="USA",
        competition_key="nfl",
        season="2026",
        sport_key="american_football",
        coverage="national",
        audience_countries=("US",),
        event_kind="season",
        stage="season_opener",
    )


class CatalogRefreshTests(unittest.TestCase):
    def _args(self, manifest: Path, release_root: Path, candidate_2026: Path, candidate_2027: Path, *extra: str) -> list[str]:
        seeds = manifest.parent / "catalog-seeds.json"
        seeds.write_text('{"schema_version": 1, "events": []}\n', encoding="utf-8")
        return [
            "--years",
            "2026",
            "2027",
            "--input",
            f"2026={candidate_2026}",
            "--input",
            f"2027={candidate_2027}",
            "--manifest",
            str(manifest),
            "--release-root",
            str(release_root),
            "--sports-registry",
            str(SPORTS_REGISTRY),
            "--competitions-registry",
            str(COMPETITIONS_REGISTRY),
            "--seeds",
            str(seeds),
            "--preview-years",
            "2026",
            "2027",
            *extra,
        ]

    def test_dry_run_does_not_create_manifest(self) -> None:
        event = season_event(date(2026, 12, 31), date(2027, 1, 2))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_2026 = root / "2026.tsv"
            candidate_2027 = root / "2027.tsv"
            write_catalog_tsv([event], candidate_2026)
            write_catalog_tsv([event], candidate_2027)
            manifest = root / "catalogs.json"

            result = refresh_main(self._args(manifest, root / "releases", candidate_2026, candidate_2027, "--dry-run"))

            self.assertEqual(result, 0)
            self.assertFalse(manifest.exists())

    def test_release_writes_manifest_and_cross_year_catalogs(self) -> None:
        event = season_event(date(2026, 12, 31), date(2027, 1, 2))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_2026 = root / "2026.tsv"
            candidate_2027 = root / "2027.tsv"
            write_catalog_tsv([event], candidate_2026)
            write_catalog_tsv([event], candidate_2027)
            manifest = root / "catalogs.json"
            release_root = root / "releases"

            result = refresh_main(self._args(manifest, release_root, candidate_2026, candidate_2027))

            self.assertEqual(result, 0)
            manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(manifest_value["default"], "2026")
            self.assertEqual([entry["status"] for entry in manifest_value["catalogs"]], ["preview", "preview"])
            _, issues = validate_manifest(manifest)
            self.assertEqual(issues, ())
            self.assertEqual(
                validate_main(
                    [
                        "--manifest",
                        str(manifest),
                        "--sports-registry",
                        str(SPORTS_REGISTRY),
                        "--competitions-registry",
                        str(COMPETITIONS_REGISTRY),
                    ]
                ),
                0,
            )
            self.assertTrue(list(release_root.rglob("catalog_2026.tsv")))

    def test_cross_year_event_is_projected_into_next_catalog(self) -> None:
        overlapping = season_event(date(2026, 12, 31), date(2027, 1, 2))
        next_season = replace(
            season_event(date(2027, 9, 1), date(2027, 9, 2)),
            event_id=stable_event_id(competition_key="nfl", season="2027", event_kind="season", stage="season_opener"),
            season="2027",
            title="NFL season 2027",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_2026 = root / "2026.tsv"
            candidate_2027 = root / "2027.tsv"
            write_catalog_tsv([overlapping], candidate_2026)
            write_catalog_tsv([next_season], candidate_2027)
            manifest = root / "catalogs.json"

            self.assertEqual(refresh_main(self._args(manifest, root / "releases", candidate_2026, candidate_2027)), 0)
            published = json.loads(manifest.read_text(encoding="utf-8"))
            entry_2027 = next(entry for entry in published["catalogs"] if entry["id"] == "2027")
            self.assertEqual(entry_2027["event_count"], 2)

    def test_seed_replaces_a_season_range_with_a_point_highlight(self) -> None:
        old_event = season_event(date(2026, 8, 28), date(2027, 5, 23))
        highlight_id = stable_event_id(
            competition_key="nfl",
            season="2026",
            event_kind="season",
            gender="mixed",
            stage="season_opener",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_2026 = root / "2026.tsv"
            candidate_2027 = root / "2027.tsv"
            write_catalog_tsv([old_event], candidate_2026)
            write_catalog_tsv([], candidate_2027)
            seed_path = root / "seeds.json"
            seed_path.write_text(json.dumps({
                "schema_version": 1,
                "events": [{
                    "competition_key": "nfl",
                    "season": "2026",
                    "event_kind": "season",
                    "gender": "mixed",
                    "stage": "season_opener",
                    "title": "NFL season opener",
                    "start_date": "2026-09-10",
                    "end_date": "2026-09-10",
                    "source_id": "nfl_opener_test",
                    "source_url": "https://example.test/nfl",
                    "date_checked_at": "2026-09-25",
                    "supersedes": [old_event.event_id],
                }],
            }), encoding="utf-8")
            manifest = root / "catalogs.json"

            result = refresh_main(self._args(
                manifest,
                root / "releases",
                candidate_2026,
                candidate_2027,
                "--seeds",
                str(seed_path),
            ))

            self.assertEqual(result, 0)
            published = json.loads(manifest.read_text(encoding="utf-8"))
            entry_2026 = next(entry for entry in published["catalogs"] if entry["id"] == "2026")
            catalog = read_catalog_tsv(manifest.parent / entry_2026["file"])
            self.assertEqual([event.event_id for event in catalog.events], [highlight_id])
            self.assertEqual(catalog.events[0].inclusive_end_date, catalog.events[0].start_date)
            self.assertEqual(validate_manifest(manifest)[1], ())

    def test_retired_event_ids_remove_season_ranges_from_each_year(self) -> None:
        old_event = season_event(date(2026, 9, 1), date(2027, 1, 11))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_2026 = root / "2026.tsv"
            candidate_2027 = root / "2027.tsv"
            write_catalog_tsv([old_event], candidate_2026)
            write_catalog_tsv([old_event], candidate_2027)
            seed_path = root / "seeds.json"
            seed_path.write_text(json.dumps({
                "schema_version": 1,
                "events": [],
                "retired_event_ids": [old_event.event_id],
            }), encoding="utf-8")
            manifest = root / "catalogs.json"

            result = refresh_main(self._args(
                manifest,
                root / "releases",
                candidate_2026,
                candidate_2027,
                "--seeds",
                str(seed_path),
            ))

            self.assertEqual(result, 0)
            published = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual([entry["event_count"] for entry in published["catalogs"]], [0, 0])

    def test_ready_catalog_with_pending_coverage_is_rejected(self) -> None:
        event = season_event(date(2026, 9, 1), date(2026, 9, 2))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_2026 = root / "2026.tsv"
            candidate_2027 = root / "2027.tsv"
            write_catalog_tsv([event], candidate_2026)
            write_catalog_tsv([replace(
                event,
                start_date=date(2027, 9, 1),
                end_date_exclusive=date(2027, 9, 2),
                event_id=stable_event_id(competition_key="nfl", season="2027", event_kind="season", stage="season_opener"),
                season="2027",
            )], candidate_2027)
            manifest = root / "catalogs.json"

            self.assertEqual(
                refresh_main(self._args(manifest, root / "releases", candidate_2026, candidate_2027, "--preview-years")),
                1,
            )
            self.assertFalse(manifest.exists())

    def test_invalid_candidate_keeps_existing_manifest_unchanged(self) -> None:
        valid = season_event(date(2026, 12, 31), date(2027, 1, 2))
        invalid = season_event(date(2027, 9, 9), date(2027, 1, 11))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate_2026 = root / "2026.tsv"
            candidate_2027 = root / "2027.tsv"
            write_catalog_tsv([valid], candidate_2026)
            write_catalog_tsv([valid], candidate_2027)
            manifest = root / "catalogs.json"
            release_root = root / "releases"
            self.assertEqual(refresh_main(self._args(manifest, release_root, candidate_2026, candidate_2027)), 0)
            previous_manifest = manifest.read_text(encoding="utf-8")

            write_catalog_tsv([invalid], candidate_2027)
            result = refresh_main(self._args(manifest, release_root, candidate_2026, candidate_2027))

            self.assertEqual(result, 1)
            self.assertEqual(manifest.read_text(encoding="utf-8"), previous_manifest)

    def test_legacy_candidate_uses_reviewed_enrichment_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = root / "2026.tsv"
            candidate.write_text("1.9.2026\tNFL season 2026\tAmerican Football\tUSA\n", encoding="utf-8")
            enrichment = root / "2026.json"
            enrichment.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "rows": {
                            "1": {
                                "competition_key": "nfl",
                                "season": "2026",
                                "coverage": "national",
                                "event_kind": "season",
                                "stage": "season_opener",
                                "evidence": [{"source_id": "nfl-calendar", "source_url": "https://example.test/nfl"}],
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            manifest = root / "catalogs.json"
            result = refresh_main(
                [
                    "--years",
                    "2026",
                    "--input",
                    f"2026={candidate}",
                    "--enrichment",
                    f"2026={enrichment}",
                    "--manifest",
                    str(manifest),
                    "--release-root",
                    str(root / "releases"),
                    "--sports-registry",
                    str(SPORTS_REGISTRY),
                    "--competitions-registry",
                    str(COMPETITIONS_REGISTRY),
                    "--preview-years",
                    "2026",
                ]
            )

            self.assertEqual(result, 0)
            manifest_value = json.loads(manifest.read_text(encoding="utf-8"))
            evidence_path = manifest.parent / manifest_value["catalogs"][0]["evidence"]
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            self.assertEqual(evidence["event_evidence"][next(iter(evidence["event_evidence"]))][0]["source_id"], "nfl-calendar")


if __name__ == "__main__":
    unittest.main()
