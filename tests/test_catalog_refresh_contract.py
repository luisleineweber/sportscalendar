from contextlib import redirect_stdout, redirect_stderr
from dataclasses import asdict
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from catalog_fixtures import highlight, official_source, requirement
from scripts.refresh_catalogs import main
from sportkalender.catalog_source_refresh import SourceRefreshResult
from sportkalender.catalog_tsv import write_catalog_tsv

ROOT = Path(__file__).resolve().parents[1]


class RefreshContractTests(unittest.TestCase):
    def configure(self, root, required=False):
        opener = highlight()
        closing = highlight("final_matchday", start="2027-05-22")
        extra = highlight("all_star")
        coverage = {"schema_version": 2, "goals": [{"country": "FR", "sport_key": "basketball"}],
                    "highlights": [requirement(opener, required=required), requirement(closing, required=required), requirement(extra, required=False)]}
        (root / "coverage.json").write_text(json.dumps(coverage))
        (root / "sources.json").write_text(json.dumps({"schema_version": 1, "sources": [asdict(official_source())]}))
        seeds = []
        for event in [opener, closing]:
            seeds.append({"competition_key": event.competition_key, "season": event.season,
                          "event_kind": event.event_kind, "gender": event.gender, "stage": event.stage,
                          "title": event.title, "start_date": event.start_date.isoformat(),
                          "end_date": event.inclusive_end_date.isoformat(), "source_id": "organizer",
                          "source_url": "https://example.test/schedule", "date_checked_at": "2026-10-01",
                          "date_statement": "The organizer confirms the highlight date.",
                          "coverage": "national", "audience_countries": ["DE"],
                          "audience_statement": "This is a German domestic league."})
        (root / "seeds.json").write_text(json.dumps({"schema_version": 1, "events": seeds}))
        write_catalog_tsv([], root / "2026.tsv")
        write_catalog_tsv([], root / "2027.tsv")
        return ["--years", "2026", "2027", "--input", f"2026={root / '2026.tsv'}",
                "--input", f"2027={root / '2027.tsv'}", "--manifest", str(root / "catalogs.json"),
                "--release-root", str(root / "releases"), "--coverage", str(root / "coverage.json"),
                "--sources", str(root / "sources.json"), "--seeds", str(root / "seeds.json"),
                "--sports-registry", str(ROOT / "data/sports.json"),
                "--competitions-registry", str(ROOT / "data/competitions.json"),
                "--report", str(root / "report.json")]

    def run_refresh(self, args):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return main(args)

    def test_ready_ignores_optional_absence_and_goal_gap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(self.run_refresh(self.configure(root, required=True)), 0)
            manifest = json.loads((root / "catalogs.json").read_text())
            self.assertEqual([entry["status"] for entry in manifest["catalogs"]], ["ready", "ready"])
            report = json.loads((root / "report.json").read_text())
            self.assertEqual(report["catalogs"][0]["coverage"]["pending_count"], 0)
            self.assertEqual(report["catalogs"][0]["coverage"]["optional_pending_count"], 1)
            self.assertEqual(report["catalogs"][0]["by_source"]["organizer"]["stored_rows"], 1)
            self.assertEqual(report["catalogs"][0]["by_source"]["organizer"]["by_sport"], {"football": 1})

    def test_required_source_failure_keeps_active_files_and_reports_reason(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.configure(root, required=True)
            self.assertEqual(self.run_refresh(args), 0)
            before = (root / "catalogs.json").read_bytes()
            with patch("scripts.refresh_catalogs.refresh_sources", return_value=SourceRefreshResult((), {}, (), ("Organizer source failed.",))):
                self.assertEqual(self.run_refresh([*args, "--fetch-sources"]), 1)
            self.assertEqual((root / "catalogs.json").read_bytes(), before)
            self.assertEqual(json.loads((root / "report.json").read_text())["blockers"], ["Organizer source failed."])

    def test_disappearing_required_event_blocks_even_a_preview_update(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.configure(root, required=True)
            self.assertEqual(self.run_refresh(args), 0)
            before = (root / "catalogs.json").read_bytes()
            (root / "seeds.json").write_text('{"schema_version": 1, "events": []}')
            self.assertEqual(self.run_refresh([*args, "--preview-years", "2026", "2027"]), 1)
            self.assertEqual((root / "catalogs.json").read_bytes(), before)
            report = json.loads((root / "report.json").read_text())
            self.assertTrue(report["blockers"])

    def test_unreadable_row_cannot_be_hidden_by_valid_seed_events(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.configure(root)
            with (root / "2026.tsv").open("a") as output:
                output.write("not-a-date\tBroken event\tFootball\n")
            self.assertEqual(self.run_refresh([*args, "--preview-years", "2026", "2027"]), 1)
            self.assertFalse((root / "catalogs.json").exists())
            report = json.loads((root / "report.json").read_text())
            self.assertEqual(report["catalogs"][0]["status"], "rejected")
            self.assertTrue(report["blockers"])


if __name__ == "__main__":
    unittest.main()
