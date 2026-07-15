"""Parity test: the Python v5 scorer must exactly reproduce the TypeScript
scorer's golden fixtures (fundamental-screener test/scoringFixtures.test.ts).
Any mismatch means the port drifted from the shipped scorer and QR-008 must
not run until it is fixed."""

import json
import unittest
from pathlib import Path

from quant_research.scoring_v5 import SCORING_VERSION, score_row

GOLDEN = Path(__file__).parent / "fixtures" / "scoring-v5-golden.json"


class TestScoringV5Parity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(GOLDEN, encoding="utf-8") as handle:
            cls.golden = json.load(handle)

    def test_fixture_version_matches_port(self):
        self.assertEqual(self.golden["scoringVersion"], SCORING_VERSION)

    def test_fixture_battery_is_nonempty(self):
        self.assertGreaterEqual(len(self.golden["cases"]), 30)

    def test_every_case_matches_exactly(self):
        for case in self.golden["cases"]:
            with self.subTest(case=case["name"]):
                self.assertEqual(score_row(case["input"]), case["output"])


if __name__ == "__main__":
    unittest.main()
