import unittest
from datetime import date

from goals_bot import parse_target_date


class ParseTargetDateTest(unittest.TestCase):
    def test_template_line(self):
        self.assertEqual(parse_target_date("🎯 Goal: x\n📅 Target date: 2026-11-15"), date(2026, 11, 15))

    def test_bold_and_dots(self):
        self.assertEqual(parse_target_date("**Target date:** 2026.11.5."), date(2026, 11, 5))

    def test_slashes_lowercase(self):
        self.assertEqual(parse_target_date("target date - 2026/1/9"), date(2026, 1, 9))

    def test_placeholder_or_missing(self):
        self.assertIsNone(parse_target_date("📅 Target date: YYYY-MM-DD"))
        self.assertIsNone(parse_target_date("no date here"))
        self.assertIsNone(parse_target_date(None))

    def test_invalid_date(self):
        self.assertIsNone(parse_target_date("Target date: 2026-02-30"))


if __name__ == "__main__":
    unittest.main()
