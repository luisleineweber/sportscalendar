from __future__ import annotations

from datetime import date
from pathlib import Path
import tempfile
import unittest

from sportkalender.catalog_ids import custom_event_id, stable_event_id
from sportkalender.catalog_model import CatalogEvent
from sportkalender.catalog_registry import load_registry
from sportkalender.catalog_tsv import read_catalog_tsv, write_catalog_tsv
from sportkalender.core import SportEvent, load_events_from_tsv, write_ics


ROOT = Path(__file__).resolve().parents[1]


def published_event(
    *,
    start_date: date = date(2026, 9, 1),
    end_date_exclusive: date = date(2026, 9, 2),
    location: str = "New York",
) -> CatalogEvent:
    event_id = stable_event_id(
        competition_key="nba",
        season="2026-27",
        event_kind="season",
        gender="mixed",
        stage="season_opener",
    )
    return CatalogEvent(
        event_id=event_id,
        start_date=start_date,
        end_date_exclusive=end_date_exclusive,
        title="NBA season 2026-27",
        sport="Basketball",
        location=location,
        competition_key="nba",
        season="2026-27",
        sport_key="basketball",
        coverage="national",
        audience_countries=("US",),
        event_kind="season",
        gender="mixed",
        stage="season_opener",
    )


class CatalogDataTests(unittest.TestCase):
    def test_header_order_does_not_turn_metadata_into_location(self) -> None:
        event = published_event()
        row = {
            "event_id": event.event_id,
            "Datum": "1.9.2026",
            "Ereignis": event.title,
            "Sportart": event.sport,
            "Ort": event.location,
            "competition_key": event.competition_key,
            "season": event.season,
            "stage": event.stage,
            "sport_key": event.sport_key,
            "coverage": event.coverage,
            "audience_countries": "US",
            "event_kind": event.event_kind,
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.tsv"
            headers = list(row)
            path.write_text(
                "\t".join(headers) + "\n" + "\t".join(row[header] for header in headers) + "\n",
                encoding="utf-8",
            )
            result = read_catalog_tsv(path)

        self.assertTrue(result.valid)
        self.assertTrue(result.is_published)
        self.assertEqual(result.events[0].location, "New York")
        self.assertEqual(result.events[0].competition_key, "nba")

    def test_legacy_rows_get_content_based_custom_ids(self) -> None:
        content = "1.9.2026\tEvent\tBasketball\tNew York\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy.tsv"
            path.write_text(content, encoding="utf-8")
            first = read_catalog_tsv(path)
            second = read_catalog_tsv(path)

        self.assertTrue(first.valid)
        self.assertFalse(first.is_published)
        self.assertEqual(first.events[0].event_id, second.events[0].event_id)
        self.assertTrue(first.events[0].event_id.startswith("custom:"))
        self.assertEqual(
            first.events[0].event_id,
            custom_event_id(
                start_date="2026-09-01",
                end_date_exclusive="2026-09-02",
                title="Event",
                sport="Basketball",
                location="New York",
            ),
        )

    def test_writer_round_trips_published_metadata(self) -> None:
        event = published_event()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.tsv"
            write_catalog_tsv([event], path)
            result = read_catalog_tsv(path)

        self.assertTrue(result.valid)
        self.assertEqual(result.events, (event,))

    def test_custom_id_matches_browser_fixture(self) -> None:
        self.assertEqual(
            custom_event_id(
                start_date="2026-09-01",
                end_date_exclusive="2026-09-02",
                title="Final 🎾",
                sport="Tennis",
                location="München, DE",
            ),
            "custom:1161e51ae494c4f3",
        )

    def test_registry_contains_expected_named_competitions(self) -> None:
        registry = load_registry(ROOT / "data/sports.json", ROOT / "data/competitions.json")

        self.assertEqual(registry.competitions["nfl"].sport_key, "american_football")
        self.assertEqual(registry.competitions["uefa_champions_league"].primary_display_group, "International")

    def test_date_or_location_correction_keeps_published_id(self) -> None:
        original = published_event()
        corrected = published_event(start_date=date(2026, 9, 2), end_date_exclusive=date(2026, 9, 3), location="Boston")

        self.assertEqual(original.event_id, corrected.event_id)

    def test_python_ics_uses_catalog_event_id(self) -> None:
        event = published_event()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "catalog.tsv"
            output_path = root / "events.ics"
            write_catalog_tsv([event], catalog_path)
            write_ics(load_events_from_tsv(catalog_path), output_path)
            ics_text = output_path.read_bytes().decode("utf-8")

        unfolded_ics = ics_text.replace("\r\n ", "")
        self.assertIn(f"UID:{event.event_id}@sportkalender", unfolded_ics)

    def test_python_ics_sorts_ids_and_folds_unicode_by_bytes(self) -> None:
        first_id = f"event-{'a' * 64}"
        second_id = f"event-{'b' * 64}"
        entries = [
            SportEvent(date(2026, 1, 1), date(2026, 1, 2), "Final 🎾 " * 12, "Tennis", "München, DE " * 8, second_id),
            SportEvent(date(2026, 1, 1), date(2026, 1, 2), "Überraschung", "Tennis", "", first_id),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.ics"
            write_ics(entries, path)
            first = path.read_bytes()
            write_ics(entries, path)
            self.assertEqual(path.read_bytes(), first)

        self.assertLess(first.index(first_id.encode()), first.index(second_id.encode()))
        self.assertTrue(all(len(line) <= 75 for line in first.split(b"\r\n")))


if __name__ == "__main__":
    unittest.main()
