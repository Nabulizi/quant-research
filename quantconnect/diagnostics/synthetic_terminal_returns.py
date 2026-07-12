# QuantConnect diagnostic: synthetic terminal-return and retention accounting.
# Gate for QR-008 (see docs/program.md). NOT a strategy. QC Cloud only -- every
# line is a QC API call, so there is no local self-test; the check is reading
# the backtest logs against the criteria below. ASCII-only, paste-safe.
#
# Question: can a SYNTHETIC portfolio (price-tracked dicts, no orders) realize a
# return for EVERY prior holding through delistings, mergers, bankruptcies, and
# universe removal? Tests 003-006 could not: they collected prices only for the
# newly eligible universe, so departing holdings silently left the return mean
# (attrition bias, see docs/ledger.md audit note 2026-07-11).
#
# Two paths, one positive control:
#   T (terminal): manually subscribe names with known terminal events, hold
#     them synthetically from first data, and resolve each month via price or
#     a consumed delisting event.
#   U (universe): synthetically hold last month's top-10 by market cap; the
#     universe selector returns union(current eligible, still-held names) so
#     subscriptions are retained after a name drops out of eligibility.
#   BUGGY control: recompute path-U resolution the Tests-003-006 way (prices
#     collected only for newly eligible names) and count what it drops.
#
# Preregistered PASS criteria (all must hold):
#   P1  UNRESOLVED == 0: every synthetic holding in both paths resolves every
#       month via price or terminal event. One unresolved name = FAIL.
#   P2  Terminal prices match ground truth (QR terminal spike, actual holdings):
#         LEH  bankruptcy 2008-09     terminal < $1
#         TWTR cash merger 2022-10    terminal in [52, 56]   (~$54.20 cash)
#         ATVI cash merger 2023-10    terminal in [92, 97]   (~$95.00 cash)
#         XLNX stock merger 2022-02   terminal in [150, 250] (1.7234 AMD)
#         CELG cash+stock+CVR 2019-11 terminal in [90, 130]  ($50 + BMY + CVR)
#       All five delisting events must be consumed by the synthetic book.
#   P3  Positive control: BUGGY omission count > 0 on the same data (the old
#       accounting demonstrably drops holdings; otherwise this diagnostic
#       could not have caught the original defect).
#
# PASS unlocks preregistering QR-008. Record the QC backtest ID in
# docs/ledger.md either way.

# region imports
from AlgorithmImports import *
import math
# endregion


