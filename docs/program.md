# Quant research program

## Mission

Develop and falsify systematic equity hypotheses with point-in-time,
survivorship-free data. The program optimizes for trustworthy decisions, not for
producing a strategy. A rejected hypothesis is a complete result.

QuantConnect Cloud is the primary research engine. This repository owns new
research code and the operational record from `QR-008` onward.
`../fundamental-screener` remains the live screening and idea-generation
application; it is not evidence that a signal has historical alpha.

## Current state

- The QuantConnect data path passed the delisting, terminal-return, and
  point-in-time fundamental probes.
- Naive FCF yield and qv20 are rejected. The synthetic qv50/100 evidence is
  invalid and the explored family is closed, not validated.
- The 2023-2026 period has been inspected repeatedly and is no longer a clean
  holdout for new hypotheses.
- No strategy is approved for paper trading, broker integration, or live capital.

The detailed historical record remains in
`../../fundamental-screener/docs/qc-experiment-log.md`. The concise operational
index is `ledger.md` in this directory.

## Research lifecycle

Every hypothesis moves through the following states:

1. **Idea** - state the economic mechanism and why the market may not remove it.
2. **Preregistered** - freeze the signal, universe, portfolio construction,
   costs, periods, controls, and primary pass/fail criterion in a committed file.
3. **Implemented** - change only what the preregistration permits; record the code
   commit and QC backtest identifier.
4. **Audited** - run data-quality checks, null controls, trivial benchmarks,
   turnover, cost stress, and exposure attribution.
5. **Decided** - publish PASS or FAIL against the frozen primary criterion. Never
   rescue a failed test with an unregistered metric or parameter change.
6. **Observed** - only a historically passing, fully specified strategy may begin
   prospective shadow observation. Observation is not paper or live trading.

A modification inspired by a result is a new hypothesis with a new experiment
ID. It must not overwrite the original result.

## Mandatory design controls

- Ranking inputs must be finite numeric values. Log exclusions each rebalance.
- The universe must be point-in-time and survivorship-free.
- Signals use information available on the signal date and trade no earlier than
  the declared execution time.
- Same-breadth random controls use fixed, recorded seeds.
- EW-universe, EW-top-100-by-market-cap, and SPY are always reported.
- Costs, turnover, CAGR, Sharpe, maximum drawdown, and yearly returns are always
  reported.
- Sector, size, beta, and correlation attribution is required before promotion.
- The primary criterion is singular. Other diagnostics are robustness checks,
  not additional chances to declare success.
- Missing observations and corporate actions must not silently remove returns.
- Every synthetic portfolio must realize a return for every prior-period holding.
  A name leaving the new eligible universe is still a prior holding; retain its
  subscription or consume its QC delisting/terminal event. Any unresolved held
  name invalidates that period rather than shrinking the return denominator.

## Evidence periods

Historical evidence should be reported across fixed market regimes and with an
anchored or rolling walk-forward view. The already-viewed 2023-2026 window is a
pseudo-out-of-sample robustness period, not a pristine holdout. The first clean
evidence for any new frozen strategy will be prospective observations collected
after its preregistration date.

## Promotion gates

A candidate may enter prospective shadow observation only when all of these hold:

- Its net Sharpe exceeds the 75th percentile of same-breadth hold-random controls.
- Its net Sharpe exceeds EW-top-100 over the primary evaluation window.
- The result survives twice the base cost assumption.
- Performance is not carried by one sector or one short subperiod.
- Turnover, drawdown, data exclusions, and market exposures are acceptable and
  fully reported.
- The result follows the preregistration without post-result tuning.

No candidate advances from shadow observation to paper trading until a separate
promotion policy is written using genuinely prospective evidence. Execution
work remains out of scope until then.

## Engineering boundary

The harness is an extraction from the working QC experiments, not a new research
platform. Shared deterministic calculations belong in `quant_research/core.py`
and must have local unit tests. QC-specific universe selection and data access
stay in the experiment algorithm. Historical experiment files in
`../../should-i-trade` are immutable evidence; new experiments use the shared
helpers rather than rewriting old files.

Time-box infrastructure work to one working day per research cycle. If a helper
does not directly support the next preregistered experiment or prevent a known
failure mode, defer it.
