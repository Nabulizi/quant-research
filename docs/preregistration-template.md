# QR-NNN: hypothesis name

Status: DRAFT

Do not run the full-period backtest until this file is complete and committed.
Replace every placeholder; unresolved choices invalidate preregistration.

## Claim and mechanism

- **Claim:** [One falsifiable sentence.]
- **Mechanism:** [Why the effect should exist and persist after costs.]
- **Prior evidence:** [Literature or evidence known before this test.]
- **What is genuinely new:** [Why this is not a repair of a failed strategy.]

## Frozen specification

- **Research engine and data:** QuantConnect Cloud, point-in-time fundamentals,
  survivorship-free US equity data.
- **Dates and evidence windows:** [Exact dates and role of each window.]
- **Universe:** [Security type, liquidity, price, market-cap, and data rules.]
- **Signal date:** [Exact schedule and information cutoff.]
- **Execution date:** [Exact next-bar or scheduled execution assumption.]
- **Signal:** [Exact formula, lags, transforms, direction, and tie handling.]
- **Missing values:** Exclude every row with a non-finite required input and log
  the count at each rebalance.
- **Portfolio:** [Breadth, weighting, rebalance frequency, and constraints.]
- **Costs:** [Base bps per side and stress level.]
- **Random controls:** [Type, count, breadth, seed base, replacement behavior.]
- **Benchmarks:** EW-universe, EW-top-100-by-market-cap, and SPY.
- **Terminal returns:** [How every prior holding remains priced through universe
  removal, delisting, merger, or bankruptcy. Missing held-name returns invalidate
  a period and must never be dropped from the average.]

## Primary criterion

[Write exactly one pass/fail rule. Recommended default: net Sharpe exceeds both
the 75th percentile of same-breadth hold-random controls and EW-top-100 over the
primary evaluation window.]

## Required robustness checks

- Twice-base costs.
- Fixed historical regime subperiods and yearly returns.
- Turnover and maximum drawdown.
- Sector, size, beta, and correlation attribution.
- Data-exclusion counts and eligible-universe breadth.
- Pseudo-out-of-sample 2023-2026 results clearly labeled as previously viewed.

Robustness checks may veto promotion but cannot rescue a failure of the primary
criterion.

## Interpretation rules

- **PASS:** [What may happen next; normally an audit followed by shadow observation.]
- **FAIL:** Close this construction. Do not tune it. A materially different idea
  requires a new experiment ID and a new mechanism.
- **INVALID:** [Data/code failures that require correction and an exact rerun.]

## Reproducibility record

- Preregistration commit:
- Implementation commit:
- QuantConnect project/backtest ID:
- Random seed base:
- Result artifact or log:
- Final verdict commit:
