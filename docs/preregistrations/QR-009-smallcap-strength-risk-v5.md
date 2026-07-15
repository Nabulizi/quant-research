# QR-009: Strength/Risk v5 composite in the small-cap band

Status: FROZEN (2026-07-15)

All preconditions are satisfied (see the bottom section). The full historical
test may run exactly once against this specification; the result is final per
the interpretation rules.

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
  cannot easily arbitrage it: the band's median daily dollar volume was
  ~$6.5M in 2011 (QR-D03, QC `2e5f1560537c348342a3e322ad0ab091`) — at
  100+ name breadth, institutional position sizes require days of full
  volume per name, while a small account trades it freely.

## Frozen specification

- **Research engine and data:** QuantConnect Cloud, point-in-time MorningStar
  fundamentals, survivorship-free. Synthetic books with QR-D01 terminal
  accounting; scorer via the parity-locked port (`quant_research/scoring_v5.py`,
  fixtures from `fundamental-screener@0fa9049`).
- **Dates and evidence windows:** warm-up from 2006 for the derived 5Y
  margin; primary window 2011-01-01 through 2022-12-31 (QR-D03: forward P/E
  reaches 92.6% band coverage in 2011; interest coverage 74.9% and outside
  the v5 coverage denominator, missing = conservative); 2023-2026
  pseudo-out-of-sample, labeled previously viewed.
- **Universe:** US common equity, finite market cap > 0, price > $5, deduped,
  ranked by market cap exactly as QR-008; take ranks 501-1500, then exclude
  names with daily dollar volume <= $2,000,000 at selection (QR-D03: trims
  ~p15 of the band early, near nothing later; excluded counts logged). The
  rank definition keeps the universe disjoint from QR-008's top 500.
- **Signal/execution/portfolio/missing values:** identical to QR-008's frozen
  spec (same field map, same industry map, same Strong-tier EW rules, same
  latest-observable-close execution basis, same entry/exit rules).
- **Costs:** 25 bps per side base; 50 bps per side stress. Confirmed against
  the QR-D03 dollar-volume table with the $2M/day floor in place; no upward
  revision required.
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

- **P-A (small-cap field coverage and liquidity):** SATISFIED by QR-D03
  (QC `2e5f1560537c348342a3e322ad0ab091`, ledger 2026-07-15): window
  2011-2022, floor $2M/day, costs confirmed 25/50 bps.
- **P-B (implementation reuse):** SATISFIED. Implementation committed at
  `0fcf09e`; the five deltas vs QR-008's audited code are documented in the
  experiment README and diff-verifiable. Smoke backtest
  `6beacf95003b7a57ba6709b0963a6c05` (2011-H1): band constructed, breadth
  ~120-149, zero entry skips, zero unresolved, IWM reporting.
- **P-C (parity):** SATISFIED. Parity suite green (37/37) at `0fcf09e`.

## Reproducibility record

- Preregistration commit: draft `4a73620`, pinned `ff09f3e`; freeze commit
  recorded in the ledger row for QR-009
- Implementation commit: `0fcf09e`
- Smoke backtest (machinery only, 2011-H1): `6beacf95003b7a57ba6709b0963a6c05`
- QuantConnect project/backtest ID: `00e46e0e2ee3804e2eae7e9c7f1a4a99`
  (valid full run, 2026-07-15, first and only)
- Random seed base: QR009 (seeds 0-99)
- Result artifact or log: `results/QR-009-smallcap-strength-risk-v5/` +
  ObjectStore key `qr009/results.json`
- Final verdict commit: the commit adding the results directory (PASS on
  the primary criterion; audit pending)
