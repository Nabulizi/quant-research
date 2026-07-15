# Shadow observation policy

Adopted 2026-07-15. First subject: QR-008 (the only audited PASS).

## What shadow observation is

A monthly, zero-capital, prospective log of what the frozen strategy would
hold, recorded **before** the returns exist. Its purpose is:

1. **Implementation fidelity** — prove the frozen pipeline produces sane,
   reproducible picks on live data, month after month.
2. **Prospective evidence accumulation** — build the first genuinely
   out-of-sample record, free of every historical-testing caveat.

It is explicitly **not** a statistical re-proof. A monthly strategy cannot
demonstrate a Sharpe edge prospectively in any reasonable time; anyone
treating 12 shadow months as confirmation or refutation of the historical
alpha is misreading noise. The operational record is the deliverable.

## Subject freeze

QR-008 as preregistered (frozen `d8419d5`) and implemented (`cc6c6cb`):
scoring v5 parity-locked to `fundamental-screener@0fa9049`, the committed
field map and industry map, top-500 universe, Strong-tier EW. The
fundamental-screener app may evolve its scorer independently; QR-008 shadow
observation stays on v5 regardless. Any change to the observed construction
ends this observation and requires a new experiment ID.

## Monthly procedure

Within the first three trading days of each month:

1. Run the frozen QR-008 bundle on QC Cloud with **only** the end date
   extended to the current date (the sole permitted edit, alongside SMOKE).
   Record the backtest ID.
2. Extract the final month's selection from the run (Strong-tier tickers,
   breadth, coverage counts, industry-bucket mix) and commit it as
   `results/QR-008-strength-risk-v5/shadow/YYYY-MM.json` plus a row in
   `shadow/log.md`. The git commit timestamp and QC backtest ID are the
   proof of prospectivity: picks on record before returns exist.
3. Grade the **previous** month's committed picks from this run's realized
   series (candidate vs EW-universe, EW-top-100, SPY) and append the grades
   to the prior month's row. Grades never modify the picks record.

A missed month is logged as MISSED with the reason. Two consecutive missed
months lapse the observation; a lapse and restart is recorded, not hidden.

## Monthly fidelity checks (flag, don't tune)

- Breadth inside the historical envelope (51-159); outside -> flag.
- One-way turnover vs prior month's picks near the historical ~20%/month;
  >40% -> flag.
- Insufficient-data count and per-field missing counts consistent with the
  QR-D02 baseline; a jump -> flag (possible upstream data change).
- Industry-bucket mix: any bucket >40% -> flag.

A flag triggers investigation and a written note. It never triggers a
parameter change: the construction is frozen. If investigation finds a data
or code defect, the INVALID rules of the preregistration apply.

## Review and what comes after

- **Review point:** after 12 consecutive graded months (earliest 2027-08).
- **Operational pass:** no unexplained flags, no missed-month lapses, picks
  reproducible from the recorded backtest IDs.
- **Performance guardrail (review trigger, not a kill switch):** rolling
  12-month candidate return more than 10pp below EW-universe -> a written
  regime review. Given beta ~0.96 and R2 ~0.93, larger gaps are unlikely
  without something structural; the review decides whether the mechanism
  claim still stands.
- At the review, and only then, a **promotion policy** may be written using
  this prospective record — that document (not this one) defines whether and
  how anything proceeds toward small real capital. Until it exists, no paper
  trading, no broker integration, no live capital; the program rules in
  `program.md` continue to bind.

## Relationship to fundamental-screener snapshots

The screener's own snapshot/forecast logging is a useful adjunct (different
universe, live provider data, current scoring version) but is not part of
this observation and cannot substitute for it: QR-008's record must come
from the frozen v5 pipeline on the frozen universe definition.
