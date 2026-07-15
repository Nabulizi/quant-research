# QR-008 audit export -- paste into a QC RESEARCH NOTEBOOK cell (not a
# backtest). Reads ObjectStore key qr008/results.json (written by the valid
# full run 9bb76ea828c3f4e8575e097a8b973ca3) and:
#   1. writes qr008_results.json into the notebook workspace -- right-click
#      it in the JupyterLab file browser > Download (works on tiers where
#      the Object Store web download is gated), and
#   2. prints a compact audit payload (~15 KB) to copy-paste instead if the
#      file download is also unavailable.
# The payload holds everything the preregistered audit needs: net monthly
# series for candidate/benchmarks/SPY, turnover, the full 100-control net
# Sharpe distribution, breadth, industry-bucket mix, and coverage counts.

import json

qb = QuantBook()
raw = qb.object_store.read("qr008/results.json")
d = json.loads(raw)
with open("qr008_results.json", "w") as f:
    f.write(raw)
print(f"wrote qr008_results.json ({len(raw)} bytes) to the notebook workspace")

BPS = 10.0


def net(book):
    return [None if g is None else g - 2 * t * BPS / 1e4
            for g, t in zip(book["gross"], book["to"])]


def sharpe(xs):
    n = len(xs)
    m = sum(xs) / n
    s = (sum((x - m) ** 2 for x in xs) / (n - 1)) ** 0.5
    return m / s * 12 ** 0.5 if s else 0.0


months = len(d["books"]["cand"]["gross"])
dates = d["dates"][:months]
years = [int(x[:4]) for x in dates]
primary = [i for i, y in enumerate(years) if 2011 <= y <= 2022]

buckets_by_year = {}
for rec, y in zip(d["records"], years):
    tgt = buckets_by_year.setdefault(y, {})
    for k, v in (rec.get("cand_buckets") or {}).items():
        tgt[k] = tgt.get(k, 0) + v

payload = {
    "dates": dates,
    "cand_net": [round(x, 6) for x in net(d["books"]["cand"])],
    "cand_to": [round(t, 4) for t in d["books"]["cand"]["to"][:months]],
    "ew100_net": [round(x, 6) for x in net(d["books"]["ew_top100"])],
    "ew100_to": [round(t, 4) for t in d["books"]["ew_top100"]["to"][:months]],
    "ewu_net": [round(x, 6) for x in net(d["books"]["ew_univ"])],
    "spy": [round(x, 6) for x in d["spy"]],
    "ctrl_net_sharpe_primary": [
        round(sharpe([net(d["books"][f"c{i:02d}"])[m] for m in primary]), 4)
        for i in range(100)
    ],
    "breadth": [r["breadth"] for r in d["records"]][:months],
    "insufficient": [r["insufficient"] for r in d["records"]][:months],
    "cand_buckets_by_year": buckets_by_year,
    "miss_last_month": d["records"][-1]["miss"],
    "entry_skips": d["entry_skips"],
}
print("AUDIT-PAYLOAD-BEGIN")
print(json.dumps(payload))
print("AUDIT-PAYLOAD-END")
