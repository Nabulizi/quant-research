# QR-008: Shipped Strength/Risk v5 composite, Strong-tier portfolio

Status: DRAFT

Do not run the full-period backtest until this file is complete and committed.
The DRAFT marker may be removed only after the three preconditions at the
bottom are satisfied.

## Claim and mechanism

- **Claim:** An equal-weight, monthly-rebalanced portfolio of every US equity
  tiered "Strong" by the fundamental-screener scoring framework v5, frozen
  as shipped at `fundamental-screener@0fa9049`, beats the preregistered
  benchmarks net of costs over 2011-2022.
- **Mechanism:** The composite overweights cash-conversion quality, serviceable
  balance sheets, and improving fundamentals (revenue acceleration, margin
  inflection) while capping crowded, value-trap, and peak-cycle setups.
  Quality/profitability tilts have documented historical premia; the
  improvement criteria target pre-recognition repricing. Whether this
  particular weighted combination clears realistic costs and a mega-cap-heavy
  benchmark is exactly what is unknown.
- **Prior evidence:** None for this composite. It was designed as a screening
  heuristic, not fit to return data. Related academic factor evidence (quality,
  profitability) is directional support only. The screener's own UI labels the
  score "an experimental heuristic, not a validated return forecast."
- **What is genuinely new:** This is product validation of a shipped,
  independently motivated score. It is not a repair of the closed QR-001..007
  FCF-yield/quality-value rank family: the v5 composite is a 12-criterion
  tiered classifier with eliminators, waivers, and caps, existing for product
  reasons regardless of this test's outcome. The exact shipped logic is frozen
  by golden fixtures (`tests/fixtures/scoring-v5-golden.json`) and the
  parity-proven Python port (`quant_research/scoring_v5.py`,
  `tests/test_scoring_v5.py`, 37/37 exact matches; mutation-checked).
  Whatever the verdict, it will be linked from the screener UI.

## Frozen specification

- **Research engine and data:** QuantConnect Cloud, point-in-time MorningStar
  fundamentals, survivorship-free US equity data. Synthetic (order-free)
  portfolio books using the terminal-return accounting validated by QR-D01
  (QC `aa4dac148c22053a876a52a68d06ce5a`). Field coverage and semantics per
  QR-D02 (QC `f60d0f24b132ab8552716b6625eaad60`).
- **Dates and evidence windows:**
  - Warm-up (no evaluation): 2006-01-01 to 2010-12-31, accumulating the
    derived 5Y operating-margin baseline.
  - Primary evaluation: 2011-01-01 to 2022-12-31. QR-D02 shows forward P/E
    and interest coverage are unusable earlier.
  - Pseudo-out-of-sample extension: 2023-01-01 to 2026-06-30, reported and
    clearly labeled as a previously viewed period. It cannot rescue or veto
    the primary criterion.
- **Universe:** US common equity with point-in-time fundamentals, finite
  market cap > 0, price > $5; top 500 by market cap at each monthly selection
  (identical filter to QR-D02).
- **Signal date:** First trading day of each month; fundamentals as delivered
  by QC universe selection that morning.
- **Execution date:** Same day, 90 minutes after market open (QR-D01
  schedule), synthetic book rebalanced at observed prices.
- **Signal:** Score every universe member with `quant_research/scoring_v5.py`
  (parity-locked to `fundamental-screener@0fa9049`, SCORING_VERSION=5).
  Portfolio holds the "strong" tier. Field map (QC -> scorer input):

  | Scorer input | QC source | Transform |
  |---|---|---|
  | trailingPE | `valuation_ratios.pe_ratio` | keep if > 0, else missing |
  | forwardPE | `valuation_ratios.forward_pe_ratio` | keep if > 0, else missing |
  | dividendYieldPercent | `valuation_ratios.trailing_dividend_yield` | x100; missing -> 0.0 (non-payer rule) |
  | fcfYieldPercent | `valuation_ratios.fcf_yield` | x100 |
  | evToEbitda | `valuation_ratios.ev_to_ebitda` | keep if > 0, else missing |
  | revenueGrowthTTM | `operation_ratios.revenue_growth.one_year` | x100 |
  | revenueGrowthQuarterly | `operation_ratios.revenue_growth.three_months` | x100 |
  | operatingMarginTTM | `operation_ratios.operation_margin.one_year` | x100 |
  | operatingMargin5Y | derived | mean of trailing 60 monthly operatingMarginTTM readings; missing until >= 36 readings |
  | interestCoverage | `operation_ratios.interest_coverage.one_year` | none (ratio) |
  | debtToEquity | `operation_ratios.total_debt_equity_ratio.three_months` | none (ratio) — scale must pass precondition P-A |
  | marketCap | `market_cap` | none |
  | ytdReturn | adjusted daily closes | percent return from prior calendar-year last close to signal date |
  | rangePosition | adjusted daily closes | (price - low) / (high - low) over trailing 252 trading days incl. signal date; missing if high <= low |
  | ticker | `symbol.value` | ticker overrides in scoring_v5 apply as-is |
  | industry | MorningStar sector/industry-group codes | frozen named mapping, precondition P-B |

  Industry mapping (named buckets; code table committed as precondition P-B):
  financial = Financial Services sector; REIT = Real Estate sector; cyclical =
  Basic Materials and Energy sectors plus the Semiconductors, Automobiles &
  Components, Airlines, Marine/Shipping, Construction & Homebuilding, and
  Paper & Forest Products industry groups.
