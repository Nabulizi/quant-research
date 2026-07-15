# QR-009: Strength/Risk v5 composite in the small-cap band

Status: DRAFT

Do not run the full-period backtest until this file is complete and committed.
Placeholders marked `[QR-D03]` are pinned by the QR-D03 diagnostic before the
DRAFT marker may be removed.

## Claim and mechanism

- **Claim:** An equal-weight, monthly-rebalanced portfolio of every US equity
  in market-cap ranks 501-1500 tiered "Strong" by the v5 scorer (frozen at
  `fundamental-screener@0fa9049`) beats the preregistered benchmarks net of
  small-cap trading costs over the primary window.
- **Mechanism:** Thin analyst coverage and institutional capacity limits leave
  quality/cash-conversion mispricings less arbitraged below the top 500.
  QR-008 established the composite carries selection alpha in large caps
  (t=3.8 vs its own universe); the capacity-constrained band is where any
  such alpha should be larger and more durable — and where a small account
  is a structural advantage, not a handicap.
- **Prior evidence:** QR-008 (PASS + audit) for the identical construction in
  the top-500 band. Academic small-cap quality/profitability premia are
  directional support only. No test of this composite below the top 500
  exists.
- **What is genuinely new:** A new, disjoint universe (ranks 501-1500 never
  overlap QR-008's top 500), realistic small-cap costs, and a liquidity
  floor. The signal is unchanged and stays frozen: this is not a tune of
  QR-008 but its capacity-constrained extension. Why institutional capital
  cannot easily arbitrage it: the band's median daily dollar volume
  ([QR-D03]) does not absorb institutional position sizes at the observed
  breadth.

## Frozen specification

- **Research engine and data:** QuantConnect Cloud, point-in-time MorningStar
  fundamentals, survivorship-free. Synthetic books with QR-D01 terminal
  accounting; scorer via the parity-locked port (`quant_research/scoring_v5.py`,
  fixtures from `fundamental-screener@0fa9049`).
- **Dates and evidence windows:** warm-up from 2006 for the derived 5Y
  margin; primary window `[QR-D03: earliest year where every non-neutralized
  field clears usable coverage, expected >= 2011]` through 2022-12-31;
  2023-2026 pseudo-out-of-sample, labeled previously viewed.
- **Universe:** US common equity, finite market cap > 0, price > $5,
  median-band liquidity floor `[QR-D03: minimum daily dollar volume, chosen
  so the base cost assumption is defensible]`, deduped, market-cap ranks
  501-1500 at each monthly selection.
- **Signal/execution/portfolio/missing values:** identical to QR-008's frozen
  spec (same field map, same industry map, same Strong-tier EW rules, same
  latest-observable-close execution basis, same entry/exit rules).
- **Costs:** 25 bps per side base; 50 bps per side stress. `[QR-D03 may
  revise UP only, never down, based on the dollar-volume table.]`
- **Random controls:** 100 hold-random controls, seed base `QR009`, seeds
  0-99, breadth-matched, drawn from the same monthly band.
- **Benchmarks:** EW-universe (the 1000-name band), EW-top-100 of the band,
  SPY; IWM additionally reported as a small-cap reference (not a criterion).
- **Terminal returns:** QR-D01 mechanics; any unresolved held name voids the
  period. Small caps delist more often — the void rule is the safety net and
  a period-void in the primary window makes the run INVALID, not smaller.

## Primary criterion

Over the primary window, the candidate's net Sharpe (monthly, base costs)
exceeds BOTH (a) the 75th percentile of the 100 hold-random controls and
(b) the EW-top-100-of-band net Sharpe. Both must hold; no other path to PASS.

## Required robustness checks

- Twice-base costs (50 bps per side).
- Fixed subperiods (as in QR-008) and yearly returns.
- Turnover, maximum drawdown, breadth series.
- Sector, size, beta, and correlation attribution (vs the band EW and SPY).
- Data-exclusion counts; insufficient-data share of the band (the v5
  coverage floor is expected to bite harder here — report it).
- Pseudo-OOS 2023-2026 clearly labeled.

Robustness checks may veto promotion but cannot rescue the primary criterion.

## Interpretation rules

- **PASS:** audit, then shadow observation eligibility alongside QR-008; the
  screener evidence registry gains a small-cap scope entry.
- **FAIL:** the composite's validity stays exactly as QR-008 scoped it
  (top-500, 2011-2022); the small-cap extension is closed, not tuned. The
  evidence registry records the boundary — a negative result here is
  publishable scope information, not a loss.
- **INVALID:** data/code defect; fix and rerun the exact spec, both runs
  recorded.

## Preconditions for removing DRAFT

- **P-A (small-cap field coverage and liquidity):** run QR-D03
  (`quantconnect/diagnostics/smallcap_field_coverage.py`), record its COV/DV
  tables in the ledger, and pin the three `[QR-D03]` placeholders above.
- **P-B (implementation reuse):** the experiment reuses QR-008's audited
  implementation with only the universe filter, cost constants, seed base,
  and IWM benchmark changed; diff against `experiments/QR-008-strength-risk-v5/`
  committed and reviewed.
- **P-C (parity):** scorer parity suite green at the implementation commit.

## Reproducibility record

- Preregistration commit:
- Implementation commit:
- QuantConnect project/backtest ID:
- Random seed base: QR009 (seeds 0-99)
- Result artifact or log:
- Final verdict commit:
