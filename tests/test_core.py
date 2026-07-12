import math
import unittest

from quant_research import (
    apply_cost,
    equal_weight_return,
    equal_weight_turnover,
    finite_number,
    numeric_field,
    percentile,
    return_stats,
)


class PeriodField:
    def __init__(self, **values):
        self.__dict__.update(values)


class QuantResearchTests(unittest.TestCase):
    def test_finite_number_rejects_nan_infinity_and_bool(self):
        self.assertTrue(finite_number(1.25))
        self.assertTrue(finite_number(0))
        self.assertFalse(finite_number(float("nan")))
        self.assertFalse(finite_number(float("inf")))
        self.assertFalse(finite_number(True))
        self.assertFalse(finite_number("1.25"))

    def test_numeric_field_is_strict_about_the_requested_period(self):
        field = PeriodField(one_year=float("nan"), three_months=0.2, value=0.3)
        self.assertIsNone(numeric_field(field))
        self.assertEqual(numeric_field(field, period="three_months"), 0.2)
        self.assertEqual(numeric_field(PeriodField(one_year=0.1), "one_year"), 0.1)
        self.assertEqual(numeric_field(0.4), 0.4)
        self.assertIsNone(numeric_field(float("nan")))

    def test_percentile_matches_frozen_nearest_index_method(self):
        values = list(range(1, 11))
        self.assertEqual(percentile(values, 50), 5)
        self.assertEqual(percentile(values, 90), 9)
        with self.assertRaises(ValueError):
            percentile([], 50)
        with self.assertRaises(ValueError):
            percentile([1.0, float("nan")], 50)

    def test_return_stats_compounds_and_calculates_drawdown(self):
        stats = return_stats([0.10, -0.10, 0.10], periods_per_year=3)
        self.assertAlmostEqual(stats.cagr, 1.1 * 0.9 * 1.1 - 1)
        self.assertAlmostEqual(stats.max_drawdown, -0.10)
        self.assertEqual(stats.observations, 3)
        self.assertTrue(math.isfinite(stats.sharpe))

    def test_return_stats_rejects_invalid_observations(self):
        with self.assertRaises(ValueError):
            return_stats([0.1])
        with self.assertRaises(ValueError):
            return_stats([0.1, float("nan")])
        with self.assertRaises(ValueError):
            return_stats([0.1, -1.0])

    def test_equal_weight_turnover_handles_membership_and_weight_changes(self):
        self.assertAlmostEqual(equal_weight_turnover(["A", "B"], ["A", "C"]), 0.5)
        self.assertAlmostEqual(equal_weight_turnover(["A", "B"], ["A", "B"]), 0.0)
        self.assertAlmostEqual(equal_weight_turnover([], ["A", "B"]), 0.5)
        self.assertAlmostEqual(equal_weight_turnover(["A", "B"], []), 0.5)
        self.assertAlmostEqual(equal_weight_turnover(["A", "B"], ["A", "B", "C"]), 1 / 3)
        with self.assertRaises(ValueError):
            equal_weight_turnover(["A", "A"], ["A"])

    def test_equal_weight_return_requires_every_held_member(self):
        result = equal_weight_return(
            ["A", "B"],
            {"A": 100, "B": 50},
            {"A": 110, "B": 45},
        )
        self.assertAlmostEqual(result, 0.0)
        self.assertIsNone(equal_weight_return([], {}, {}))
        with self.assertRaises(ValueError):
            equal_weight_return(["D"], {"D": 10}, {})
        with self.assertRaises(ValueError):
            equal_weight_return(["D"], {"D": 0}, {"D": 10})

    def test_apply_cost_charges_both_sides(self):
        self.assertAlmostEqual(apply_cost(0.02, 0.25, 10), 0.0195)
        with self.assertRaises(ValueError):
            apply_cost(0.02, 1.1, 10)


if __name__ == "__main__":
    unittest.main()