class SyntheticTerminalReturns(QCAlgorithm):

    TERMINAL_BOUNDS = {
        "LEH": (0.0, 1.0),
        "TWTR": (52.0, 56.0),
        "ATVI": (92.0, 97.0),
        "XLNX": (150.0, 250.0),
        "CELG": (90.0, 130.0),
    }
    SURVIVORS = ["AAPL", "MSFT"]  # must resolve every month with zero events
    TOP_N = 10                    # path-U synthetic breadth

    def initialize(self):
        self.set_start_date(2008, 1, 1)   # LEH bankruptcy in-window
        self.set_end_date(2024, 1, 1)     # ATVI Oct-2023 in-window
        self.set_cash(100_000)
        self.add_equity("SPY", Resolution.DAILY)
        self.universe_settings.resolution = Resolution.DAILY
        self.add_universe(self._select)
        self.schedule.on(self.date_rules.month_start("SPY"),
                         self.time_rules.after_market_open("SPY", 90),
                         self._step)

        self._t_syms = {}                 # ticker -> Symbol, path T
        for t in list(self.TERMINAL_BOUNDS) + self.SURVIVORS:
            eq = self.add_equity(t, Resolution.DAILY)
            eq.set_data_normalization_mode(DataNormalizationMode.RAW)
            self._t_syms[t] = eq.symbol

        self._t_prev = {}                 # path T: symbol -> prior month price
        self._terminal = {}               # symbol -> consumed terminal price
        self._t_done = {}                 # ticker -> realized terminal price

        self._u_eligible = []             # path U: current eligible symbols
        self._u_held = []                 # path U: synthetic members
        self._sel_month = -1

        self._unresolved = 0              # P1
        self._retained = 0                # held-not-eligible names still priced
        self._bug_omit = 0                # P3
        self._months = 0

    def _select(self, fundamentals):
        if self.time.month == self._sel_month:
            return self._u_eligible + self._u_held
        self._sel_month = self.time.month
        rows = []
        for f in fundamentals:
            p, mc = f.price, f.market_cap
            if not (isinstance(p, (int, float)) and math.isfinite(p) and p > 5):
                continue
            if not (isinstance(mc, (int, float)) and math.isfinite(mc) and mc > 0):
                continue
            rows.append((f.symbol, mc))
        rows.sort(key=lambda x: x[1], reverse=True)
        self._u_eligible = [s for s, _ in rows[:self.TOP_N]]
        # The fix under test: departing holdings keep their subscription.
        return self._u_eligible + [s for s in self._u_held
                                   if s not in self._u_eligible]

    def _price(self, sym):
        sec = self.securities[sym]
        p = sec.price
        return p if sec.has_data and isinstance(p, (int, float)) and p > 0 else None

    def on_data(self, slice: Slice):
        for sym, d in slice.delistings.items():
            if d.type == DelistingType.WARNING:
                self.debug(f"DELIST-WARN {sym.value} {self.time.date()} "
                           f"price={self._price(sym)}")
                continue
            p = self._price(sym) or (d.price if d.price > 0 else None)
            self._terminal[sym] = p
            self.debug(f"DELISTED {sym.value} {self.time.date()} terminal={p}")
        for _, c in slice.symbol_changed_events.items():
            self.debug(f"SYMBOL_CHANGED {c.old_symbol} -> {c.new_symbol} "
                       f"{self.time.date()}")

    def _step(self):
        self._months += 1

        # ---- path T: resolve every synthetic terminal-basket holding ----
        for t, sym in self._t_syms.items():
            if t in self._t_done:
                continue                  # closed; QC keeps quoting last price
            prev = self._t_prev.get(sym)
            if sym in self._terminal:
                term = self._terminal.pop(sym)
                if prev is None:
                    continue              # event on a name never held
                if term is not None:
                    self._t_done[t] = term
                    self.debug(f"T-RESOLVED {t} terminal={term:.4f} "
                               f"ret={term / prev - 1:.2%}")
                else:
                    self._unresolved += 1
                    self.debug(f"T-UNRESOLVED {t} terminal event without price")
                self._t_prev.pop(sym, None)
                continue
            cur = self._price(sym)
            if prev is not None and cur is None:
                self._unresolved += 1
                self.debug(f"T-UNRESOLVED {t} {self.time.date()} no price, no event")
                self._t_prev.pop(sym, None)
            elif cur is not None:
                self._t_prev[sym] = cur   # enter on first data, then roll monthly

        # ---- path U: resolve every held name, then re-select members ----
        if self._u_held:
            cur_elig = {s: self._price(s) for s in self._u_eligible}
            for sym in self._u_held:
                cur = self._price(sym)
                if sym in self._terminal:
                    self._terminal.pop(sym)
                    self.debug(f"U-RESOLVED {sym.value} via terminal event")
                elif cur is None:
                    self._unresolved += 1
                    self.debug(f"U-UNRESOLVED {sym.value} {self.time.date()}")
                elif sym not in self._u_eligible:
                    self._retained += 1
                # BUGGY control: the old accounting saw eligible prices only.
                if cur_elig.get(sym) is None:
                    self._bug_omit += 1
        self._u_held = list(self._u_eligible)
        if self._months % 12 == 1:
            self.debug(f"HEARTBEAT {self.time.date()} months={self._months} "
                       f"unresolved={self._unresolved} retained={self._retained} "
                       f"bug_omit={self._bug_omit}")

    def on_end_of_algorithm(self):
        p1 = self._unresolved == 0
        p2 = True
        for t, (lo, hi) in self.TERMINAL_BOUNDS.items():
            term = self._t_done.get(t)
            ok = term is not None and lo <= term <= hi
            p2 = p2 and ok
            self.debug(f"P2 {t}: terminal={term} bounds=[{lo},{hi}] "
                       f"{'OK' if ok else 'FAIL'}")
        p3 = self._bug_omit > 0
        self.debug(f"P1 unresolved={self._unresolved} -> {'OK' if p1 else 'FAIL'}")
        self.debug(f"P3 buggy-accounting omissions={self._bug_omit} "
                   f"retained-after-removal={self._retained} -> "
                   f"{'OK' if p3 else 'FAIL'}")
        self.debug(f"VERDICT: {'PASS' if p1 and p2 and p3 else 'FAIL'} "
                   f"({self._months} months)")
