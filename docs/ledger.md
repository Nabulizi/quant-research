# Quant research ledger

This is the append-only operational index. Detailed preregistrations and results
for Tests 001-006 are preserved in the sibling
[historical experiment log](../../fundamental-screener/docs/qc-experiment-log.md)
and its Git history.

| ID | Hypothesis or purpose | Preregistered | Code | Result | Decision |
|---|---|---|---|---|---|
| QR-001 | Naive FCF-yield rank | Initial QC plan | `should-i-trade@5a70758` | Sharpe 0.65 vs EW-universe 0.91; MaxDD -41.9% | REJECTED |
| QR-002 | Quality gate plus FCF value | `fundamental-screener@2173021` | `should-i-trade@c879f4f` | Failed the preregistered EW-universe Sharpe criterion | REJECTED |
| QR-003 | Same-breadth random selection test | `fundamental-screener@224a3a8` | `should-i-trade@cf2db90` | Apparent pass; synthetic returns omitted held names leaving the next universe | INVALID SUPPORTING TEST |
| QR-004 | Cost and subperiod robustness | `fundamental-screener@ae1475f` | `should-i-trade@3981bbd` | Apparent pass; inherited synthetic-return attrition defect | INVALID SUPPORTING TEST |
| QR-005 | Frozen 2023-2026 extension | `fundamental-screener@b6acbee` | `should-i-trade@84902cc` | Failed after finite-input fix; also inherited return attrition defect | FAILED; METRICS INVALID |
| QR-006 | Sector, size, beta, and benchmark attribution | `fundamental-screener@73dd526` | `should-i-trade@80524fb` | Exposed material NaN bug; return metrics inherited attrition defect | DIAGNOSTIC ONLY |
| QR-007 | Corrected quality/value rerun | Existing specs; sanitation-only fix | `should-i-trade@fba1cc2` | Did not fix held-name attrition in synthetic returns | INVALID; QV50/100 UNPROVEN AND CLOSED |
| QR-D01 | Diagnostic: synthetic books resolve every holding via price or terminal event; retention through universe removal; buggy-accounting positive control | Criteria P1-P3 in file header | `quantconnect/diagnostics/synthetic_terminal_returns.py` | Awaiting QC Cloud run; record backtest ID here | PENDING - GATES QR-008 |

Authoritative historical verdict: `fundamental-screener@bd73f38`.

Methodology audit note (2026-07-11): Tests 003-006 calculate each prior synthetic
portfolio return from prices collected only for the newly eligible universe. A
prior holding that delists, loses required fundamentals, or falls outside the
top 500 is silently omitted from that month's mean. This is attrition bias and
invalidates the exact synthetic-portfolio metrics. QR-002 used actual QC holdings
and rejected qv20; qv50/100 is unproven, not exonerated. The explored family stays
closed and is not a candidate for trading. Do not spend a new experiment repairing
it.

## Next identifier

`QR-008` is reserved for the next independently motivated hypothesis. It has not
been preregistered or implemented.