- **Missing values:** Handled inside the frozen scorer (missing scores 0;
  the v5 coverage floor forces sparse rows to "weak", so they are never
  held). Log per-rebalance: universe size, per-field missing counts,
  suspect-growth count, insufficient-data count, and Strong-tier breadth.
- **Portfolio:** Long-only, equal-weight, every Strong-tier name; monthly
  rebalance. Fewer than 15 Strong names: hold all of them. Zero Strong
  names: hold cash that month and log it. No substitute selection rule under
  any condition.
- **Costs:** 10 bps per side base; 20 bps per side stress.
- **Random controls:** 100 hold-random controls, seed base `QR008`, seeds
  0-99, drawn from the same monthly top-500 universe, each matching that
  month's Strong-tier breadth; members are retained while still in the
  universe and departures are replaced by uniform random draws without
  replacement.
- **Benchmarks:** EW-universe (top 500), EW-top-100-by-market-cap, SPY.
  All synthetic books use identical return accounting.
- **Terminal returns:** Exactly the QR-D01-validated mechanics: departing
  holdings keep their subscription via union universe selection; every prior
  holding resolves each month through a price or a consumed
  delisting/merger/bankruptcy event; any unresolved held name invalidates
  that period rather than shrinking the return denominator.

## Primary criterion

Over 2011-01-01 to 2022-12-31, the candidate's net Sharpe (monthly returns,
base costs) exceeds BOTH (a) the 75th percentile of the 100 hold-random
controls' net Sharpes and (b) the EW-top-100-by-market-cap net Sharpe. Both
must hold; there is no other path to PASS.

## Required robustness checks

- Twice-base costs (20 bps per side).
- Fixed subperiods 2011-2015, 2016-2019, 2020-2022, and yearly returns.
- Turnover and maximum drawdown.
- Sector, size, beta, and correlation attribution.
- Data-exclusion counts, per-field coverage, and Strong-tier breadth series.
- Pseudo-out-of-sample 2023-2026 results clearly labeled as previously viewed.

Robustness checks may veto promotion but cannot rescue a failure of the
primary criterion.

## Interpretation rules

- **PASS:** Full audit per program rules, then prospective shadow observation.
  Link the result from the fundamental-screener UI as validated historical
  evidence with its limitations stated.
- **FAIL:** Close this construction. Do not tune tiers, weights, thresholds,
  breadth, or portfolio rules. The screener keeps its "experimental heuristic"
  framing and links to this result. A materially different composite is a new
  experiment ID requiring a new mechanism.
- **INVALID:** Data or accounting failure (e.g., unresolved held names, field
  scale error discovered post-run). Fix the defect and rerun the exact frozen
  specification; record both runs in the ledger.

## Preconditions for removing DRAFT

- **P-A (field scales):** SATISFIED by QR-D02b
  (QC `25531cd2a814d48f607ac6a472f7b094`, see ledger): debtToEquity and
  interestCoverage are raw ratios (no transform); dividend and FCF yields are
  fractions (x100 as mapped); non-payers return None, validating the
  missing -> 0.0 non-payer rule. No field-map amendment required.
- **P-B (industry map):** Commit the MorningStar code table implementing the
  named buckets above to the experiment directory.
- **P-C (parity):** `python3 -m unittest tests.test_scoring_v5` green at the
  implementation commit, against fixtures regenerated from
  `fundamental-screener@0fa9049` or a commit with identical scoring.

## Reproducibility record

- Preregistration commit:
- Implementation commit:
- QuantConnect project/backtest ID:
- Random seed base: QR008 (seeds 0-99)
- Result artifact or log:
- Final verdict commit:
