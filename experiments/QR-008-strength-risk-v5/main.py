# QR-008: shipped Strength/Risk v5 composite, Strong-tier EW portfolio.
# Preregistration: docs/preregistrations/QR-008-strength-risk-v5.md.
# Do NOT run the full period until the prereg DRAFT marker is removed.
#
# QC project manifest (4 files -- see README.md in this directory):
#   main.py         this file
#   industry_map.py this directory (P-B)
#   scoring_v5.py   verbatim copy of quant_research/scoring_v5.py
#   core.py         verbatim copy of quant_research/core.py
#
# Design (frozen by the prereg):
#   - 2006-2010 warm-up accumulates the derived 5Y operating-margin baseline;
#     no books exist before 2011.
#   - Monthly: universe = top 500 by market cap, price > $5. Fundamentals are
#     mapped to the frozen scorer inputs (QR-D02/QR-D02b scales); ytd/range
#     come from a 260-bar adjusted history call ending the prior close.
#   - Synthetic books (no orders), QR-D01 accounting: candidate (all Strong-
#     tier, EW), 100 hold-random controls (seed base QR008, breadth-matched),
#     EW-universe, EW-top-100. Held names keep subscriptions via union
#     selection; each holding resolves monthly via price or terminal event;
#     an unresolved name voids that book-month (gross=None -> INVALID).
#   - Entry rule: a target with no valid price at execution is not entered
#     that month (logged); this governs entries only, never exits.
#   - Month m: turnover to[m] paid entering at step m; gross[m] realized at
#     step m+1. Primary window: months with start date in 2011-2022.
#   - Full series saved to ObjectStore key "qr008/results.json"; the Debug
#     log carries the preregistered verdict and summary tables.

# region imports
from AlgorithmImports import *
import json
import math
import pandas as pd
from random import Random

from core import apply_cost, equal_weight_turnover, percentile, return_stats
from industry_map import industry_label, resolved_codes
from scoring_v5 import score_row
# endregion

# SMOKE = True runs only through 2011-06-30: verifies the industry map
# resolves (P-B), the field map populates, and the books rebalance. The full
# frozen run uses SMOKE = False and must not happen while the prereg is DRAFT.
SMOKE = False

EVAL_START_YEAR = 2011
PRIMARY_LAST_YEAR = 2022
TOP_N = 500
TOP_100 = 100
MIN_PRICE = 5.0
BASE_BPS = 10.0
STRESS_BPS = 20.0
N_CONTROLS = 100
SEED_BASE = "QR008"
MARGIN_MIN_OBS = 36
MARGIN_WINDOW = 60
HISTORY_BARS = 260

MISS_FIELDS = ("trailingPE forwardPE fcfYieldPercent evToEbitda revenueGrowthTTM "
               "revenueGrowthQuarterly operatingMarginTTM operatingMargin5Y "
               "interestCoverage debtToEquity ytdReturn rangePosition").split()

SUBPERIODS = [(2011, 2015), (2016, 2019), (2020, 2022)]


def _walk(obj, path):
    for part in path.split("."):
        obj = getattr(obj, part, None)
        if obj is None:
            return None
    if isinstance(obj, bool) or not isinstance(obj, (int, float)):
        return None
    return obj if math.isfinite(obj) else None


class QR008StrengthRiskV5(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2006, 1, 1)
        if SMOKE:
            self.set_end_date(2011, 6, 30)
        else:
            self.set_end_date(2026, 6, 30)
        self.set_cash(100_000)
        self._spy = self.add_equity("SPY", Resolution.DAILY).symbol
        self.universe_settings.resolution = Resolution.DAILY
        self.add_universe(self._select)
        self.schedule.on(self.date_rules.month_start("SPY"),
                         self.time_rules.after_market_open("SPY", 90),
                         self._step)

        self._sel_month = -1
        self._universe_cache = []
        self._margins = {}            # symbol -> trailing monthly op-margin %
        self._pending = None          # symbol -> partial scorer row
        self._u_eligible = []
        self._u_top100 = []
        self._terminal = {}           # symbol -> terminal price (persistent)
        self._books = None
        self._rngs = [Random(f"{SEED_BASE}-{i}") for i in range(N_CONTROLS)]
        self._dates = []              # step dates (rebalance times)
        self._records = []            # per-step coverage/breadth/holdings
        self._spy_series = []
        self._spy_prev = None
        self._entry_skips = 0
        self.debug(f"QR-008 start; industry map codes: {resolved_codes()}")

    # ---- universe selection: monthly measurement + union retention ----

    def _select(self, fundamentals):
        if self.time.month == self._sel_month:
            return self._universe_cache
        self._sel_month = self.time.month

        rows = []
        for f in fundamentals:
            m = _walk(f, "operation_ratios.operation_margin.one_year")
            if m is not None:
                hist = self._margins.setdefault(f.symbol, [])
                hist.append(m * 100.0)
                if len(hist) > MARGIN_WINDOW:
                    del hist[0]
            p = _walk(f, "price")
            mc = _walk(f, "market_cap")
            if p is None or p <= MIN_PRICE or mc is None or mc <= 0:
                continue
            rows.append((mc, f))

        if self.time.year < EVAL_START_YEAR:
            self._universe_cache = []
            return self._universe_cache

        rows.sort(key=lambda x: x[0], reverse=True)
        top = [f for _, f in rows[:TOP_N]]
        self._u_eligible = [f.symbol for f in top]
        self._u_top100 = [f.symbol for f in top[:TOP_100]]
        self._pending = {f.symbol: self._row(f) for f in top}

        held = set()
        if self._books:
            for book in self._books.values():
                held.update(book["members"])
        self._universe_cache = self._u_eligible + [
            s for s in held if s not in set(self._u_eligible)
        ]
        return self._universe_cache

    def _row(self, f):
        def pos(path):
            v = _walk(f, path)
            return v if v is not None and v > 0 else None

        def x100(path):
            v = _walk(f, path)
            return v * 100.0 if v is not None else None

        div = x100("valuation_ratios.trailing_dividend_yield")
        margins = self._margins.get(f.symbol, [])
        return {
            "ticker": f.symbol.value,
            "industry": industry_label(f),
            "marketCap": _walk(f, "market_cap"),
            "trailingPE": pos("valuation_ratios.pe_ratio"),
            "forwardPE": pos("valuation_ratios.forward_pe_ratio"),
            "dividendYieldPercent": div if div is not None else 0.0,
            "fcfYieldPercent": x100("valuation_ratios.fcf_yield"),
            "evToEbitda": pos("valuation_ratios.ev_to_ebitda"),
            "revenueGrowthTTM": x100("operation_ratios.revenue_growth.one_year"),
            "revenueGrowthQuarterly": x100("operation_ratios.revenue_growth.three_months"),
            "operatingMarginTTM": x100("operation_ratios.operation_margin.one_year"),
            "operatingMargin5Y": (
                sum(margins) / len(margins) if len(margins) >= MARGIN_MIN_OBS else None
            ),
            "interestCoverage": _walk(f, "operation_ratios.interest_coverage.one_year"),
            "debtToEquity": _walk(f, "operation_ratios.total_debt_equity_ratio.three_months"),
            "ytdReturn": None,       # filled at the step from history
            "rangePosition": None,   # filled at the step from history
            "currentPrice": None,
        }

    # ---- terminal events (QR-D01 mechanics) ----

    def on_data(self, slice: Slice):
        for sym, d in slice.delistings.items():
            if d.type == DelistingType.WARNING:
                continue
            p = self._price(sym)
            if p is None and d.price > 0:
                p = d.price
            self._terminal[sym] = p
            self.debug(f"DELISTED {sym.value} {self.time.date()} terminal={p}")

    def _price(self, sym):
        try:
            sec = self.securities[sym]
        except Exception:
            return None
        p = sec.price
        return p if sec.has_data and isinstance(p, (int, float)) and p > 0 else None

    # ---- monthly step: resolve, score, rebalance ----

    def _step(self):
        if self.time.year < EVAL_START_YEAR or self._pending is None:
            return
        if self._books is None:
            self._init_books()

        first = not self._dates
        if not first:
            for book in self._books.values():
                self._resolve(book)
            spy_p = self._price(self._spy)
            self._spy_series.append(
                spy_p / self._spy_prev - 1
                if spy_p is not None and self._spy_prev is not None else None
            )
            if spy_p is not None:
                self._spy_prev = spy_p
        else:
            self._spy_prev = self._price(self._spy)
        self._dates.append(self.time.date().isoformat())

        strong, record = self._score_universe()
        breadth = len(strong)
        uni_sorted = sorted(self._u_eligible, key=lambda s: s.value)
        uni_set = set(uni_sorted)

        self._rebalance(self._books["cand"], sorted(strong, key=lambda s: s.value))
        self._rebalance(self._books["ew_univ"], uni_sorted)
        self._rebalance(self._books["ew_top100"],
                        sorted(self._u_top100, key=lambda s: s.value))
        for i in range(N_CONTROLS):
            book = self._books[f"c{i:02d}"]
            self._rebalance(book, self._control_targets(i, book, uni_sorted, uni_set, breadth))

        record["d"] = self._dates[-1]
        record["skips_cum"] = self._entry_skips
        self._records.append(record)
        if self.time.month == 1:
            cand = self._books["cand"]
            self.debug(f"HB {self._dates[-1]} months={len(cand['gross'])} "
                       f"breadth={breadth} invalid={cand['invalid']} "
                       f"skips={self._entry_skips}")

    def _score_universe(self):
        stats = self._price_stats(self._u_eligible)
        strong = []
        miss = {k: 0 for k in MISS_FIELDS}
        n_insufficient = 0
        n_suspect = 0
        cand_industries = {}
        for sym in self._u_eligible:
            row = self._pending.get(sym)
            if row is None:
                continue
            row["ytdReturn"], row["rangePosition"] = stats.get(sym, (None, None))
            for k in MISS_FIELDS:
                if row.get(k) is None:
                    miss[k] += 1
            scored = score_row(row)
            if scored["flags"]["insufficientData"]:
                n_insufficient += 1
            if scored["flags"]["suspectRevenueGrowth"]:
                n_suspect += 1
            if scored["tier"] == "strong":
                strong.append(sym)
                bucket = row["industry"]
                cand_industries[bucket] = cand_industries.get(bucket, 0) + 1
        record = {
            "breadth": len(strong),
            "insufficient": n_insufficient,
            "suspect": n_suspect,
            "miss": miss,
            "cand": sorted(s.value for s in strong),
            "cand_buckets": cand_industries,
        }
        return strong, record

    def _price_stats(self, symbols):
        """(ytdReturn %, rangePosition) per symbol from adjusted daily closes
        ending at the prior close (point-in-time at execution).

        Iterates the returned frame's own symbol groups instead of .loc
        lookups: QC's PandasMapper KeyError for absent symbols (e.g. broken
        factor files) proved uncatchable in the cloud runtime. A symbol
        without history stays (None, None) -- missing data to the scorer."""
        out = {s: (None, None) for s in symbols}
        try:
            df = self.history(list(symbols), HISTORY_BARS, Resolution.DAILY)
            if df is None or len(df) == 0 or "close" not in df:
                return out
            year = self.time.year
            for key, series in df["close"].groupby(level=0):
                try:
                    series = series.droplevel(0)
                    if len(series) == 0:
                        continue
                    values = [float(v) for v in series.values]
                    last = values[-1]
                    window = values[-252:]
                    low, high = min(window), max(window)
                    range_pos = (last - low) / (high - low) if high > low else None
                    base = None
                    for stamp, value in zip(series.index, values):
                        # Bars are stamped at end time (next midnight); the
                        # close's calendar day is one tick earlier.
                        if (stamp - pd.Timedelta(seconds=1)).year < year:
                            base = float(value)
                        else:
                            break
                    ytd = (last / base - 1) * 100.0 if base is not None and base > 0 else None
                    out[key] = (ytd, range_pos)
                except Exception:
                    continue
        except Exception as err:
            self.debug(f"HISTORY-ERR {self.time.date()} {err}")
        return out

    # ---- synthetic books ----

    def _init_books(self):
        def book():
            return {"members": [], "entry": {}, "gross": [], "to": [], "invalid": 0}

        self._books = {"cand": book(), "ew_univ": book(), "ew_top100": book()}
        for i in range(N_CONTROLS):
            self._books[f"c{i:02d}"] = book()

    def _resolve(self, book):
        if not book["members"]:
            book["gross"].append(0.0)
            return
        rets = []
        for sym in book["members"]:
            p = self._price(sym)
            if p is None:
                p = self._terminal.get(sym)
            if p is None:
                book["invalid"] += 1
                book["gross"].append(None)
                self.debug(f"UNRESOLVED {sym.value} {self.time.date()}")
                return
            rets.append(p / book["entry"][sym] - 1)
        book["gross"].append(sum(rets) / len(rets))

    def _rebalance(self, book, targets):
        entered = []
        entry = {}
        for sym in targets:
            p = self._price(sym)
            if p is None:
                self._entry_skips += 1
                continue
            entered.append(sym)
            entry[sym] = p
        book["to"].append(equal_weight_turnover(book["members"], entered))
        book["members"] = entered
        book["entry"] = entry

    def _control_targets(self, i, book, uni_sorted, uni_set, breadth):
        rng = self._rngs[i]
        kept = [s for s in book["members"] if s in uni_set]
        if len(kept) > breadth:
            kept = rng.sample(kept, breadth)
        elif len(kept) < breadth:
            kept_set = set(kept)
            pool = [s for s in uni_sorted if s not in kept_set]
            need = min(breadth - len(kept), len(pool))
            kept = kept + rng.sample(pool, need)
        return kept

    # ---- verdict ----

    def _net(self, book, bps):
        return [
            apply_cost(g, book["to"][m], bps) if g is not None else None
            for m, g in enumerate(book["gross"])
        ]

    def on_end_of_algorithm(self):
        if not self._books or not self._books["cand"]["gross"]:
            self.debug("QR-008: no evaluated months; nothing to report")
            return
        n_months = len(self._books["cand"]["gross"])
        month_year = [int(d[:4]) for d in self._dates[:n_months]]

        def sliced(series, lo, hi):
            return [series[m] for m in range(n_months) if lo <= month_year[m] <= hi]

        def stats_line(name, series, lo, hi):
            part = sliced(series, lo, hi)
            if any(v is None for v in part):
                return f"{name} {lo}-{hi}: INVALID ({sum(1 for v in part if v is None)} void months)"
            if len(part) < 2:
                return f"{name} {lo}-{hi}: <2 months"
            st = return_stats(part, 12)
            return (f"{name} {lo}-{hi}: sharpe={st.sharpe:.3f} cagr={st.cagr:.2%} "
                    f"mdd={st.max_drawdown:.2%} n={st.observations}")

        cand_net = self._net(self._books["cand"], BASE_BPS)
        cand_stress = self._net(self._books["cand"], STRESS_BPS)
        ew100_net = self._net(self._books["ew_top100"], BASE_BPS)
        ewu_net = self._net(self._books["ew_univ"], BASE_BPS)

        lo, hi = EVAL_START_YEAR, PRIMARY_LAST_YEAR
        primary_cand = sliced(cand_net, lo, hi)
        verdict = "INVALID"
        detail = ""
        if not any(v is None for v in primary_cand) and len(primary_cand) >= 2:
            cand_sharpe = return_stats(primary_cand, 12).sharpe
            ew100_part = sliced(ew100_net, lo, hi)
            if any(v is None for v in ew100_part):
                detail = "EW-top-100 has void months"
            else:
                ew100_sharpe = return_stats(ew100_part, 12).sharpe
                ctrl_sharpes = []
                dropped = 0
                for i in range(N_CONTROLS):
                    part = sliced(self._net(self._books[f"c{i:02d}"], BASE_BPS), lo, hi)
                    if any(v is None for v in part):
                        dropped += 1
                        continue
                    ctrl_sharpes.append(return_stats(part, 12).sharpe)
                if not ctrl_sharpes:
                    detail = "all controls void"
                else:
                    p75 = percentile(ctrl_sharpes, 75)
                    passed = cand_sharpe > p75 and cand_sharpe > ew100_sharpe
                    verdict = "PASS" if passed else "FAIL"
                    detail = (f"cand={cand_sharpe:.3f} ctrl_p75={p75:.3f} "
                              f"ew100={ew100_sharpe:.3f} ctrl_dropped={dropped}")
        else:
            detail = f"candidate has {sum(1 for v in primary_cand if v is None)} void months"

        self.debug(f"PRIMARY VERDICT: {verdict} ({detail})")
        self.debug(stats_line("CAND-net", cand_net, lo, hi))
        self.debug(stats_line("CAND-2xcost", cand_stress, lo, hi))
        self.debug(stats_line("EW100-net", ew100_net, lo, hi))
        self.debug(stats_line("EWUNIV-net", ewu_net, lo, hi))
        self.debug(stats_line("SPY", self._spy_series, lo, hi))
        for sub_lo, sub_hi in SUBPERIODS:
            self.debug(stats_line("CAND-net", cand_net, sub_lo, sub_hi))
        self.debug(stats_line("CAND-net OOS", cand_net, 2023, 2026))
        self.debug(stats_line("EW100-net OOS", ew100_net, 2023, 2026))
        self.debug(stats_line("SPY OOS", self._spy_series, 2023, 2026))

        for year in range(EVAL_START_YEAR, month_year[-1] + 1):
            def yr(series):
                part = sliced(series, year, year)
                if not part or any(v is None for v in part):
                    return "na"
                total = 1.0
                for v in part:
                    total *= 1 + v
                return f"{total - 1:.1%}"
            breadths = [r["breadth"] for r, y in zip(self._records, month_year) if y == year]
            avg_b = sum(breadths) / len(breadths) if breadths else 0
            self.debug(f"YR {year} cand={yr(cand_net)} ew100={yr(ew100_net)} "
                       f"ewu={yr(ewu_net)} spy={yr(self._spy_series)} breadth~{avg_b:.0f}")

        payload = {
            "experiment": "QR-008",
            "scoring_version": 5,
            "seed_base": SEED_BASE,
            "base_bps": BASE_BPS,
            "dates": self._dates,
            "spy": self._spy_series,
            "books": {
                name: {"gross": b["gross"], "to": b["to"], "invalid": b["invalid"]}
                for name, b in self._books.items()
            },
            "records": self._records,
            "entry_skips": self._entry_skips,
        }
        self.object_store.save("qr008/results.json", json.dumps(payload))
        self.debug("saved qr008/results.json; record backtest ID in ledger")
