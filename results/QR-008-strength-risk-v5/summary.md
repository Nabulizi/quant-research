# QR-008 result: PASS (primary criterion), audit pending

- Preregistration: `docs/preregistrations/QR-008-strength-risk-v5.md`,
  frozen at `d8419d5` (draft `50a94d1`).
- Valid full run: QC backtest `9bb76ea828c3f4e8575e097a8b973ca3`
  (2026-07-15, implementation `cc6c6cb`). Prior full run
  `9b16324b3d852165bd74f7d84e7d17cf` was INVALID (duplicate-symbol crash
  2014-07, dedupe fixed, spec unchanged) per the prereg's INVALID rule.
- Integrity: 144/144 primary book-months valid (`invalid=0` for every book),
  0 of 100 controls dropped, 1,755 cumulative entry skips (known
  factor-file-broken symbols, uniform across books), terminal events consumed
  throughout (TWTR terminal 53.78 matches QR-D01 ground truth).

## Frozen primary criterion

Over 2011-01-01 to 2022-12-31, candidate net Sharpe (monthly, 10 bps/side)
must exceed BOTH the 75th percentile of 100 breadth-matched hold-random
controls AND EW-top-100-by-market-cap.

**Result: PASS — candidate 1.044 > controls p75 0.791 and > EW-top-100 0.815.**

## Primary window (2011-2022, monthly net, n=144)

| Book | Sharpe | CAGR | MaxDD |
|---|---|---|---|
| Candidate (net 10 bps) | 1.044 | 14.97% | -18.90% |
| Candidate (net 20 bps stress) | 1.011 | 14.42% | -19.07% |
| EW-top-100 (net) | 0.815 | 11.18% | -24.12% |
| EW-universe (net) | 0.780 | 11.40% | -24.15% |
| SPY | 0.848 | 11.82% | -23.93% |

Subperiods (candidate net Sharpe / CAGR / MaxDD): 2011-2015 1.191 / 14.97% /
-17.64%; 2016-2019 1.295 / 15.48% / -12.04%; 2020-2022 0.765 / 14.31% /
-18.90%. The candidate beat EW-top-100 in all 12 primary years; the edge is
concentrated in down years (2018: -2.5% vs -4.2%; 2022: -3.1% vs -15.0%),
i.e. defensive-quality character. Strong-tier breadth ranged ~53-149 names
(median around 90), declining over the decade.

## Pseudo-out-of-sample 2023-2026 (previously viewed; cannot rescue or veto)

Candidate 1.129 Sharpe / 14.01% CAGR vs EW-top-100 1.433 / 17.40% and SPY
1.522 / 19.29% (n=39). The candidate LAGGED both benchmarks in each of
2023, 2024, and 2025. Caution: the historical edge does not show in the
most recent, mega-cap-dominated regime.

## Audit (complete 2026-07-15; `audit.py` over `audit_payload.json`)

Series exported via QC backtest `d69ef709c90d732d0542fd85a0d370eb`
(Object Store web download is tier-gated); reassembled payload committed as
`audit_payload.json`; reproduce with `python3 audit.py`. Verdict Sharpe
cross-checks exactly (1.044).

- **Exposure: NOT a low-beta tilt.** Beta 0.957 vs SPY, vol 14.4% vs 14.5%,
  R2 0.923. Annualized CAPM alpha **+3.32%/yr (t=2.77)** vs SPY and
  **+4.20%/yr (t=3.79)** vs EW-universe (same names, same accounting). The
  earlier low-beta hypothesis is refuted; the edge is selection within a
  fully-invested market-like book.
- **Controls:** candidate 1.044 exceeds ALL 100 hold-random controls
  (distribution 0.661-0.867, p75 0.791).
- **Not sector- or subperiod-carried:** Diversified 67-86% per year,
  cyclicals 8-28% (peak 2022 = the energy year), banks/REITs <=7%; alpha
  positive in all three subperiods (2020-2022: +6.66%/yr, t=2.06).
- **Turnover/costs:** 20.4%/month one-way (~2.4x/yr); base-cost drag
  0.49%/yr, stress drag ~1%/yr.
- **Breadth/coverage:** breadth 51-159 (median 98), <15 fallback never
  triggered; insufficient-data rows 2-17 of 500; last-month missing counts
  match QR-D02 expectations.
- **Pseudo-OOS reframed:** 2023-2026 alpha vs EW-universe +0.33%/yr (t=0.19)
  -- the candidate MATCHED equal weight; the shortfall vs SPY (-2.81%/yr,
  t=-0.82, insignificant) is the megacap-vs-equal-weight regime, not
  negative selection. Recent evidence is neutral, not negative.

All preregistered promotion-gate checks pass. The candidate is eligible for
prospective shadow observation under a policy to be written before any
observation begins.

## Interpretation per the prereg

PASS -> full audit, then prospective shadow observation only. No paper or
live trading; no tuning of tiers, weights, thresholds, breadth, or portfolio
rules (any variant is a new experiment ID). The fundamental-screener UI may
link this result as historical evidence with the pseudo-OOS caution stated.
