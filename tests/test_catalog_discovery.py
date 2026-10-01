from pathlib import Path
import unittest

from sportkalender.catalog_discovery import discover_wikipedia
from sportkalender.catalog_registry import load_registry
from sportkalender.catalog_source_refresh import refresh_sources
from sportkalender.catalog_sources import SourceSnapshot, load_sources

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = load_registry(ROOT / "data/sports.json", ROOT / "data/competitions.json")


class DiscoveryTests(unittest.TestCase):
    def source(self):
        return next(source for source in load_sources(ROOT / "data/sources.json", REGISTRY).values()
                    if source.adapter == "wikipedia" and source.language == "en")

    def test_saved_table_reports_dates_and_rejections_without_publishing(self):
        source = self.source()
        snapshot = SourceSnapshot(source.id, source.urls_by_year["2026"], (ROOT / "tests/fixtures/wikipedia_discovery.html").read_bytes())
        result = discover_wikipedia(source, snapshot, 2026)
        self.assertEqual(result["status"], "discovery")
        self.assertEqual(result["parsed_count"], 2)
        accepted, rejected = result["discovered_events"]
        self.assertEqual(accepted["date"], "9.9.2026 - 10.1.2027")
        self.assertEqual(accepted["status"], "pending_review")
        self.assertFalse(accepted["blocks_ready"])
        self.assertEqual(rejected["status"], "rejected")
        self.assertEqual(result["rejected_by_reason"], {"unparseable_date": 1})

    def test_empty_page_reports_parse_failure(self):
        source = self.source()
        for content in (b"<h1>No table</h1>", b"", b"\xff"):
            with self.subTest(content=content):
                result = discover_wikipedia(source, SourceSnapshot(source.id, source.urls_by_year["2026"], content), 2026)
                self.assertEqual(result["status"], "parse_failed")

    def test_refresh_checks_adjacent_source_years_and_keeps_discovery_unpublished(self):
        source = self.source()
        fetched = []
        def fetch(source, year, *args, **kwargs):
            fetched.append(year)
            return SourceSnapshot(source.id, source.urls_by_year[str(year)], (ROOT / "tests/fixtures/wikipedia_discovery.html").read_bytes(), "2026-10-01")
        result = refresh_sources({source.id: source}, [2026, 2027], (), {}, Path("unused"), fetch=fetch, pause=lambda seconds: None)
        self.assertEqual(fetched, [2025, 2026, 2027, 2028])
        self.assertEqual([row["source_year"] for row in result.rows], fetched)
        self.assertEqual(result.events, ())
        self.assertEqual(result.blockers, ())


if __name__ == "__main__":
    unittest.main()
