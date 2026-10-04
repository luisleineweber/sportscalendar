from __future__ import annotations

import unittest

import pandas as pd

from scripts.fetch_wikipedia_merged import deduplicate_final_rows, normalize_english_date, normalize_german_date


class NormalizeEnglishDateTests(unittest.TestCase):
    def test_converts_january_cross_year_range(self) -> None:
        normalized, start, end = normalize_english_date("15 December - 3", year=2025, context_month=1)

        self.assertEqual(normalized, "15.12.2024 - 3.1.2025")
        self.assertEqual(start, "2024-12-15")
        self.assertEqual(end, "2025-01-03")

    def test_converts_long_range_with_context_month(self) -> None:
        normalized, start, end = normalize_english_date("31 - 15 March", year=2025, context_month=1)

        self.assertEqual(normalized, "31.1.2025 - 15.3.2025")
        self.assertEqual(start, "2025-01-31")
        self.assertEqual(end, "2025-03-15")

    def test_rejects_contextless_day_only_range(self) -> None:
        normalized, start, end = normalize_english_date("3 - 17", year=2025, context_month=None)

        self.assertIsNone(normalized)
        self.assertIsNone(start)
        self.assertIsNone(end)

    def test_resolves_contextual_cross_year_nfl_range(self) -> None:
        normalized, start, end = normalize_english_date("9–10 January", year=2026, context_month=9)

        self.assertEqual(normalized, "9.9.2026 - 10.1.2027")
        self.assertEqual(start, "2026-09-09")
        self.assertEqual(end, "2027-01-10")

    def test_preserves_explicit_end_year(self) -> None:
        normalized, start, end = normalize_english_date("8–5 June 2027", year=2026, context_month=9)

        self.assertEqual(normalized, "8.9.2026 - 5.6.2027")
        self.assertEqual(start, "2026-09-08")
        self.assertEqual(end, "2027-06-05")


class NormalizeGermanDateTests(unittest.TestCase):
    def test_parses_named_months_and_context_year(self) -> None:
        normalized, start, end = normalize_german_date(
            "19. Sep. – 4. Okt.",
            year=2026,
            context_month=9,
        )

        self.assertEqual(normalized, "19.9.2026 - 4.10.2026")
        self.assertEqual(start, "2026-09-19")
        self.assertEqual(end, "2026-10-04")

    def test_parses_numeric_dates_after_named_month_support(self) -> None:
        normalized, start, end = normalize_german_date(
            "1.1.2026 - 2.1.2026",
            year=2026,
            context_month=1,
        )

        self.assertEqual(normalized, "1.1.2026 - 2.1.2026")
        self.assertEqual(start, "2026-01-01")
        self.assertEqual(end, "2026-01-02")


class DeduplicateFinalRowsTests(unittest.TestCase):
    def test_prefers_de_source_for_exact_duplicate(self) -> None:
        dataframe = pd.DataFrame(
            [
                {
                    "date_raw": "1.1.2025",
                    "event_raw": "Open",
                    "sport_raw": "Tennis",
                    "location_raw": "Melbourne",
                    "status_raw": pd.NA,
                    "winner_raw": pd.NA,
                    "source": "en",
                    "source_url": "https://example.invalid/en",
                    "source_table_index": 0,
                    "source_heading": "January",
                    "source_month": 1,
                    "row_order": 1,
                    "date": "1.1.2025",
                    "event": "Open",
                    "sport": "Tennis",
                    "location": "Melbourne",
                    "sort_start_date": "2025-01-01",
                    "sort_end_date": "2025-01-01",
                    "final_row_key": "1.1.2025|open|tennis|melbourne",
                    "is_valid_final_row": True,
                    "drop_reason": pd.NA,
                    "duplicate_exact": False,
                    "duplicate_exact_preferred": False,
                    "keep_final_row": False,
                },
                {
                    "date_raw": "1.1.2025",
                    "event_raw": "Open",
                    "sport_raw": "Tennis",
                    "location_raw": "Melbourne",
                    "status_raw": pd.NA,
                    "winner_raw": pd.NA,
                    "source": "de",
                    "source_url": "https://example.invalid/de",
                    "source_table_index": 0,
                    "source_heading": "Januar",
                    "source_month": 1,
                    "row_order": 2,
                    "date": "1.1.2025",
                    "event": "Open",
                    "sport": "Tennis",
                    "location": "Melbourne",
                    "sort_start_date": "2025-01-01",
                    "sort_end_date": "2025-01-01",
                    "final_row_key": "1.1.2025|open|tennis|melbourne",
                    "is_valid_final_row": True,
                    "drop_reason": pd.NA,
                    "duplicate_exact": False,
                    "duplicate_exact_preferred": False,
                    "keep_final_row": False,
                },
            ]
        )

        annotated, kept = deduplicate_final_rows(dataframe)

        self.assertEqual(len(kept), 1)
        self.assertEqual(kept.iloc[0]["source"], "de")
        self.assertTrue(bool(annotated.loc[annotated["source"] == "de", "duplicate_exact_preferred"].iloc[0]))
        self.assertFalse(bool(annotated.loc[annotated["source"] == "en", "keep_final_row"].iloc[0]))


if __name__ == "__main__":
    unittest.main()
