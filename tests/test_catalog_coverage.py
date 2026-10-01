from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from catalog_fixtures import highlight, official_source, requirement, reviewed_evidence
from sportkalender.catalog_coverage import CoverageContract, build_coverage_report, load_coverage_families
from sportkalender.catalog_registry import load_registry

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = load_registry(ROOT / 'data/sports.json', ROOT / 'data/competitions.json')
SOURCES = {'organizer': official_source()}


class CatalogCoverageTests(unittest.TestCase):
    def report(self, events, requirements, evidence=None, year=2027, sources=None):
        return build_coverage_report(tuple(events), evidence or {}, year, CoverageContract(
            ({'country': 'FR', 'sport_key': 'basketball'},), tuple(requirements)),
            SOURCES if sources is None else sources)

    def test_opening_and_closing_use_dates_in_separate_years(self):
        opener = highlight()
        closing = highlight('final_matchday', start='2027-05-22')
        requirements = [requirement(opener), requirement(closing)]
        evidence = {e.event_id: reviewed_evidence(e) for e in [opener, closing]}
        for year, event in [(2026, opener), (2027, closing)]:
            report = self.report([opener, closing], requirements, evidence, year)
            self.assertEqual(report['expected_count'], 1)
            self.assertEqual(report['verified_count'], 1)
            self.assertEqual(report['rows'][0]['expected_event_id'], event.event_id)

    def test_closing_and_next_opener_need_independent_evidence(self):
        closing = highlight('final_matchday', start='2027-05-22')
        opener = highlight(season='2027-28', start='2027-08-20')
        report = self.report([closing, opener], [requirement(closing), requirement(opener)],
                             {closing.event_id: reviewed_evidence(closing)})
        self.assertEqual(report['verified_count'], 1)
        self.assertEqual(report['pending_count'], 1)
        self.assertEqual(report['rows'][1]['status'], 'pending_date_check')
        self.assertTrue(report['rows'][1]['blocks_ready'])

    def test_all_star_wrong_season_or_division_cannot_satisfy_opener(self):
        opener = highlight(start='2027-08-20', season='2027-28')
        wrong = [highlight('all_star', start='2027-08-20', season='2027-28'),
                 highlight(start='2027-08-20', season='2026-27'),
                 highlight(start='2027-08-20', season='2027-28', division='second')]
        report = self.report(wrong, [requirement(opener)], {e.event_id: reviewed_evidence(e) for e in wrong})
        self.assertEqual(report['pending_count'], 1)
        self.assertEqual(report['rows'][0]['available_count'], 0)

    def test_optional_absence_and_goal_gap_do_not_block_required_coverage(self):
        closing = highlight('final_matchday', start='2027-05-22')
        extra = highlight('all_star', start='2027-01-20')
        report = self.report([closing], [requirement(closing), requirement(extra, required=False)],
                             {closing.event_id: reviewed_evidence(closing)})
        self.assertEqual(report['pending_count'], 0)
        self.assertEqual(report['optional_pending_count'], 1)
        self.assertEqual(report['goals'][0]['status'], 'gap')
        self.assertFalse(report['goals'][0]['blocks_ready'])
        self.assertFalse(report['rows'][1]['blocks_ready'])

    def test_secondary_or_unknown_source_does_not_verify_dates(self):
        event = highlight('final_matchday', start='2027-05-22')
        for sources in [{}, {'organizer': official_source(authority='secondary')}]:
            report = self.report([event], [requirement(event)], {event.event_id: reviewed_evidence(event)}, sources=sources)
            self.assertEqual(report['verified_count'], 0)
            self.assertEqual(report['pending_count'], 1)

    def test_official_evidence_must_match_full_range_edition_and_stage(self):
        event = highlight('final_tournament', start='2027-05-20', end='2027-05-23')
        for key, value in [('confirmed_end_date', '2027-05-20'), ('season', '2027-28'),
                           ('stage', 'all_star'), ('date_statement', ''), ('date_checked_at', 'invalid'),
                           ('source_url', 'https://example.test/unregistered')]:
            with self.subTest(key=key):
                evidence = reviewed_evidence(event)
                evidence[0][key] = value
                report = self.report([event], [requirement(event)], {event.event_id: evidence})
                self.assertEqual(report['verified_count'], 0)
        report = self.report([event], [requirement(event)], {event.event_id: reviewed_evidence(event)})
        self.assertEqual(report['verified_count'], 1)
        self.assertEqual(report['published_event_count'], 1)
        self.assertEqual(report['rows'][0]['actual_end_date'], '2027-05-23')

    def test_date_verified_scope_unresolved_remains_a_separate_blocker(self):
        event = highlight('final_matchday', start='2027-05-22')
        evidence = reviewed_evidence(event)
        del evidence[0]['audience_decision']
        report = self.report([event], [requirement(event)], {event.event_id: evidence})
        self.assertEqual(report['pending_count'], 0)
        self.assertEqual(report['unresolved_audience_count'], 1)

    def test_missing_required_date_is_retained_as_pending(self):
        event = highlight('final_matchday', start='2027-05-22')
        row = {**requirement(event), 'expected_start_date': None, 'expected_end_date': None}
        report = self.report([], [row])
        self.assertEqual(report['expected_count'], 1)
        self.assertEqual(report['pending_count'], 1)
        self.assertTrue(report['rows'][0]['blocks_ready'])

    def test_rejected_optional_highlight_is_reported_without_blocking(self):
        extra = highlight('all_star', start='2027-01-20')
        report = self.report([], [{**requirement(extra, required=False), 'rejection_reason': 'The source describes a youth event.'}])
        self.assertEqual(report['rows'][0]['status'], 'rejected')
        self.assertFalse(report['rows'][0]['blocks_ready'])
        self.assertEqual(report['pending_count'], 0)

    def test_conflicting_official_dates_do_not_pass_on_one_matching_record(self):
        event = highlight('final_matchday', start='2027-05-22')
        records = reviewed_evidence(event)
        records.append({**records[0], 'confirmed_start_date': '2027-05-23', 'confirmed_end_date': '2027-05-23'})
        report = self.report([event], [requirement(event)], {event.event_id: records})
        self.assertEqual(report['pending_count'], 1)

    def test_contract_has_no_automatic_competition_quotas(self):
        contract = load_coverage_families(ROOT / 'data/coverage.json', REGISTRY)
        self.assertEqual(len(contract.goals), 20)
        self.assertFalse(any(row['required'] and row['competition_key'] == 'nba' for row in contract.highlights))
        self.assertEqual({row['stage'] for row in contract.highlights if row['required'] and row['competition_key'] == 'nfl'}, {'season_opener', 'playoff_final'})

    def test_contract_rejects_single_anchor_and_wrong_year_window(self):
        opener = highlight()
        closing = highlight('final_matchday', start='2027-05-22')
        for rows in [[requirement(opener)], [requirement(opener), {
            **requirement(closing), 'catalog_year': 2026, 'expected_start_date': '2027-05-22',
            'expected_end_date': '2027-05-22', 'date_statement': 'Official date.'}]]:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'coverage.json'
                path.write_text(json.dumps({'schema_version': 2, 'goals': [], 'highlights': rows}))
                with self.assertRaises(ValueError):
                    load_coverage_families(path, REGISTRY)


if __name__ == '__main__':
    unittest.main()
