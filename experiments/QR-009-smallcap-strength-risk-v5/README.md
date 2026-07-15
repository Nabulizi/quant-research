# QR-009: Strength/Risk v5 in the small-cap band

Implementation of [the preregistration](../../docs/preregistrations/QR-009-smallcap-strength-risk-v5.md).
**Do not run the full period while the prereg says `Status: DRAFT`.**

## Diff vs the audited QR-008 implementation (prereg precondition P-B)

`main.py` started as a byte copy of `../QR-008-strength-risk-v5/main.py`
(state `cc6c6cb`) with exactly these changes — verify with
`diff ../QR-008-strength-risk-v5/main.py main.py`:

1. **Universe:** rank the deduped, price>$5 list exactly as QR-008, take
   ranks 501-1500 (`RANK_LO/RANK_HI`), then drop names with daily dollar
   volume <= $2M (`MIN_DOLLAR_VOLUME`); excluded count logged (`dvx`).
2. **Costs:** `BASE_BPS = 25`, `STRESS_BPS = 50`.
3. **Seed base:** `QR009` (controls remain 100 hold-random, breadth-matched).
4. **IWM** subscribed and reported as an additional benchmark series
   (benchmark bookkeeping generalized into a two-symbol loop).
5. **ObjectStore key** `qr009/results.json`; class renamed; record keys
   shortened (`insuf`, `susp`, `buckets`, `skips`, `dvx`) and end-of-run
   log labels compacted to fit the 32000-char bundle cap.

Scoring, field map, industry map (shared from the QR-008 directory),
terminal-return accounting, execution basis, entry rules, control mechanics,
and the verdict computation are unchanged.

## Single-file bundle

`qc_bundle_main.py`, built by `build_qc_bundle.py` (same minify pipeline as
QR-008 plus bundle-only pruning of three functions this experiment never
calls: `numeric_field`, `equal_weight_return`, `resolved_codes` — sources
untouched). Regenerate after any source change and right before the frozen
full run. Only hand-edit: the `SMOKE` flag.

## Run checklist

1. Parity green at the implementation commit (P-C).
2. Smoke run: bundle with `SMOKE = True` (through 2011-06-30) — checks the
   band construction, the dollar-volume floor, and IWM plumbing.
3. Remove DRAFT from the prereg, fill its commit fields, commit (freeze).
4. Regenerate the bundle, `SMOKE = False`, run the full period once, record
   the QC backtest ID in the ledger either way.
5. Results/summary/audit follow the QR-008 pattern
   (`results/QR-009-smallcap-strength-risk-v5/`).
