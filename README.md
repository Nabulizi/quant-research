# Quant Research

An independent research repository for designing, falsifying, and prospectively
observing systematic equity hypotheses.

This repository starts active research at `QR-008`. Earlier QuantConnect work is
preserved in sibling repositories rather than copied here:

- `../should-i-trade` owns the historical QC algorithms for `QR-001` through
  `QR-007`.
- `../fundamental-screener/docs/qc-experiment-log.md` owns their detailed
  preregistrations, results, and methodology audit.

Neither sibling application is a validated alpha engine. This repository does
not contain broker execution or live-trading code.

## Start here

1. Read [the program rules](docs/program.md).
2. Check [the experiment ledger](docs/ledger.md).
3. Copy [the preregistration template](docs/preregistration-template.md) to
   `docs/preregistrations/QR-NNN-short-name.md`.
4. Commit the completed preregistration before implementing or running the full
   historical test.
5. Store the algorithm under `experiments/QR-NNN-short-name/` and its compact,
   reproducible output under `results/QR-NNN-short-name/`.

`QR-008` is reserved but intentionally has no signal implementation yet.

## Local checks

The deterministic research core has no third-party runtime dependencies.

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile quant_research/*.py tests/*.py
```

QuantConnect algorithms run in QC Cloud. Local tests cover deterministic logic;
QC-specific universe, data, and corporate-action behavior requires a committed
diagnostic or experiment and a recorded QC backtest ID.

## Layout

```text
quant-research/
├── quant_research/       # Locally tested deterministic calculations
├── docs/                 # Program rules, ledger, and preregistrations
├── experiments/          # One immutable directory per experiment ID
├── results/              # Compact result records keyed by experiment ID
├── quantconnect/         # QC-specific diagnostics and integration notes
└── tests/                # Offline guardrail tests
```

