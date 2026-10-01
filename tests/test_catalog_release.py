from __future__ import annotations

from dataclasses import replace
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from catalog_fixtures import highlight, official_source, requirement, reviewed_evidence
from sportkalender.catalog_coverage import CoverageContract
from sportkalender.catalog_release import ReleaseCandidate, write_release_batch
from sportkalender.catalog_registry import load_registry
from sportkalender.catalog_validation import validate_events, validate_manifest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATHS = (ROOT / "data/sports.json", ROOT / "data/competitions.json")
REGISTRY = load_registry(*REGISTRY_PATHS)


class ReleaseTests(unittest.TestCase):
    def candidate(self, day="2026-08-28", status="preview", evidence=True):
        event = highlight(start=day)
        validation = validate_events((event,), catalog_year=2026, registry=REGISTRY)
        return ReleaseCandidate(2026, Path("candidate.tsv"), validation, status,
                                {event.event_id: reviewed_evidence(event)} if evidence else {})

    def publish(self, root, candidate, contract=CoverageContract()):
        return write_release_batch((candidate,), manifest_path=root / "catalogs.json",
                                   release_root=root / "releases", registry_paths=REGISTRY_PATHS,
                                   coverage_families=contract, sources={"organizer": official_source()}, default_id="2026")

    def test_crash_before_release_rename_keeps_previous_batch_usable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.publish(root, self.candidate())
            before = (root / "catalogs.json").read_bytes()
            replace_file = os.replace
            def fail_release(source, target):
                if Path(source).is_dir(): raise OSError("test crash before release rename")
                return replace_file(source, target)
            with patch("sportkalender.catalog_release.os.replace", side_effect=fail_release):
                with self.assertRaises(OSError): self.publish(root, self.candidate("2026-08-29"))
            self.assertEqual((root / "catalogs.json").read_bytes(), before)
            self.assertEqual(validate_manifest(root / "catalogs.json", REGISTRY)[1], ())

    def test_crash_before_manifest_replacement_keeps_previous_batch_usable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.publish(root, self.candidate())
            before = (root / "catalogs.json").read_bytes()
            replace_file = os.replace
            def fail_manifest(source, target):
                if Path(target).name == "catalogs.json": raise OSError("test crash before manifest replacement")
                return replace_file(source, target)
            with patch("sportkalender.catalog_release.os.replace", side_effect=fail_manifest):
                with self.assertRaises(OSError): self.publish(root, self.candidate("2026-08-29"))
            self.assertEqual((root / "catalogs.json").read_bytes(), before)
            self.assertEqual(validate_manifest(root / "catalogs.json", REGISTRY)[1], ())

    def test_unchanged_build_does_not_replace_manifest_or_update_time(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.publish(root, self.candidate())
            before = (root / "catalogs.json").read_bytes()
            with patch("sportkalender.catalog_release.os.replace", side_effect=AssertionError("unchanged release must not write")):
                self.publish(root, self.candidate())
            self.assertEqual((root / "catalogs.json").read_bytes(), before)

    def test_ready_passes_with_optional_and_goal_gaps(self):
        candidate = self.candidate(status="ready")
        event = candidate.validation.events[0]
        extra = highlight("all_star")
        contract = CoverageContract(({'country': 'FR', 'sport_key': 'basketball'},),
                                    (requirement(event), requirement(extra, required=False)))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, manifest = self.publish(root, candidate, contract)
            self.assertEqual(manifest["catalogs"][0]["status"], "ready")
            self.assertEqual(manifest["catalogs"][0]["coverage"]["pending_count"], 0)
            self.assertEqual(manifest["catalogs"][0]["coverage"]["optional_pending_count"], 1)

    def test_ready_cannot_be_written_with_unresolved_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError): self.publish(root, self.candidate(status="ready", evidence=False))
            self.assertFalse((root / "catalogs.json").exists())

    def test_cross_year_metadata_conflict_is_rejected_before_manifest_replace(self):
        event = highlight(start="2026-12-31", end="2027-01-01")
        first = ReleaseCandidate(2026, Path("2026.tsv"), validate_events((event,), catalog_year=2026, registry=REGISTRY), "preview")
        second_event = replace(event, audience_countries=("FR",))
        second = ReleaseCandidate(2027, Path("2027.tsv"), validate_events((second_event,), catalog_year=2027, registry=REGISTRY), "preview")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                write_release_batch((first, second), manifest_path=root / "catalogs.json", release_root=root / "releases", registry_paths=REGISTRY_PATHS, default_id="2026")
            self.assertFalse((root / "catalogs.json").exists())


    def test_dry_run_checks_candidates_against_preserved_catalogs(self):
        event = highlight(start="2026-12-31", end="2027-01-01")
        candidates = tuple(
            ReleaseCandidate(year, Path(f"{year}.tsv"), validate_events((event,), catalog_year=year, registry=REGISTRY), "preview")
            for year in (2026, 2027)
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, manifest = write_release_batch(candidates, manifest_path=root / "catalogs.json", release_root=root / "releases", registry_paths=REGISTRY_PATHS, default_id="2026")
            before = (root / "catalogs.json").read_bytes()
            changed = replace(event, title="Corrected title")
            candidate = replace(candidates[0], validation=validate_events((changed,), catalog_year=2026, registry=REGISTRY))
            with self.assertRaisesRegex(ValueError, "differs between catalogs"):
                write_release_batch((candidate,), manifest_path=root / "catalogs.json", release_root=root / "releases", registry_paths=REGISTRY_PATHS, default_id="2026", dry_run=True, preserved_entries=(manifest["catalogs"][1],))
            self.assertEqual((root / "catalogs.json").read_bytes(), before)
            self.assertEqual(len(list((root / "releases").iterdir())), 1)

    def test_dry_run_checks_ready_scope_without_writing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "audience"):
                write_release_batch((self.candidate(status="ready", evidence=False),), manifest_path=root / "catalogs.json", release_root=root / "releases", registry_paths=REGISTRY_PATHS, default_id="2026", dry_run=True)
            self.assertEqual(list(root.iterdir()), [])

    def test_unchanged_build_checks_existing_release_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, manifest = self.publish(root, self.candidate())
            before = (root / "catalogs.json").read_bytes()
            (root / manifest["catalogs"][0]["file"]).write_text("broken")
            with self.assertRaisesRegex(ValueError, "Active release checks failed"):
                self.publish(root, self.candidate())
            self.assertEqual((root / "catalogs.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
