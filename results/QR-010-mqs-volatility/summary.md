# QR-010 result: PASS, worded per the baseline gate

- Preregistration: `docs/preregistrations/QR-010-mqs-volatility.md`, frozen
  at `ff3b918`; scoring engine and implementation at `should-i-trade@90d7b67`.
- Run: single frozen local run 2026-07-15 (`backtest_vol.py`, deterministic,
  seed QR010); raw output committed as `run-output.txt`. 256 non-overlapping
  21-day blocks, 2005-01-03 .. 2026-04-17.

## Frozen primary criterion

Block Spearman rho(score, forward RV21) negative with permutation p < 0.01,
AND bottom score quintile's mean RV21 above the top quintile's.

**Result: PASS — rho = -0.440, p < 0.00001; bottom quintile 24.8% vs top
12.2% annualized forward vol.**

## Robustness (all as preregistered)

- RV5 horizon: rho = -0.562, quintile spread 26.5% vs 9.0% (stronger short).
- Tails: higher score -> milder worst day (rho 0.268) and shallower window
  drawdown (rho 0.259).
- Subperiods: all four negative (-0.549 / -0.461 / -0.195 / -0.365);
  2016-2019 weakest (a low-vol regime with little to rank).
- Overlapping daily view agrees (rho -0.470; no significance claimed).
- Quintile means (low->high score): 24.8 / 16.9 / 12.2 / 12.1 / 12.2 — the
  score separates the WORST regime quintile from the rest and is flat above
  that: it is a "bad tape" detector, not a graded dial at the top.

## The wording gate (preregistered; determines the claim, not the pass)

rho(VIX, RV21) = 0.663 and rho(trailing RV21, RV21) = 0.556 — both exceed
the score's 0.440. **Mandated wording: the result is consistent with known
volatility persistence; the composite demonstrates no added forward-vol
information beyond same-day VIX.** The dashboard's value over a VIX quote is
aggregation and presentation, not incremental forecasting content.

## Standing evidence for should-i-trade after QR-010

1. Return timing: FALSIFIED (unchanged).
2. Next-session conditions: FALSIFIED (unchanged).
3. Forward-volatility ranking: SUPPORTED-WITHIN-SCOPE — low scores precede
   elevated volatility (pseudo-in-sample: this window was mined by the two
   prior tests), with no demonstrated information beyond VIX.
4. Clean confirmation channel (preregistered): 12 months of the prospective
   forecast log graded on the same direction, starting with the first log
   month after 2026-07-15.

Interpretation for users: the exposure-dial framing is directionally
legitimate — a low score is historically rough tape — but a VIX quote
carried the same (more) information. No tuning of weights in response; a
redesigned score is a new experiment ID with a new mechanism.
