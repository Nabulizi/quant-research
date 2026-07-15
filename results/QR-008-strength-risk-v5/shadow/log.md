# QR-008 shadow observation log

Governed by `docs/shadow-observation-policy.md`. Append-only; one row per
month. Picks are committed before returns exist (git timestamp + QC backtest
ID prove prospectivity); grades are appended the following month and never
modify a picks record.

| Month | Committed | QC backtest ID | Breadth | Flags | Grade (cand vs EWU / EW100 / SPY, filled at M+1) |
|---|---|---|---|---|---|
