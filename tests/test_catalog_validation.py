from __future__ import annotations

from datetime import date
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from sportkalender.catalog_ids import stable_event_id
from sportkalender.catalog_model import CatalogEvent
from sportkalender.catalog_registry import load_registry
from sportkalender.catalog_tsv import write_catalog_tsv
from sportkalender.catalog_validation import validate_catalog_file, validate_events, validate_ready_events
from catalog_fixtures import highlight, reviewed_evidence


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = load_registry(ROOT / "data/sports.json", ROOT / "data/competitions.json")


def event(*, start: date = date(2026, 9, 1), end: date = date(2026, 9, 2), event_id: str | None = None) -> CatalogEvent:
    return CatalogEvent(
        event_id=event_id
        or stable_event_id(competition_key="nfl", season="2026", event_kind="season", stage="season_opener"),
        start_date=start,
        end_date_exclusive=end,
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


class CatalogValidationTests(unittest.TestCase):
    def test_final_tournament_retains_full_dates_as_one_event(self):
        final = highlight("final_tournament", start="2026-05-01", end="2026-05-20")
        result = validate_events((final,), catalog_year=2026, registry=REGISTRY)
        self.assertTrue(result.valid)
        self.assertEqual(result.summary["unique_event_ids"], 1)
        self.assertEqual(result.events[0].inclusive_end_date, date(2026, 5, 20))

    def test_playoff_league_cannot_use_routine_final_matchday(self):
        invalid = highlight("final_matchday", competition_key="nfl", sport_key="american_football", sport="American Football")
        result = validate_events((invalid,), catalog_year=2026, registry=REGISTRY)
        self.assertIn("regular_season_closing", {issue.code for issue in result.issues})

    def test_ready_requires_reviewed_audience_even_when_dates_pass(self):
        candidate = highlight()
        self.assertTrue(validate_ready_events((candidate,), {}))
        self.assertEqual(validate_ready_events((candidate,), {candidate.event_id: reviewed_evidence(candidate)}), ())
        international = highlight(coverage="shared_major", audience_countries=())
        self.assertTrue(validate_ready_events((international,), {}))
        self.assertEqual(validate_ready_events((international,), {international.event_id: reviewed_evidence(international)}), ())

    def test_reversed_range_is_rejected_from_catalog(self) -> None:
        invalid = event(start=date(2026, 9, 9), end=date(2026, 1, 11))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.tsv"
            write_catalog_tsv([invalid], path)
            result = validate_catalog_file(path, catalog_year=2026, registry=REGISTRY)

        self.assertFalse(result.valid)
        self.assertIn("reversed_date_range", {issue.code for issue in result.issues})

    def test_season_ranges_must_be_short_highlights(self) -> None:
        invalid = event(start=date(2026, 1, 1), end=date(2026, 1, 16))

        result = validate_events((invalid,), catalog_year=2026, registry=REGISTRY)

        self.assertFalse(result.valid)
        self.assertIn("season_range_too_long", {issue.code for issue in result.issues})

    def test_unknown_registry_keys_are_rejected(self) -> None:
        invalid = replace(event(), sport_key="unknown_sport")
        result = validate_events((invalid,), catalog_year=2026, registry=REGISTRY)

        self.assertFalse(result.valid)
        self.assertIn("unknown_sport_key", {issue.code for issue in result.issues})

    def test_duplicate_ids_are_rejected(self) -> None:
        first = event()
        second = event(start=date(2026, 9, 3), end=date(2026, 9, 4))
        result = validate_events((first, second), catalog_year=2026, registry=REGISTRY)

        self.assertFalse(result.valid)
        self.assertIn("duplicate_event_id", {issue.code for issue in result.issues})

    def test_catalog_year_requires_overlap(self) -> None:
        outside = event(start=date(2025, 1, 1), end=date(2025, 1, 2))
        result = validate_events((outside,), catalog_year=2026, registry=REGISTRY)

        self.assertFalse(result.valid)
        self.assertIn("outside_catalog_year", {issue.code for issue in result.issues})


if __name__ == "__main__":
    unittest.main()
