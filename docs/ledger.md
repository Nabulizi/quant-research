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
| QR-D01 | Diagnostic: synthetic books resolve every holding via price or terminal event; retention through universe removal; buggy-accounting positive control | Criteria P1-P3 in file header | `quantconnect/diagnostics/synthetic_terminal_returns.py` | QC `aa4dac148c22053a876a52a68d06ce5a` (2026-07-14): P1 unresolved=0 over 192 months; P2 all five terminals in bounds (LEH 0.14, TWTR 53.78, ATVI 94.42, XLNX 194.87, CELG 108.24); P3 buggy accounting omits 70 holding-months on same data | PASS - QR-008 UNLOCKED |
| QR-D02 | Diagnostic: per-year point-in-time coverage of every QC MorningStar field feeding the screener Strength/Risk v5 scorer (`fundamental-screener@0fa9049`); measurement only, informs the QR-008 window/universe/field map | Measurement-only; no pass/fail | `quantconnect/diagnostics/fundamental_field_coverage.py` | QC `f60d0f24b132ab8552716b6625eaad60` (2026-07-14), 128,000 universe-rows 2005-2026. Semantics: all ratio fields are fractions (x100 for the scorer's percent inputs); rev_g_3m consistent with quarter-YoY. Coverage: fwd_pe 0% 2005-07, ~97%+ from 2011; int_cov ~15% 2005-08, ~86-91% from 2010; div_yld ~79% (non-payers), ev_ebitda ~86% (financials, neutralized anyway); pe/de/rev_g/op_mgn/sector >=97% throughout. Cautions for the prereg: normalize non-positive pe/fwd_pe/ev_ebitda to missing; trailing div yield shows artifacts (AAPL 0.15% Jan-2005 despite paying none) so freeze a non-payer rule; op-margin 5Y average must be derived by accumulation (min 36 monthly readings, warm up from ~2006) | COMPLETE - QR-008 PRIMARY WINDOW MUST START >= 2011 |
| QR-D02b | Diagnostic: field-scale spot check for QR-008 precondition P-A (QC debug truncation hid QR-D02's SAMPLE values) | Bands from filed financials in file header | `quantconnect/diagnostics/field_scale_sample.py` | QC `25531cd2a814d48f607ac6a472f7b094` (2026-07-14), snapshot 2015-06-01: D/E and interest coverage are raw ratios (AAPL 0.34/140.3, KO 1.47/20.3, T 1.12/3.76, GE 3.24/2.80, GOOGL 0.048/171.9 -- all in band); div_yld and fcf_yld are fractions (AAPL 0.0148/0.0831, KO 0.0304); non-payers AMZN/GOOGL return div_yld=None, so the missing->0.0 non-payer rule is correct and the AAPL Jan-2005 0.15% reading was a rare stale artifact outside the 2011+ window; QC keeps extreme positive P/Es (AMZN 826.8) rather than nulling them, handled by the frozen scorer's >0-else-missing rule and <=1000 sanitize bound | P-A SATISFIED - NO FIELD-MAP AMENDMENT |
| QR-008 | Shipped Strength/Risk v5 composite (`fundamental-screener@0fa9049`), Strong-tier EW portfolio vs hold-random controls and EW-top-100 | `docs/preregistrations/QR-008-strength-risk-v5.md` FROZEN at `d8419d5` (draft `50a94d1`, P-A `8a452a2`); P-B/P-C evidence in file | `experiments/QR-008-strength-risk-v5/` at `cc6c6cb`; smoke QC `d3421d6ab5b1f2f849796a879f46d9d5`, `035c34f2f09b975b526b6aa9ea9dbf00` (machinery only) | Run 1 QC `9b16324b3d852165bd74f7d84e7d17cf` INVALID (duplicate-symbol crash 2014-07; dedupe fix `cc6c6cb`, spec unchanged). Valid run QC `9bb76ea828c3f4e8575e097a8b973ca3` (2026-07-15): net Sharpe 1.044 > controls p75 0.791 and > EW-top-100 0.815 over 2011-2022 (n=144, invalid=0, 2x-cost 1.011, MaxDD -18.9% vs -24.1%); beat EW-top-100 all 12 years, edge concentrated in down years. Caution: lags EW-top-100 and SPY in previously-viewed 2023-2026. Audit (2026-07-15): beta 0.957, alpha +3.32%/yr vs SPY (t=2.77) and +4.20%/yr vs EW-universe (t=3.79); beats 100/100 controls; not sector- or subperiod-carried; turnover 20%/mo one-way; pseudo-OOS alpha vs EW-universe ~0 (megacap regime explains the SPY lag). Details `results/QR-008-strength-risk-v5/` | PASS + AUDIT COMPLETE - ELIGIBLE FOR SHADOW OBSERVATION; NOT TRADEABLE |
| QR-D03 | Diagnostic: v5 scorer field coverage + dollar-volume distribution in the small-cap band (ranks 501-1500); pins QR-009 window, liquidity floor, cost model | Measurement-only; no pass/fail | `quantconnect/diagnostics/smallcap_field_coverage.py` | QC `2e5f1560537c348342a3e322ad0ab091` (2026-07-15), 12,000 band-rows/yr 2005-2026. fwd_pe 0% pre-2008, 92.6% from 2011; int_cov 74.9% 2011 rising to ~87% (not in the v5 coverage denominator; missing = conservative); div_yld ~56-67% (non-payers, handled); ev_ebitda ~68-82% (floor will bite more than top-500 -- report insufficient share); pe/de/rev_g/fcf >=95-100%. Dollar volume 2011: p10 $1.1M / p25 $2.4M / p50 $6.5M per day, median ~$60M by 2025. Pins: primary window 2011-2022; liquidity floor $2M/day at selection; costs stay 25/50 bps | COMPLETE - QR-009 PLACEHOLDERS PINNED |
| QR-009 | Strength/Risk v5 composite in market-cap ranks 501-1500 (capacity-constrained extension of QR-008; signal frozen, universe disjoint) | `docs/preregistrations/QR-009-smallcap-strength-risk-v5.md` FROZEN at `8b9dac3` (draft `4a73620`, pinned `ff09f3e`); P-A/P-B/P-C evidence in file | `experiments/QR-009-smallcap-strength-risk-v5/` at `0fcf09e`; smoke QC `6beacf95003b7a57ba6709b0963a6c05` (machinery only) | Awaiting the single frozen full-period run (SMOKE=False bundle from `8b9dac3`); record its QC backtest ID here | FROZEN - RUN ONCE |

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

`QR-010` is the next free identifier. QR-008 is decided (PASS, audited, in
shadow observation); QR-009 is frozen awaiting its single full-period run.
