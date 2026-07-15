# QR-008: shipped Strength/Risk v5, Strong-tier EW

Implementation of [the preregistration](../../docs/preregistrations/QR-008-strength-risk-v5.md).
**Do not run the full period while the prereg still says `Status: DRAFT`.**

## QC project manifest

Create one QC Cloud project with exactly these four Python files:

| QC file | Source of truth |
|---|---|
| `main.py` | this directory |
| `industry_map.py` | this directory |
| `scoring_v5.py` | `quant_research/scoring_v5.py` (copy verbatim) |
| `core.py` | `quant_research/core.py` (copy verbatim) |

## Run checklist (in order)

1. **P-C (parity):** `python3 -m unittest discover -s tests -v` green at the
   implementation commit. Record the commit hash.
2. **P-B (industry map) + smoke run:** set the end date temporarily to
   2011-06-30 and run. It must (a) initialize — a wrong enum candidate name in
   `industry_map.py` raises at initialize with the name to fix — and (b) log
   the resolved code table (`QR-008 start; industry map codes: ...`) plus a
   plausible first heartbeat. Commit the logged code table here.
3. Remove the `Status: DRAFT` marker from the preregistration, fill its
   "Preregistration commit" field, and commit. This is the freeze.
4. Restore the end date (2026-06-30), run the full period once, and record
   the QC backtest ID in `docs/ledger.md` and the prereg's reproducibility
   record. Never rerun-and-pick.
5. Copy the Debug verdict block into `results/QR-008-strength-risk-v5/summary.md`
   and download ObjectStore key `qr008/results.json` (QC project > Object
   Store) as the machine-readable artifact for the audit (attribution,
   control distribution, coverage series).

## Interpretation conventions (frozen with the implementation)

- **Month indexing:** turnover `to[m]` is paid entering positions at step
  `m`; `gross[m]` is realized at step `m+1`. Month `m` belongs to a window by
  its **start date** (`dates[m]`). Primary window = start dates 2011-2022;
  pseudo-OOS = start dates 2023+ (previously viewed; cannot rescue or veto).
- **Net returns:** `net[m] = gross[m] - 2 * to[m] * bps / 10000` via
  `core.apply_cost`; base 10 bps/side, stress 20.
- **Range/YTD:** adjusted daily closes from a 260-bar history call ending at
  the prior close — the latest information available at execution time.
  `rangePosition` uses the trailing 252 bars; `ytdReturn` is measured from
  the last close of the prior calendar year (bar end-time stamps shifted one
  tick to recover the close's calendar day).
- **5Y margin:** trailing mean of up to 60 monthly `operation_margin.one_year`
  readings (accumulated from 2006 for every name in the fundamentals feed,
  not only top-500 members); missing until 36 readings exist.
- **Entry rule:** a target with no valid price at execution is not entered
  that month (counted in `entry_skips`). This governs entries only; exits
  always follow the QR-D01 terminal-return rule — a held name that resolves
  neither by price nor by terminal event voids that book-month (`gross=None`),
  which makes the affected window INVALID rather than shrinking the mean.
- **Prices:** default (adjusted) normalization, so month-over-month price
  ratios include splits and dividends; at delisting the remaining adjustment
  factor is ~1, so the QR-D01 terminal fallback (`delisting.price`) is on a
  consistent basis.
- **Known approximations (accepted, frozen):** (a) the synthetic industry
  label drives the scorer's financial suspect-growth bound by bucket, which
  can differ from Finnhub's label for asset-light financials (e.g. V/MA get
  the tighter 60% bound); (b) scorer ticker overrides match contemporaneous
  tickers, exactly as the shipped app behaves; (c) the universe price filter
  uses the QC fundamental price field, as in QR-D02.

## INVALID conditions

Void book-months in the candidate or benchmarks during the primary window,
a field-scale error discovered post-run, or a parity-test failure at the
implementation commit. Per the prereg: fix the defect, rerun the exact frozen
spec, record both runs in the ledger.
