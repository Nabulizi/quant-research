# QR-009 audit export as a BACKTEST (for workflows without research
# notebooks; Object Store web download is tier-gated). Reads
# qr009/results.json (written by valid run 00e46e0e2ee3804e2eae7e9c7f1a4a99)
# and prints a compact audit payload as numbered debug chunks:
#   PAYLOAD chunks=N
#   P000|{...   P001|...   (reassemble by index, strip the P###| prefix)
# Dates are omitted: month m maps to calendar month 2011-01 + m (verified
# monotonic monthly steps). Paste the full log back for reassembly.

# region imports
from AlgorithmImports import *
import json
# endregion

BPS = 25.0
CHUNK = 170


def _net(book):
    return [None if g is None else round(g - 2 * t * BPS / 1e4, 6)
            for g, t in zip(book["gross"], book["to"])]


def _sharpe(xs):
    n = len(xs)
    m = sum(xs) / n
    s = (sum((x - m) ** 2 for x in xs) / (n - 1)) ** 0.5
    return m / s * 12 ** 0.5 if s else 0.0


class QR009AuditExport(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2024, 1, 2)
        self.set_end_date(2024, 1, 5)
        self.set_cash(100_000)
        self.add_equity("SPY", Resolution.DAILY)

        raw = self.object_store.read("qr009/results.json")
        d = json.loads(raw)
        months = len(d["books"]["cand"]["gross"])
        years = [2011 + m // 12 for m in range(months)]
        primary = [m for m, y in enumerate(years) if y <= 2022]

        buckets = {}
        for rec, y in zip(d["records"], years):
            tgt = buckets.setdefault(y, {})
            for k, v in (rec.get("buckets") or {}).items():
                tgt[k] = tgt.get(k, 0) + v

        cand = _net(d["books"]["cand"])
        payload = {
            "start": "2011-01", "months": months,
            "cand_net": cand,
            "cand_to": [round(t, 4) for t in d["books"]["cand"]["to"][:months]],
            "ew100_net": _net(d["books"]["ew_top100"]),
            "ewu_net": _net(d["books"]["ew_univ"]),
            "spy": [round(x, 6) for x in d["spy"]],
            "iwm": [round(x, 6) for x in d["iwm"]],
            "ctrl_sharpe": [
                round(_sharpe([_net(d["books"][f"c{i:02d}"])[m] for m in primary]), 4)
                for i in range(100)
            ],
            "breadth": [r["breadth"] for r in d["records"]][:months],
            "insuf": [r["insuf"] for r in d["records"]][:months],
            "buckets": buckets,
            "miss_last": d["records"][-1]["miss"],
            "skips": d["entry_skips"],
            "dvx": d["records"][-1]["dvx"],
        }
        s = json.dumps(payload, separators=(",", ":"))
        chunks = [s[i:i + CHUNK] for i in range(0, len(s), CHUNK)]
        self.debug(f"PAYLOAD chunks={len(chunks)} bytes={len(s)}")
        for i, c in enumerate(chunks):
            self.debug(f"P{i:03d}|{c}")
        self.debug("PAYLOAD-END")
