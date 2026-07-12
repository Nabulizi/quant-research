# QuantConnect boundary

QuantConnect Cloud supplies the point-in-time fundamentals, survivorship-free
universe data, prices, mapping events, and terminal corporate-action behavior used
by the program.

Local helpers cannot prove QC lifecycle behavior. Before `QR-008`, add and run a
focused diagnostic that verifies synthetic controls retain every prior holding
through the return date and realize delisting, merger, bankruptcy, and universe-
removal returns. Record its QC backtest ID in the ledger. Do not infer this from
the older actual-holdings terminal spike: Tests 003-006 demonstrated that a
synthetic portfolio can bypass those engine protections.

Diagnostics live under `quantconnect/diagnostics/`. Signal algorithms live only
inside their registered `experiments/QR-NNN-short-name/` directory.

