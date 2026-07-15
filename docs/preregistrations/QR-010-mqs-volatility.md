# QR-010: Market Quality Score as a forward-volatility gauge

Status: DRAFT

Do not run the full-period test until this file is complete and committed.
Unlike QR-008/009 this experiment runs locally in the `should-i-trade`
repository (Yahoo daily data, its own replay engine); the operational record
stays in this ledger.

## Claim and mechanism

- **Claim:** Lower shipped Market Quality Scores precede higher short-horizon
  realized SPY volatility. This is the testable claim under the product's
  "exposure dial" framing — a RISK-ranking claim, not a return claim.
- **Mechanism:** The composite is built from volatility, trend, breadth,
  momentum, and macro state. Volatility clusters strongly and regime
  indicators plausibly rank near-term risk even where they cannot rank
  returns (which two prior tests falsified).
- **Prior evidence:** should-i-trade's committed backtests FALSIFIED the
  return-timing claim (vol-targeting baseline won at matched exposure) and
  the next-session-conditions claim (preregistered, spread ran negative).
  The forward-volatility claim has never been tested. Vol persistence
  itself is textbook — which is exactly why the baselines below gate the
  wording.
- **What is genuinely new:** First test of the risk-ranking claim; frozen
  shipped score; explicit information-content comparison against trivial
  volatility predictors, which prior tests lacked.

## Frozen specification

- **Engine and data:** the `should-i-trade` replay engine (`backtest.py`
  machinery: same alignment, warmup, and safety overrides), Yahoo daily
  data, `ANALYSIS_START = 2005-01-01`. Scoring engine frozen at the
  `should-i-trade` main-branch commit recorded at freeze time ([FREEZE]).
- **Signal:** the shipped composite `total` computed at the close of day
  `i`, exactly as `score_day` replays it.
- **Outcome (primary):** forward realized volatility `RV21(i)` = annualized
  standard deviation of SPY daily simple returns over days `i+1 .. i+21`.
  Robustness horizon: `RV5`. Tail robustness: worst single-day SPY return
  and max intraperiod drawdown within the same window.
- **Observations:** NON-OVERLAPPING 21-trading-day blocks (every 21st scored
  day from the first scored day), ~250 observations over 2005-2026.
  Overlapping daily windows are reported as a robustness view only —
  overlap inflates significance and cannot support the primary criterion.
- **Baselines (gate the wording, not the pass):** on the same blocks,
  Spearman rank correlation with `RV21` for (a) same-day `^VIX` close and
  (b) trailing 21-day realized vol. The claim "adds information beyond
  trivial predictors" may be made only if |rho_score| exceeds both; a pass
  without that is worded "consistent with known volatility persistence".
- **Subperiods:** 2005-2010, 2011-2015, 2016-2019, 2020-2026.
- **Honesty note:** the 2005-2026 window has been mined by two prior tests
  of this score. A pass is pseudo-in-sample evidence and will be labeled as
  such; the clean extension is preregistered here as 12 months of the
  product's prospective forecast log graded against the same criterion
  direction, starting at the first log month after freeze.

## Primary criterion

On the non-overlapping blocks over the full window: Spearman rank
correlation between `total(i)` and `RV21(i)` is NEGATIVE with p < 0.01
(two-sided, exact/permutation), AND the bottom score quintile's mean RV21
exceeds the top quintile's. Both parts must hold; no other path to PASS.

## Required robustness checks

- RV5 horizon; worst-day and drawdown tails; overlapping-window view.
- Sign of the block Spearman within each of the four subperiods (report;
  three of four negative expected for a healthy pass).
- Baseline comparison (above) — determines wording, cannot rescue or veto.
- Quintile monotonicity table.

## Interpretation rules

- **PASS:** the dashboard's exposure-dial framing gains preregistered
  historical support, worded per the baseline gate; README/methodology and
  the research-summary evidence claims update accordingly; prospective
  forecast-log grading continues as the clean confirmation.
- **FAIL:** the score is descriptive-only; README/methodology remove any
  implication that low scores anticipate risk; the dashboard remains a
  conditions report. Do not tune weights in response — a redesigned score
  is a new experiment with a new mechanism.
- **INVALID:** data or replay defect (e.g., lookahead found in P-A); fix
  and rerun the exact spec, both runs recorded.

## Preconditions for removing DRAFT

- **P-A (information timing):** verify `score_day(i)` consumes data only
  through the close of day `i` (no lookahead into the forward window);
  record the check.
- **P-B (implementation):** the analysis script committed to
  `should-i-trade` implementing exactly this spec, reviewed against it.
- **P-C (freeze pin):** record the `should-i-trade` main commit hash that
  freezes the scoring engine, and run the parity of replay vs live scoring
  that repo already maintains.

## Reproducibility record

- Preregistration commit:
- should-i-trade frozen commit:
- Implementation commit:
- Result artifact or log:
- Final verdict commit:
