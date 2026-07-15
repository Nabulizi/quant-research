# QuantConnect diagnostic QR-D02: point-in-time coverage of every MorningStar
# field the fundamental-screener Strength/Risk v5 scorer needs.
# Informs the QR-008 preregistration (window, universe, field mapping). NOT a
# gate and NOT a signal test: no returns are computed, no pass/fail criterion.
# QC Cloud only. ASCII-only, paste-safe.
#
# Question: for each candidate QC field feeding the v5 scorer
# (fundamental-screener@0fa9049 lib/scoring.ts, SCORING_VERSION=5), what
# fraction of a top-500-by-market-cap, price>$5 universe has a finite value,
# per year, 2005-2026? A field whose coverage is poor (or whose period
# semantics are wrong) must be remapped or excluded BEFORE the
# preregistration freezes the spec -- the v5 coverage floor (<70% -> Weak)
# would otherwise silently shred the eligible universe.
#
# Field map under test (screener input -> QC candidate path):
#   trailingPE            -> valuation_ratios.pe_ratio
#   forwardPE             -> valuation_ratios.forward_pe_ratio
#   dividendYieldPercent  -> valuation_ratios.trailing_dividend_yield (fraction?)
#   fcfYieldPercent       -> valuation_ratios.fcf_yield (fraction?)
#   evToEbitda            -> valuation_ratios.ev_to_ebitda
#   revenueGrowthTTM      -> operation_ratios.revenue_growth.one_year
#   revenueGrowthQuarterly-> operation_ratios.revenue_growth.three_months
#                            (VERIFY semantics: must be YoY for the quarter,
#                            not QoQ -- check the SAMPLE line against known
#                            figures before trusting it)
#   operatingMarginTTM    -> operation_ratios.operation_margin.one_year
#   operatingMargin5Y     -> DERIVED: trailing mean of monthly one_year
#                            readings (min 36 months) -- not probed here
#   interestCoverage      -> operation_ratios.interest_coverage.one_year
#   debtToEquity          -> operation_ratios.total_debt_equity_ratio
#                            (three_months and one_year both probed)
#   industry classification -> asset_classification.morningstar_sector_code /
#                            morningstar_industry_code (codes, not Finnhub
#                            labels: QR-008 needs a code->bucket mapping for
#                            financial/REIT/cyclical neutralization)
#   ytdReturn, rangePosition, marketCap -> price/history-derived, always
#                            available; only market_cap probed as sanity.
#
# Output (Debug log):
#   SAMPLE <date> AAPL <field>=<raw value> ...   -- semantics check (fraction
#       vs percent, growth definition) on one well-known name, first month.
#   COV <year> n=<universe-rows> <field>=<pct> ...  -- one line per year.
#   COV TOTAL ...                                 -- whole-period aggregate.
# Record the QC backtest ID and the per-year table in docs/ledger.md; the
# QR-008 prereg cites them when pinning window, universe, and field map.

# region imports
from AlgorithmImports import *
import math
# endregion

FIELDS = [
    ("mcap",      "market_cap"),
    ("pe",        "valuation_ratios.pe_ratio"),
    ("fwd_pe",    "valuation_ratios.forward_pe_ratio"),
    ("div_yld",   "valuation_ratios.trailing_dividend_yield"),
    ("fcf_yld",   "valuation_ratios.fcf_yield"),
    ("ev_ebitda", "valuation_ratios.ev_to_ebitda"),
    ("rev_g_1y",  "operation_ratios.revenue_growth.one_year"),
    ("rev_g_3m",  "operation_ratios.revenue_growth.three_months"),
    ("op_mgn_1y", "operation_ratios.operation_margin.one_year"),
    ("int_cov",   "operation_ratios.interest_coverage.one_year"),
    ("de_3m",     "operation_ratios.total_debt_equity_ratio.three_months"),
    ("de_1y",     "operation_ratios.total_debt_equity_ratio.one_year"),
    ("sector",    "asset_classification.morningstar_sector_code"),
    ("industry",  "asset_classification.morningstar_industry_code"),
]
TOP_N = 500
MIN_PRICE = 5.0


def _num(obj, path):
    """Finite numeric value at attribute path, else None. Booleans excluded."""
    try:
        for part in path.split("."):
            obj = getattr(obj, part, None)
            if obj is None:
                return None
        if isinstance(obj, bool) or not isinstance(obj, (int, float)):
            return None
        return obj if math.isfinite(obj) else None
    except Exception:
        return None


class FundamentalFieldCoverage(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2005, 1, 1)
        self.set_end_date(2026, 7, 1)
        self.set_cash(100_000)
        self.add_equity("SPY", Resolution.DAILY)  # keeps the clock ticking
        self.universe_settings.resolution = Resolution.DAILY
        self.add_universe(self._select)

        self._last_month = -1
        self._sampled = False
        self._year = None
        self._year_counts = {name: 0 for name, _ in FIELDS}
        self._year_rows = 0
        self._total_counts = {name: 0 for name, _ in FIELDS}
        self._total_rows = 0

    def _select(self, fundamentals):
        if self.time.month == self._last_month:
            return []
        self._last_month = self.time.month

        rows = []
        for f in fundamentals:
            p = _num(f, "price")
            mc = _num(f, "market_cap")
            if p is None or p <= MIN_PRICE or mc is None or mc <= 0:
                continue
            rows.append((mc, f))
        rows.sort(key=lambda x: x[0], reverse=True)
        rows = [f for _, f in rows[:TOP_N]]

        if self._year is not None and self.time.year != self._year:
            self._flush(str(self._year), self._year_counts, self._year_rows)
            self._year_counts = {name: 0 for name, _ in FIELDS}
            self._year_rows = 0
        self._year = self.time.year

        for f in rows:
            self._year_rows += 1
            self._total_rows += 1
            for name, path in FIELDS:
                if _num(f, path) is not None:
                    self._year_counts[name] += 1
                    self._total_counts[name] += 1

        if not self._sampled:
            for f in rows:
                if f.symbol.value == "AAPL":
                    vals = " ".join(f"{name}={_num(f, path)}" for name, path in FIELDS)
                    self.debug(f"SAMPLE {self.time.date()} AAPL {vals}")
                    self._sampled = True
                    break

        return []  # measurement only; never subscribe the universe

    def _flush(self, label, counts, n):
        if n == 0:
            self.debug(f"COV {label} n=0")
            return
        pcts = " ".join(f"{name}={100.0 * counts[name] / n:.1f}" for name, _ in FIELDS)
        self.debug(f"COV {label} n={n} {pcts}")

    def on_end_of_algorithm(self):
        if self._year is not None:
            self._flush(str(self._year), self._year_counts, self._year_rows)
        self._flush("TOTAL", self._total_counts, self._total_rows)
        self.debug("QR-D02 done: paste the COV table and SAMPLE line into "
                   "docs/ledger.md with the backtest ID before preregistering QR-008.")
