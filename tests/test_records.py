import unittest
from datetime import date, datetime, timezone

from providers.records import parse_record_date, record_matches_date


class TestRecordCalendarDates(unittest.TestCase):
    def test_parse_iso_dates_and_convex_millisecond_timestamps(self):
        self.assertEqual(parse_record_date("2026-10-16"), date(2026, 10, 16))
        created_at = datetime(2026, 10, 16, tzinfo=timezone.utc).timestamp() * 1000
        self.assertEqual(parse_record_date(created_at), date(2026, 10, 16))
        self.assertIsNone(parse_record_date("not-a-date"))

    def test_journal_matches_entry_date_and_timeline(self):
        journal = {"date": "2026-10-16", "startDate": "2026-10-20", "endDate": "2026-10-22"}
        self.assertTrue(record_matches_date("journal", journal, date(2026, 10, 16)))
        self.assertTrue(record_matches_date("journal", journal, date(2026, 10, 21)))
        self.assertFalse(record_matches_date("journal", journal, date(2026, 10, 23)))

    def test_open_ended_record_timeline_matches_future_date(self):
        task = {"startDate": "2026-10-16", "endDate": ""}
        self.assertTrue(record_matches_date("task", task, date(2026, 12, 1)))
        self.assertFalse(record_matches_date("task", task, date(2026, 10, 15)))

    def test_creation_date_is_included_alongside_timeline(self):
        project = {
            "createdAt": datetime(2026, 10, 10, tzinfo=timezone.utc).timestamp() * 1000,
            "startDate": "2026-11-01",
            "endDate": "2026-11-02",
        }
        self.assertTrue(record_matches_date("project", project, date(2026, 10, 10)))
        self.assertTrue(record_matches_date("project", project, date(2026, 11, 2)))


if __name__ == "__main__":
    unittest.main()
