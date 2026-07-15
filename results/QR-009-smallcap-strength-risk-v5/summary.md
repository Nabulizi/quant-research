# QR-009 result: PASS (primary criterion), audit pending

- Preregistration: `docs/preregistrations/QR-009-smallcap-strength-risk-v5.md`,
  frozen at `8b9dac3`.
- Valid full run: QC backtest `00e46e0e2ee3804e2eae7e9c7f1a4a99`
  (2026-07-15, implementation `0fcf09e`). First and only run.
- Integrity: 144/144 primary book-months valid across all 103 books;
  0 of 100 controls dropped; 216 cumulative entry skips over 15 years;
  ~100 band delistings resolved via terminal events. ONE unresolved name
  (HTLF, 2025-03: QC emitted no delisting event) voided one EW-universe
  book-month in the pseudo-OOS window — handled by the preregistered void
  rule, visible as `ewu=na` in 2025; the primary window is unaffected.

## Frozen primary criterion

Over 2011-2022, candidate net Sharpe (monthly, 25 bps/side) must exceed BOTH
the 75th percentile of 100 breadth-matched hold-random controls AND the
EW-top-100 of the band.

**Result: PASS — candidate 0.782 > controls p75 0.624 and > EW-top-100 0.605.**

## Primary window (2011-2022, monthly net, n=144)

| Book | Sharpe | CAGR | MaxDD |
|---|---|---|---|
| Candidate (net 25 bps) | 0.782 | 12.84% | -28.41% |
| Candidate (net 50 bps stress) | 0.709 | 11.42% | -28.76% |
| EW-top-100 of band (net) | 0.605 | 9.34% | -29.50% |
| EW-universe / band (net) | 0.584 | 9.60% | -31.90% |
| SPY | 0.848 | 11.82% | -23.93% |
| IWM | 0.520 | 8.42% | -32.29% |

Subperiods (candidate Sharpe): 2011-2015 0.984; 2016-2019 0.948; 2020-2022
0.473 — all positive. Breadth ~100-187 Strong names. Yearly record vs the
band top-100 is streakier than QR-008 (loses 2017 and 2020, wins 2021 by
+15pp and 2022 by +7pp); single-period dependence to be checked in audit.

**Honest headline caution: SPY (0.848) out-Sharped the candidate (0.782).**
The preregistered criterion is deliberately band-relative — it tests
selection skill where institutional capacity is constrained — and the
composite added +3.2%/yr over its band net of costs. But small caps as an
asset class lagged mega caps this whole era; this result does NOT say
"small-cap Strong-tier beat the S&P 500." It didn't.

## Pseudo-out-of-sample 2023-2026 (previously viewed; cannot rescue or veto)

Candidate 0.711 / 10.51% CAGR vs band EW-top-100 0.654 / 9.78% and IWM
0.711 / 12.81%; SPY 1.522 / 19.29% (n=39). Within-band edge roughly holds;
everything small trails SPY.

## Audit (complete 2026-07-15; `audit.py` over `audit_payload.json`)

Series exported via QC backtest `0e7faac06171da3d2038fb47b9b7eae3`;
verdict Sharpe cross-checks exactly (0.782). Reproduce: `python3 audit.py`.

- **The decisive decomposition:** vs its band, alpha **+3.70%/yr (t=3.37)**,
  beta 0.907, R2 0.954; vs IWM, alpha **+4.91%/yr (t=3.54)**. vs SPY, beta
  1.107 and alpha **0.08%/yr (t=0.04)** -- i.e. genuine within-band selection
  skill, but ZERO S&P-relative alpha: everything above SPY-scale returns is
  small-cap asset-class exposure, which did not pay this era.
- **Controls:** beats ALL 100 (distribution 0.510-0.673, p75 0.624).
- **Not single-period-carried:** excluding 2021 entirely, Sharpe 0.696
  (still above both preregistered thresholds) and band alpha +2.83%/yr
  (t=2.71). Subperiod alphas positive throughout.
- **Not sector-carried:** Diversified 69-86%/yr; cyclicals peak 21% (2022);
  REITs peak 15%; banks ~0 (band financials mostly tier Weak/neutralized).
- **Turnover/costs:** 21.3%/month one-way; 1.28%/yr drag at 25 bps
  (2.6%/yr at stress -- consistent with the 0.709 stress Sharpe).
- **Universe integrity:** dollar-volume floor excluded ~51 names/month
  (9,362 cumulative), matching QR-D03's estimate; insufficient-data rows
  28-84 of the band (the coverage floor bites harder down-cap, as
  preregistered); entry skips 216 over 15 years.
- **Pseudo-OOS:** band alpha +0.35%/yr (t=0.20) -- neutral within the band,
  same pattern as QR-008; vs SPY -8.8%/yr (t=-1.64, n.s.) = the size
  headwind, not stock selection.

All preregistered checks pass. Eligible for shadow observation alongside
QR-008. Scope sentence for the evidence registry: within-band selection
alpha confirmed; no S&P-relative alpha -- holding this strategy is a
small-cap allocation decision plus selection, not a market-beating machine.

## Interpretation per the prereg

PASS -> audit, then shadow-observation eligibility alongside QR-008; the
screener evidence registry gains a small-cap scope entry stating both the
within-band result and the SPY caution.
