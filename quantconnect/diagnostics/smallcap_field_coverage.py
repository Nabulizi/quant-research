# QuantConnect diagnostic QR-D03: per-year coverage of the v5 scorer's
# MorningStar fields in the SMALL-CAP band (market-cap ranks 501-1500,
# price > $5), plus the dollar-volume distribution for the liquidity floor.
# Informs the QR-009 preregistration (window, universe, cost model).
# Measurement only; no pass/fail. QC Cloud only. ASCII-only, paste-safe.
#
# QR-D02 measured the TOP-500 universe; its numbers do not transfer down-cap:
# forward P/E (analyst estimates) and interest coverage are the expected weak
# fields, and the v5 coverage floor (<70% -> Weak) could shred a small-cap
# universe in years where they are absent. QR-009's window must be chosen
# from THIS table, not QR-D02's.
#
# Output per year:
#   COV <year> n=<rows> <field>=<pct> ... dv_med=<median $ daily volume, $M>
#   DV <year> p10=... p25=... (dollar-volume percentiles, $M/day)
# plus first-month SAMPLE line for one well-known small cap.

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
    ("sector",    "asset_classification.morningstar_sector_code"),
    ("dv",        "dollar_volume"),
]
RANK_LO = 500     # skip the QR-008 top-500
RANK_HI = 1500    # ranks 501-1500 inclusive
MIN_PRICE = 5.0


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


class SmallcapFieldCoverage(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2005, 1, 1)
        self.set_end_date(2026, 7, 1)
        self.set_cash(100_000)
        self.add_equity("SPY", Resolution.DAILY)
        self.universe_settings.resolution = Resolution.DAILY
        self.add_universe(self._select)
        self._last_month = -1
        self._sampled = False
        self._year = None
        self._counts = {n: 0 for n, _ in FIELDS}
        self._rows = 0
        self._dvs = []

    def _select(self, fundamentals):
        if self.time.month == self._last_month:
            return []
        self._last_month = self.time.month

        rows = []
        seen = set()
        for f in fundamentals:
            p = _num(f, "price")
            mc = _num(f, "market_cap")
            if p is None or p <= MIN_PRICE or mc is None or mc <= 0:
                continue
            if f.symbol in seen:
                continue
            seen.add(f.symbol)
            rows.append((mc, f))
        rows.sort(key=lambda x: x[0], reverse=True)
        band = [f for _, f in rows[RANK_LO:RANK_HI]]

        if self._year is not None and self.time.year != self._year:
            self._flush(str(self._year))
            self._counts = {n: 0 for n, _ in FIELDS}
            self._rows = 0
            self._dvs = []
        self._year = self.time.year

        for f in band:
            self._rows += 1
            for name, path in FIELDS:
                if _num(f, path) is not None:
                    self._counts[name] += 1
            dv = _num(f, "dollar_volume")
            if dv is not None:
                self._dvs.append(dv)

        if not self._sampled and band:
            f = band[len(band) // 2]  # a mid-band name
            vals = " ".join(f"{n}={_num(f, p)}" for n, p in FIELDS)
            self.debug(f"SAMPLE {self.time.date()} {f.symbol.value} {vals}")
            self._sampled = True
        return []

    def _flush(self, label):
        if self._rows == 0:
            self.debug(f"COV {label} n=0")
            return
        pcts = " ".join(f"{n}={100.0 * self._counts[n] / self._rows:.1f}"
                        for n, _ in FIELDS)
        dvs = sorted(self._dvs)
        def pct(q):
            return dvs[min(int(q * len(dvs)), len(dvs) - 1)] / 1e6 if dvs else 0
        self.debug(f"COV {label} n={self._rows} {pcts}")
        self.debug(f"DV {label} p10={pct(.10):.1f} p25={pct(.25):.1f} "
                   f"p50={pct(.50):.1f} p75={pct(.75):.1f} ($M/day)")

    def on_end_of_algorithm(self):
        if self._year is not None:
            self._flush(str(self._year))
        self.debug("QR-D03 done: paste COV/DV tables + SAMPLE into docs/ledger.md; "
                   "they pin the QR-009 window, liquidity floor, and cost model.")
