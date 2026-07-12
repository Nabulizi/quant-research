# Repository guidance

This repository owns the systematic quant research program from `QR-008` onward.

## Required workflow

- Read `docs/program.md` and `docs/ledger.md` before changing an experiment.
- Never implement or run a full-period signal test before its preregistration is
  complete and committed.
- Treat experiment directories and recorded results as immutable evidence. A
  correction or materially changed hypothesis receives a new experiment ID.
- Never tune a failed construction. Close it in the ledger.
- Keep broker integration, order routing, credentials, and live trading out of
  this repository until a separate promotion policy explicitly permits them.

## Engineering rules

- Keep QC-independent calculations in `quant_research/` with offline unit tests.
- Keep QC data access and algorithm lifecycle code inside the relevant experiment
  or diagnostic.
- Require finite numeric inputs and complete holding-period returns.
- A missing return for a prior holding is an error, not permission to shrink the
  portfolio denominator.
- Use fixed, recorded random seeds and repository-qualified commit hashes.
- Add infrastructure only when it supports the next preregistered experiment or
  prevents a demonstrated failure mode.

## Verification

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile quant_research/*.py tests/*.py
```

