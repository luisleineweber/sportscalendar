from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from urllib.error import HTTPError
import tempfile
import unittest

from catalog_fixtures import highlight, official_source, reviewed_evidence
from sportkalender.catalog_registry import load_registry
from sportkalender.catalog_source_refresh import parse_official_highlights, refresh_sources
from sportkalender.catalog_sources import SourceSnapshot, fetch_snapshot, load_sources

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = load_registry(ROOT / "data/sports.json", ROOT / "data/competitions.json")


class SourceTests(unittest.TestCase):
    def test_official_saved_pages_produce_separate_highlights(self):
        sources = load_sources(ROOT / "data/sources.json", REGISTRY)
        for key, dates in [("premier_league_2026_27", ["2026-08-21", "2027-05-30"]),
                           ("ligue_1_2026_27", ["2026-08-21", "2027-05-29"])]:
            source = sources[key]
            snapshot = SourceSnapshot(key, source.urls_by_year["2026"], (ROOT / f"tests/fixtures/{key}.html").read_bytes(), "2026-10-01")
            result = parse_official_highlights(source, snapshot)
            self.assertEqual(result.blockers, ())
            self.assertEqual([e.start_date.isoformat() for e in result.events], dates)
            self.assertEqual([e.stage for e in result.events], ["season_opener", "final_matchday"])
            self.assertNotEqual(result.events[0].event_id, result.events[1].event_id)

    def test_http_success_without_expected_dates_is_a_source_failure(self):
        source = load_sources(ROOT / "data/sources.json", REGISTRY)["premier_league_2026_27"]
        snapshot = SourceSnapshot(source.id, source.urls_by_year["2026"], b"<h1>Schedule</h1>", "2026-10-01")
        result = parse_official_highlights(source, snapshot)
        self.assertTrue(result.blockers)
        self.assertEqual(result.events, ())

    def test_stale_season_does_not_pass(self):
        source = load_sources(ROOT / "data/sources.json", REGISTRY)["premier_league_2026_27"]
        content = (ROOT / "tests/fixtures/premier_league_2026_27.html").read_bytes().replace(b"2026", b"2024").replace(b"2027", b"2025")
        result = parse_official_highlights(source, SourceSnapshot(source.id, source.urls_by_year["2026"], content))
        self.assertTrue(result.blockers)

    def test_changed_reviewed_source_blocks_required_family(self):
        event = highlight()
        source = replace(official_source(), required_catalog_ids=("2026",))
        evidence = {event.event_id: reviewed_evidence(event)}
        def fetch(*args, **kwargs):
            return SourceSnapshot(source.id, source.urls_by_year["2026"], b"changed", "2026-10-01")
        result = refresh_sources({source.id: source}, [2026], (event,), evidence, Path("unused"), fetch=fetch)
        self.assertTrue(result.blockers)
        self.assertEqual(result.rows[0]["status"], "review_required")
        self.assertFalse(result.evidence[event.event_id][0]["source_current"])
        self.assertNotIn("source_current", evidence[event.event_id][0])

    def test_unchanged_review_keeps_its_actual_check_age(self):
        event = highlight()
        source = official_source()
        snapshot = SourceSnapshot(source.id, source.urls_by_year["2026"], b"unchanged", "2026-10-01")
        evidence = {event.event_id: reviewed_evidence(event)}
        evidence[event.event_id][0].update(source_hash=snapshot.content_hash, date_checked_at="2026-09-01")
        result = refresh_sources({source.id: source}, [2026], (event,), evidence, Path("unused"), fetch=lambda *args, **kwargs: snapshot)
        self.assertEqual(result.blockers, ())
        self.assertEqual(result.rows[0]["status"], "unchanged_reviewed")
        self.assertEqual(result.rows[0]["date_checked_at"], ["2026-09-01"])

    def test_optional_failure_is_reported_without_blocking(self):
        source = official_source()
        result = refresh_sources({source.id: source}, [2026], (), {}, Path("unused"),
                                 fetch=lambda *args, **kwargs: SourceSnapshot(source.id, "", error="HTTP 404"))
        self.assertEqual(result.blockers, ())
        self.assertEqual(result.rows[0]["status"], "fetch_failed")
        self.assertFalse(result.rows[0]["blocks_release"])

    def test_optional_year_failure_does_not_block_another_required_year(self):
        event = highlight()
        source = replace(official_source(), required_catalog_ids=("2026",), urls_by_year={"2026": "https://example.test/2026", "2027": "https://example.test/2027"})
        snapshot = SourceSnapshot(source.id, source.urls_by_year["2026"], b"unchanged", "2026-10-01")
        evidence = {event.event_id: reviewed_evidence(event)}
        evidence[event.event_id][0]["source_hash"] = snapshot.content_hash
        def fetch(source, year, *args, **kwargs):
            return snapshot if year == 2026 else SourceSnapshot(source.id, source.urls_by_year["2027"], error="HTTP 404")
        result = refresh_sources({source.id: source}, [2026, 2027], (event,), evidence, Path("unused"), fetch=fetch, pause=lambda seconds: None)
        self.assertEqual(result.blockers, ())
        self.assertFalse(result.rows[1]["blocks_release"])

    def test_304_without_cache_cannot_succeed(self):
        source = official_source()
        def not_modified(request, **kwargs):
            raise HTTPError(request.full_url, 304, "Not Modified", {}, None)
        with tempfile.TemporaryDirectory() as directory:
            result = fetch_snapshot(source, 2026, Path(directory), opener=not_modified)
        self.assertIn("no matching saved response", result.error)

    def test_matching_cached_response_supports_304_and_offline(self):
        source = official_source()
        class Response:
            headers = {"ETag": "test-etag"}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return b"saved page"
        def not_modified(request, **kwargs):
            self.assertEqual(request.get_header("If-none-match"), "test-etag")
            raise HTTPError(request.full_url, 304, "Not Modified", {}, None)
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            first = fetch_snapshot(source, 2026, cache, opener=lambda *args, **kwargs: Response())
            cached = fetch_snapshot(source, 2026, cache, opener=not_modified)
            offline = fetch_snapshot(source, 2026, cache, offline=True)
            self.assertEqual(first.content, cached.content)
            self.assertEqual(offline.content_hash, first.content_hash)

    def test_dry_source_fetch_does_not_write_files(self):
        source = official_source()
        class Response:
            headers = {}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return b"saved page"
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / "cache"
            result = fetch_snapshot(source, 2026, cache, save=False, opener=lambda *args, **kwargs: Response())
            self.assertFalse(cache.exists())
            self.assertFalse(result.error)


if __name__ == "__main__":
    unittest.main()
