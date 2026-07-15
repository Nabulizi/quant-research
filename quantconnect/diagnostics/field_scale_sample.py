# QuantConnect diagnostic QR-D02b: field-scale spot check (precondition P-A of
# the QR-008 preregistration). QR-D02's SAMPLE line is truncated by the QC log
# viewer, so this prints ONE SHORT LINE PER TICKER that cannot truncate.
# Measurement only; no pass/fail logic in code -- the check is comparing the
# logged values to the filed-financials bands below. QC Cloud only.
#
# Snapshot date: first trading day of June 2015 (Q1-2015 balance sheets).
# Expected values if each field is a RAW RATIO / FRACTION (from 10-Q/10-K):
#
#   ticker  de(~)   int_cov(~)   div_yld(fraction ~)
#   AAPL    0.3-0.5    50-120       0.014-0.020
#   KO      1.3-1.7      8-14       0.030-0.036
#   T       0.9-1.1      2.5-5      0.052-0.060
#   GE      2.0-3.5      1-4        0.031-0.038
#   AMZN    1.0-1.6      3-10       NON-PAYER: expect None or 0.0
#   GOOGL   0.05-0.12    50-300     NON-PAYER: expect None or 0.0
#
# Reads:
#   de x100 of the band     -> MorningStar D/E is a PERCENT: the QR-008 field
#                              map must divide by 100 (prereg amendment).
#   de inside the band      -> ratio as assumed; P-A passes for D/E.
#   non-payer div_yld > 0   -> artifact confirmed; record its size and decide
#                              the non-payer epsilon before removing DRAFT.
# Record the backtest ID and the table under QR-D02 in docs/ledger.md.

# region imports
from AlgorithmImports import *
import math
# endregion

TICKERS = ["AAPL", "KO", "T", "GE", "AMZN", "GOOGL"]

FIELDS = [
    ("de_3m",   "operation_ratios.total_debt_equity_ratio.three_months"),
    ("de_1y",   "operation_ratios.total_debt_equity_ratio.one_year"),
    ("int_cov", "operation_ratios.interest_coverage.one_year"),
    ("div_yld", "valuation_ratios.trailing_dividend_yield"),
    ("fcf_yld", "valuation_ratios.fcf_yield"),
    ("pe",      "valuation_ratios.pe_ratio"),
]


def _num(obj, path):
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


class FieldScaleSample(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2015, 6, 1)
        self.set_end_date(2015, 6, 10)
        self.set_cash(100_000)
        self.universe_settings.resolution = Resolution.DAILY
        self.add_universe(self._select)
        self._done = False

    def _select(self, fundamentals):
        if not self._done:
            wanted = {t: None for t in TICKERS}
            for f in fundamentals:
                if f.symbol.value in wanted and wanted[f.symbol.value] is None:
                    wanted[f.symbol.value] = f
            for t in TICKERS:
                f = wanted[t]
                if f is None:
                    self.debug(f"SCALE {t}: not in fundamentals")
                    continue
                for name, path in FIELDS:
                    self.debug(f"SCALE {t} {name}={_num(f, path)}")
            self._done = True
            self.debug("QR-D02b done: compare against the bands in the file "
                       "header; record under QR-D02 in docs/ledger.md.")
        return []
