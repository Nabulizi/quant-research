#!/usr/bin/env python3
"""QR-009 preregistered audit over audit_payload.json (exported from QC
backtest 0e7faac06171da3d2038fb47b9b7eae3, source run 00e46e0e...).
Stdlib only:  python3 results/QR-009-strength-risk-v5/audit.py"""

import json
from pathlib import Path

d = json.loads((Path(__file__).parent / "audit_payload.json").read_text())
months = d["months"]
years = [2011 + m // 12 for m in range(months)]


def window(lo, hi):
    return [m for m, y in enumerate(years) if lo <= y <= hi]


def mean(xs):
    return sum(xs) / len(xs)


def std(xs):
    m = mean(xs)
    return (sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5


def sharpe(xs):
    s = std(xs)
    return mean(xs) / s * 12 ** 0.5 if s else 0.0


def ols(y, x):
    """y = a + b*x; returns a, b, t(a), r2."""
    n = len(y)
    xb, yb = mean(x), mean(y)
    sxx = sum((v - xb) ** 2 for v in x)
    b = sum((xv - xb) * (yv - yb) for xv, yv in zip(x, y)) / sxx
    a = yb - b * xb
    resid = [yv - a - b * xv for xv, yv in zip(x, y)]
    s2 = sum(r * r for r in resid) / (n - 2)
    se_a = (s2 * (1 / n + xb * xb / sxx)) ** 0.5
    syy = sum((v - yb) ** 2 for v in y)
    return a, b, a / se_a, 1 - sum(r * r for r in resid) / syy


def reg_line(label, y, x):
    pairs = [(a, b) for a, b in zip(y, x) if a is not None and b is not None]
    a, b, t, r2 = ols([p[0] for p in pairs], [p[1] for p in pairs])
    print(f"  vs {label}: beta={b:.3f} alpha={a*12:.2%}/yr t(alpha)={t:.2f} r2={r2:.3f}")


def report(label, lo, hi):
    idx = window(lo, hi)
    cand = [d["cand_net"][m] for m in idx]
    print(f"\n[{label}] n={len(idx)}")
    print(f"  cand sharpe={sharpe(cand):.3f} vol={std(cand)*12**.5:.1%}")
    reg_line("band-EW", cand, [d["ewu_net"][m] for m in idx])
    reg_line("SPY", cand, [d["spy"][m] for m in idx])
    reg_line("IWM", cand, [d["iwm"][m] for m in idx])


P = window(2011, 2022)
cand = [d["cand_net"][m] for m in P]
print(f"verdict cross-check: cand net sharpe 2011-2022 = {sharpe(cand):.3f} (QC logged 0.782)")

report("PRIMARY 2011-2022", 2011, 2022)
report("2020-2022", 2020, 2022)
report("PSEUDO-OOS 2023-2026", 2023, 2026)

cs = sorted(d["ctrl_sharpe"])
c = sharpe(cand)
beaten = sum(1 for v in cs if v < c)
print(f"\n[controls, primary] n=100 min={cs[0]:.3f} p25={cs[24]:.3f} p50={cs[49]:.3f} "
      f"p75={cs[74]:.3f} p90={cs[89]:.3f} max={cs[-1]:.3f}")
print(f"  candidate {c:.3f} beats {beaten}/100 controls")

to = [d["cand_to"][m] for m in P]
drag = 2 * mean(to) * 25 / 10000 * 12
print(f"\n[turnover, primary] mean one-way={mean(to):.1%}/mo "
      f"(~{mean(to)*12:.0f}x/yr one-way); base-cost drag={drag:.2%}/yr")

b = [d["breadth"][m] for m in P]
print(f"\n[breadth, primary] min={min(b)} median={sorted(b)[len(b)//2]} max={max(b)}; "
      f"months<15: {sum(1 for v in b if v < 15)}")
ins = [d["insuf"][m] for m in P]
print(f"[insufficient-data rows] min={min(ins)} max={max(ins)} of the band")

print("\n[candidate industry-bucket share by year] (Semiconductors = ALL cyclicals)")
for y in sorted(d["buckets"]):
    bk = d["buckets"][y]
    tot = sum(bk.values())
    shares = " ".join(f"{k[:4]}={v/tot:.0%}" for k, v in sorted(bk.items(), key=lambda kv: -kv[1]))
    print(f"  {y}: n={tot:5d} {shares}")

ex21 = [m for m in P if years[m] != 2021]
c21 = [d["cand_net"][m] for m in ex21]
pairs = [(d["cand_net"][m], d["ewu_net"][m]) for m in ex21 if d["ewu_net"][m] is not None]
a, b, t, r2 = ols([p[0] for p in pairs], [p[1] for p in pairs])
print(f"\n[2021-dependence] primary excl. 2021: sharpe={sharpe(c21):.3f}; "
      f"alpha vs band-EW {a*12:.2%}/yr t={t:.2f}")

print(f"\n[coverage, last month] missing of band: {d['miss_last']}")
print(f"[dv-floor exclusions, cumulative] {d['dvx']}")
print(f"[entry skips, cumulative] {d['skips']}")
