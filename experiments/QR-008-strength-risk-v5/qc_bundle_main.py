# GENERATED single-file bundle for QR-008 -- do not edit by hand.
# Built by build_qc_bundle.py from quant-research@c0a41c4.
# Sources: quant_research/core.py, quant_research/scoring_v5.py,
#          experiments/QR-008-strength-risk-v5/{industry_map,main}.py
# Before pasting: set SMOKE = True for the P-B smoke run through
# 2011-06-30; SMOKE = False only for the frozen full-period run.
from __future__ import annotations
from AlgorithmImports import *


# ===== quant_research/core.py =====
"""Deterministic, QC-independent helpers for quant research experiments."""


import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Hashable


@dataclass(frozen=True)
class ReturnStats:
    cagr: float
    sharpe: float
    max_drawdown: float
    observations: int


def finite_number(value: Any) -> bool:
    """Return whether value is a finite real number, excluding booleans."""
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
    )


def numeric_field(field: Any, period: str = "one_year") -> float | int | None:
    """Read the requested period from a QuantConnect-style field, else None.

    No cross-period fallback: substituting another period would silently mix
    horizons in a ranking. Callers wanting a different period pass it explicitly.
    """
    value = getattr(field, period, None)
    if finite_number(value):
        return value
    return field if finite_number(field) else None


def percentile(values: Iterable[float], percent: float) -> float:
    """Return the nearest-rank-on-index percentile used by the QC experiments."""
    ordered = sorted(values)
    if not ordered:
        raise ValueError("percentile requires at least one value")
    if not all(finite_number(value) for value in ordered):
        raise ValueError("percentile values must be finite numbers")
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    index = round((percent / 100.0) * (len(ordered) - 1))
    return ordered[index]


def return_stats(returns: Sequence[float], periods_per_year: int = 12) -> ReturnStats:
    """Calculate compounded CAGR, arithmetic Sharpe, and maximum drawdown."""
    if len(returns) < 2:
        raise ValueError("return_stats requires at least two observations")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    if not all(finite_number(value) and value > -1 for value in returns):
        raise ValueError("returns must be finite and greater than -1")

    observations = len(returns)
    mean = sum(returns) / observations
    variance = sum((value - mean) ** 2 for value in returns) / (observations - 1)
    standard_deviation = variance**0.5

    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for value in returns:
        equity *= 1 + value
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity / peak - 1)

    cagr = equity ** (periods_per_year / observations) - 1
    sharpe = mean / standard_deviation * periods_per_year**0.5 if standard_deviation else 0.0
    return ReturnStats(cagr, sharpe, max_drawdown, observations)


def equal_weight_turnover(
    old_members: Sequence[Hashable], new_members: Sequence[Hashable]
) -> float:
    """Return one-way turnover as half the absolute equal-weight change."""
    if len(set(old_members)) != len(old_members) or len(set(new_members)) != len(new_members):
        raise ValueError("portfolio members must be unique")

    old_names = set(old_members)
    new_names = set(new_members)
    old_weight = 1.0 / len(old_names) if old_names else 0.0
    new_weight = 1.0 / len(new_names) if new_names else 0.0
    names = old_names | new_names
    absolute_change = sum(
        abs((new_weight if name in new_names else 0.0) -
            (old_weight if name in old_names else 0.0))
        for name in names
    )
    return absolute_change / 2.0


def equal_weight_return(
    members: Sequence[Hashable], previous: Mapping[Hashable, float], current: Mapping[Hashable, float]
) -> float | None:
    """Return the mean member return, rejecting incomplete holding-period data."""
    if len(set(members)) != len(members):
        raise ValueError("portfolio members must be unique")
    if not members:
        return None

    observed = []
    missing = []
    for member in members:
        old_price = previous.get(member)
        new_price = current.get(member)
        if (
            not finite_number(old_price)
            or not finite_number(new_price)
            or old_price <= 0
            or new_price < 0
        ):
            missing.append(member)
            continue
        observed.append(new_price / old_price - 1)
    if missing:
        raise ValueError(
            f"missing a valid holding-period return for {len(missing)} of "
            f"{len(members)} members"
        )
    return sum(observed) / len(observed)


def apply_cost(gross_return: float, one_way_turnover: float, bps_per_side: float) -> float:
    """Apply per-side trading costs to a gross periodic return."""
    if not finite_number(gross_return):
        raise ValueError("gross_return must be finite")
    if not finite_number(one_way_turnover) or not 0 <= one_way_turnover <= 1:
        raise ValueError("one_way_turnover must be between 0 and 1")
    if not finite_number(bps_per_side) or bps_per_side < 0:
        raise ValueError("bps_per_side must be non-negative")
    return gross_return - 2 * one_way_turnover * bps_per_side / 10_000.0


# ===== quant_research/scoring_v5.py =====
"""Python port of the fundamental-screener Strength/Risk scorer, v5.

Line-for-line faithful to ``fundamental-screener@0fa9049 lib/scoring.ts``
(SCORING_VERSION = 5) plus ``clampFraction`` from ``lib/range.ts``. The parity
test ``tests/test_scoring_v5.py`` replays the golden fixtures generated by the
TypeScript scorer (``tests/fixtures/scoring-v5-golden.json``) and requires
exactly identical output -- that is the QR-008 "frozen as-is" guarantee.

Rows are mappings with the ScanRow camelCase keys (``trailingPE``,
``fcfYieldPercent``, ...). Percent-valued inputs are percents, exactly as the
screener receives them; the QC field-mapping layer (fraction -> x100,
non-positive ratios -> None, the non-payer dividend rule, derived 5Y margin)
belongs to the QR-008 experiment adapter, not here.

Do not "fix" or tune anything in this file: any behavior change must happen in
the TypeScript scorer first, bump SCORING_VERSION, and regenerate the fixtures.
"""


import math
import re
from collections.abc import Mapping
from typing import Any

SCORING_VERSION = 5

MAX_STRENGTH = 21
MAX_RISK = 20
RISK_FLOOR = 8

MEGA_CAP_THRESHOLD = 200_000_000_000
EXTREME_DE_RATIO = 10
WEAK_INTEREST_COVERAGE = 2
STRONG_INTEREST_COVERAGE = 6

SUSPECT_REV_GROWTH_FINANCIAL = 60
SUSPECT_REV_GROWTH_GENERAL = 300

EQ_CONVERSION_STRONG = 1.0
EQ_CONVERSION_WEAK = 0.7
EQ_CONVERSION_CRITICAL = 0.5
BENIGN_EQ_MIN_FCF_YIELD = 2
BENIGN_EQ_MIN_REV_GROWTH = 20

REV_ACCEL_THRESHOLD_PP = 3
MARGIN_INFLECTION_PP = 1

MIN_CRITERION_COVERAGE = 0.7
TRAP_CHEAP_EV_EBITDA = 8
TRAP_CHEAP_FCF_YIELD = 8

# JS Number.MIN_VALUE / Number.MAX_VALUE (sanitize bounds use them as
# "strictly positive" / "any finite" limits).
_JS_MIN_VALUE = 5e-324
_JS_MAX_VALUE = 1.7976931348623157e308

CRITERION_KEYS = [
    "earningsQuality",
    "leverage",
    "revenueGrowth",
    "revenueAcceleration",
    "fcfYieldLevel",
    "marginInflection",
    "peCompression",
    "valuation",
    "dividendCoverage",
    "pricePosition",
    "ytdMomentum",
    "dividendYield",
]

CRITERION_WEIGHT = {
    "earningsQuality": 3,
    "leverage": 3,
    "revenueGrowth": 2,
    "revenueAcceleration": 2,
    "fcfYieldLevel": 2,
    "marginInflection": 2,
    "peCompression": 2,
    "valuation": 1,
    "dividendCoverage": 1,
    "pricePosition": 1,
    "ytdMomentum": 1,
    "dividendYield": 1,
}

_CYCLICAL_PATTERNS = [
    r"semiconductor",
    r"automobile", r"\bautos?\b", r"auto components",
    r"\boil\b", r"\bgas\b", r"\bcoal\b", r"petroleum", r"drilling",
    r"energy equipment", r"consumable fuels",
    r"mining", r"metals", r"\bsteel\b", r"aluminum",
    r"chemical",
    r"\bmarine\b", r"shipping",
    r"airline",
    r"construction", r"building", r"homebuild",
    r"paper", r"forest",
]
_FINANCIAL_PATTERNS = [r"financ", r"\bbank", r"insurance", r"capital markets"]
_REIT_PATTERNS = [r"\breits?\b", r"real estate"]

_OVERRIDE_BALANCE_SHEET = {"COF", "DFS", "AXP", "SYF", "ALLY"}
_OVERRIDE_ASSET_LIGHT = {
    "BLK", "TROW", "BEN",
    "CME", "ICE", "NDAQ", "CBOE",
    "SPGI", "MCO", "MSCI", "FDS", "MORN",
    "V", "MA",
}


def _matches(industry: Any, patterns: list[str]) -> bool:
    return isinstance(industry, str) and any(
        re.search(p, industry, re.IGNORECASE) for p in patterns
    )


def is_cyclical_industry(industry: Any) -> bool:
    return _matches(industry, _CYCLICAL_PATTERNS)


def is_financial_industry(industry: Any) -> bool:
    return _matches(industry, _FINANCIAL_PATTERNS)


def is_reit_industry(industry: Any) -> bool:
    return _matches(industry, _REIT_PATTERNS)


def classify_financial_model(ticker: Any, industry: Any) -> str:
    t = (ticker or "").strip().upper() if isinstance(ticker, str) else ""
    if t in _OVERRIDE_BALANCE_SHEET:
        return "balance-sheet"
    if t in _OVERRIDE_ASSET_LIGHT:
        return "asset-light"
    return "balance-sheet" if is_financial_industry(industry) else "non-financial"


def is_balance_sheet_financial(ticker: Any, industry: Any) -> bool:
    return classify_financial_model(ticker, industry) == "balance-sheet"


def _n(value: Any) -> float | int | None:
    """Finite number else None (mirrors the TS n(); booleans excluded)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if math.isfinite(value) else None


def _clamp_fraction(value: Any) -> float:
    v = _n(value)
    return 0 if v is None else min(1, max(0, v))


def _bounded(value: Any, lo: float, hi: float) -> float | int | None:
    v = _n(value)
    return v if v is not None and lo <= v <= hi else None


def _sanitize_growth_value(raw: Any, industry: Any) -> tuple[float | None, bool]:
    v = _n(raw)
    if v is None:
        return None, False
    bound = (
        SUSPECT_REV_GROWTH_FINANCIAL
        if is_financial_industry(industry)
        else SUSPECT_REV_GROWTH_GENERAL
    )
    return (None, True) if v < -100 or v > bound else (v, False)


def sanitize_revenue_growth(row: Mapping[str, Any]) -> tuple[float | None, bool]:
    return _sanitize_growth_value(row.get("revenueGrowthTTM"), row.get("industry"))


def sanitize_quarterly_rev_growth(row: Mapping[str, Any]) -> tuple[float | None, bool]:
    return _sanitize_growth_value(row.get("revenueGrowthQuarterly"), row.get("industry"))


def sanitize_score_row(row: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(row)
    out["marketCap"] = _bounded(row.get("marketCap"), _JS_MIN_VALUE, _JS_MAX_VALUE)
    out["currentPrice"] = _bounded(row.get("currentPrice"), _JS_MIN_VALUE, _JS_MAX_VALUE)
    out["trailingPE"] = _bounded(row.get("trailingPE"), _JS_MIN_VALUE, 1_000)
    out["forwardPE"] = _bounded(row.get("forwardPE"), _JS_MIN_VALUE, 1_000)
    out["dividendYieldPercent"] = _bounded(row.get("dividendYieldPercent"), 0, 25)
    out["ytdReturn"] = _bounded(row.get("ytdReturn"), -100, 1_000)
    out["fcfYieldPercent"] = _bounded(row.get("fcfYieldPercent"), -100, 100)
    out["revenueGrowthTTM"] = sanitize_revenue_growth(row)[0]
    out["revenueGrowthQuarterly"] = sanitize_quarterly_rev_growth(row)[0]
    out["evToEbitda"] = _bounded(row.get("evToEbitda"), _JS_MIN_VALUE, 1_000)
    out["interestCoverage"] = _bounded(row.get("interestCoverage"), -10_000, 10_000)
    out["operatingMarginTTM"] = _bounded(row.get("operatingMarginTTM"), -200, 100)
    out["operatingMargin5Y"] = _bounded(row.get("operatingMargin5Y"), -200, 100)
    out["rangePosition"] = _bounded(row.get("rangePosition"), 0, 1)
    return out


def compute_breakdown(input_row: Mapping[str, Any]) -> dict[str, int]:
    row = sanitize_score_row(input_row)
    pe = _n(row.get("trailingPE"))
    fwd_pe = _n(row.get("forwardPE"))
    fcf = _n(row.get("fcfYieldPercent"))
    rev_growth = sanitize_revenue_growth(row)[0]
    de = _n(row.get("debtToEquity"))
    ev_ebitda = _n(row.get("evToEbitda"))
    div_yield = _n(row.get("dividendYieldPercent"))
    ytd = _n(row.get("ytdReturn"))
    range_pos = (
        _n(_clamp_fraction(row.get("rangePosition")))
        if row.get("rangePosition") is not None
        else None
    )

    financial = is_balance_sheet_financial(row.get("ticker"), row.get("industry"))

    earnings_quality = 0
    if not financial:
        if fcf is not None and fcf < 0:
            earnings_quality = -1
        elif fcf is not None and pe is not None and pe > 0:
            conversion = (fcf * pe) / 100
            earnings_quality = (
                1 if conversion > EQ_CONVERSION_STRONG
                else -1 if conversion < EQ_CONVERSION_WEAK
                else 0
            )

    leverage = 0
    if de is not None and not financial and not is_reit_industry(row.get("industry")):
        ic = _n(row.get("interestCoverage"))
        if ic is not None and ic < WEAK_INTEREST_COVERAGE:
            leverage = -1
        elif 0 <= de <= EXTREME_DE_RATIO:
            leverage = 1 if de < 1.0 else -1 if de > 2.0 else 0

    revenue_growth = (
        (1 if rev_growth > 10 else -1 if rev_growth < 0 else 0)
        if rev_growth is not None
        else 0
    )

    rev_q = sanitize_quarterly_rev_growth(row)[0]
    revenue_acceleration = 0
    if rev_growth is not None and rev_q is not None:
        revenue_acceleration = (
            1 if rev_q > rev_growth + REV_ACCEL_THRESHOLD_PP
            else -1 if rev_q < rev_growth - REV_ACCEL_THRESHOLD_PP
            else 0
        )

    fcf_yield_level = (
        (1 if fcf > 5 else -1 if fcf < 2 else 0)
        if fcf is not None and not financial
        else 0
    )

    op_ttm = _n(row.get("operatingMarginTTM"))
    op_5y = _n(row.get("operatingMargin5Y"))
    margin_inflection = 0
    if op_ttm is not None and op_5y is not None:
        margin_inflection = (
            1 if op_ttm > op_5y + MARGIN_INFLECTION_PP
            else -1 if op_ttm < op_5y - MARGIN_INFLECTION_PP
            else 0
        )

    pe_compression = 0
    if pe is not None and fwd_pe is not None:
        pe_compression = 1 if fwd_pe < pe else -1 if fwd_pe > pe else 0
        if pe_compression == 1 and is_cyclical_industry(row.get("industry")):
            pe_compression = 0

    valuation = (
        (1 if ev_ebitda < 15 else -1 if ev_ebitda > 25 else 0)
        if ev_ebitda is not None and not financial
        else 0
    )

    dividend_coverage = 0
    if div_yield is not None and div_yield > 0 and not financial:
        if fcf is not None:
            dividend_coverage = 1 if fcf > div_yield else -1

    price_position = (
        (1 if range_pos < 0.4 else -1 if range_pos > 0.9 else 0)
        if range_pos is not None
        else 0
    )

    ytd_momentum = (1 if ytd > 0 else -1 if ytd < 0 else 0) if ytd is not None else 0

    dividend_yield = (
        (1 if div_yield > 1.5 else 0)
        if div_yield is not None and div_yield > 0
        else 0
    )

    return {
        "earningsQuality": earnings_quality,
        "leverage": leverage,
        "revenueGrowth": revenue_growth,
        "revenueAcceleration": revenue_acceleration,
        "fcfYieldLevel": fcf_yield_level,
        "marginInflection": margin_inflection,
        "peCompression": pe_compression,
        "valuation": valuation,
        "dividendCoverage": dividend_coverage,
        "pricePosition": price_position,
        "ytdMomentum": ytd_momentum,
        "dividendYield": dividend_yield,
    }


def compute_scores(breakdown: Mapping[str, int]) -> tuple[int, int]:
    strength = 0
    risk = 0
    for key in CRITERION_KEYS:
        weighted = breakdown[key] * CRITERION_WEIGHT[key]
        if weighted > 0:
            strength += weighted
        elif weighted < 0:
            risk += -weighted
    return strength, risk


def is_optically_cheap(row: Mapping[str, Any]) -> bool:
    if is_balance_sheet_financial(row.get("ticker"), row.get("industry")):
        return False
    ev = _n(row.get("evToEbitda"))
    fcf = _n(row.get("fcfYieldPercent"))
    return (ev is not None and ev < TRAP_CHEAP_EV_EBITDA) or (
        fcf is not None and fcf > TRAP_CHEAP_FCF_YIELD
    )


def is_value_trap(row: Mapping[str, Any]) -> bool:
    rev = sanitize_revenue_growth(row)[0]
    return rev is not None and rev < 0 and is_optically_cheap(row)


def is_peak_cycle(row: Mapping[str, Any]) -> bool:
    if not is_cyclical_industry(row.get("industry")):
        return False
    pe = _n(row.get("trailingPE"))
    fwd = _n(row.get("forwardPE"))
    return pe is not None and fwd is not None and fwd > pe and is_optically_cheap(row)


def compute_coverage(row: Mapping[str, Any]) -> dict[str, Any]:
    pe = _n(row.get("trailingPE"))
    fwd_pe = _n(row.get("forwardPE"))
    fcf = _n(row.get("fcfYieldPercent"))
    rev = sanitize_revenue_growth(row)[0]
    de = _n(row.get("debtToEquity"))
    ev_ebitda = _n(row.get("evToEbitda"))
    div_yield = _n(row.get("dividendYieldPercent"))
    ytd = _n(row.get("ytdReturn"))
    range_pos = (
        _n(_clamp_fraction(row.get("rangePosition")))
        if row.get("rangePosition") is not None
        else None
    )

    financial = is_balance_sheet_financial(row.get("ticker"), row.get("industry"))
    per_criterion = {
        "earningsQuality": (not financial, fcf is not None and (fcf < 0 or pe is not None)),
        "leverage": (not financial and not is_reit_industry(row.get("industry")), de is not None),
        "revenueGrowth": (True, rev is not None),
        "revenueAcceleration": (True, rev is not None and sanitize_quarterly_rev_growth(row)[0] is not None),
        "fcfYieldLevel": (not financial, fcf is not None),
        "marginInflection": (True, _n(row.get("operatingMarginTTM")) is not None and _n(row.get("operatingMargin5Y")) is not None),
        "peCompression": (True, pe is not None and fwd_pe is not None),
        "valuation": (not financial, ev_ebitda is not None),
        "dividendCoverage": (not financial, div_yield is not None and (div_yield <= 0 or fcf is not None)),
        "pricePosition": (True, range_pos is not None),
        "ytdMomentum": (True, ytd is not None),
        "dividendYield": (True, div_yield is not None),
    }

    covered = 0
    applicable = 0
    for key in CRITERION_KEYS:
        is_applicable, is_covered = per_criterion[key]
        if not is_applicable:
            continue
        applicable += 1
        if is_covered:
            covered += 1
    return {
        "covered": covered,
        "applicable": applicable,
        "fraction": 0 if applicable == 0 else covered / applicable,
    }


def has_insufficient_data(row: Mapping[str, Any], coverage: Mapping[str, Any] | None = None) -> bool:
    coverage = coverage if coverage is not None else compute_coverage(row)
    if coverage["fraction"] < MIN_CRITERION_COVERAGE:
        return True
    financial = is_balance_sheet_financial(row.get("ticker"), row.get("industry"))
    if not financial and _n(row.get("fcfYieldPercent")) is None:
        return True
    if (
        not financial
        and not is_reit_industry(row.get("industry"))
        and _n(row.get("debtToEquity")) is None
    ):
        return True
    return False


def is_benign_earnings_quality(row: Mapping[str, Any]) -> bool:
    fcf = _n(row.get("fcfYieldPercent"))
    rev = sanitize_revenue_growth(row)[0]
    return (
        fcf is not None and fcf >= BENIGN_EQ_MIN_FCF_YIELD
        and rev is not None and rev > BENIGN_EQ_MIN_REV_GROWTH
    )


def is_critical_earnings_quality(row: Mapping[str, Any]) -> bool:
    fcf = _n(row.get("fcfYieldPercent"))
    pe = _n(row.get("trailingPE"))
    if fcf is None:
        return False
    if fcf < 0:
        return True
    if pe is not None and pe > 0:
        return (fcf * pe) / 100 < EQ_CONVERSION_CRITICAL
    return False


def is_serviceable_leverage(row: Mapping[str, Any]) -> bool:
    ic = _n(row.get("interestCoverage"))
    return ic is not None and ic >= STRONG_INTEREST_COVERAGE


def is_disqualified(breakdown: Mapping[str, int], row: Mapping[str, Any]) -> bool:
    eq = (
        breakdown["earningsQuality"] == -1
        and is_critical_earnings_quality(row)
        and not is_benign_earnings_quality(row)
    )
    lev = breakdown["leverage"] == -1 and not is_serviceable_leverage(row)
    return eq or lev


def is_crowded(row: Mapping[str, Any]) -> bool:
    cap = _n(row.get("marketCap"))
    pos = _clamp_fraction(row.get("rangePosition")) if row.get("rangePosition") is not None else None
    return cap is not None and cap >= MEGA_CAP_THRESHOLD and pos is not None and pos > 0.9


def tier_for(strength_score: int, risk_score: int, flags: Mapping[str, bool]) -> str:
    if flags["disqualified"] or flags["insufficientData"] or risk_score >= RISK_FLOOR:
        return "weak"
    capped = flags["crowding"] or flags["valueTrap"] or flags["peakCycle"] or flags["softEarningsQuality"]
    if strength_score >= 12:
        return "moderate" if capped else "strong"
    if strength_score >= 7:
        return "moderate"
    return "weak"


def score_row(raw_row: Mapping[str, Any]) -> dict[str, Any]:
    """Score one row; returns the golden-fixture output shape (sans row echo)."""
    row = sanitize_score_row(raw_row)
    breakdown = compute_breakdown(row)
    strength, risk = compute_scores(breakdown)
    coverage = compute_coverage(row)
    flags = {
        "disqualified": is_disqualified(breakdown, row),
        "cyclical": is_cyclical_industry(row.get("industry")),
        "crowding": is_crowded(row),
        "benignEarningsQuality": breakdown["earningsQuality"] == -1 and is_benign_earnings_quality(row),
        # Deliberately reads the RAW row: sanitize already nulled suspect values.
        "suspectRevenueGrowth": sanitize_revenue_growth(raw_row)[1] or sanitize_quarterly_rev_growth(raw_row)[1],
        "insufficientData": has_insufficient_data(row, coverage),
        "valueTrap": is_value_trap(row),
        "peakCycle": is_peak_cycle(row),
        "serviceableLeverage": breakdown["leverage"] == -1 and is_serviceable_leverage(row),
        "softEarningsQuality": (
            breakdown["earningsQuality"] == -1
            and not is_critical_earnings_quality(row)
            and not is_benign_earnings_quality(row)
        ),
    }
    return {
        "breakdown": breakdown,
        "strengthScore": strength,
        "riskScore": risk,
        "coverage": coverage,
        "flags": flags,
        "tier": tier_for(strength, risk, flags),
    }


# ===== experiments/QR-008-strength-risk-v5/industry_map.py =====
# QR-008 industry map (preregistration precondition P-B).
#
# Maps QC MorningStar classification codes to the named buckets frozen in
# docs/preregistrations/QR-008-strength-risk-v5.md, then emits a synthetic
# label the frozen scorer's regexes classify identically:
#   financial -> "Banks"          (matches /\bbank/i)
#   REIT      -> "REIT"           (matches /\breits?\b/i)
#   cyclical  -> "Semiconductors" (matches /semiconductor/i)
#   other     -> "Diversified"    (matches nothing)
# Precedence: financial > REIT > cyclical. Ticker overrides inside
# scoring_v5 (COF/DFS/AXP/SYF/ALLY, V/MA/BLK/...) still apply on top.
#
# Buckets (from the prereg):
#   financial: Financial Services sector
#   REIT:      Real Estate sector
#   cyclical:  Basic Materials + Energy sectors (covers chemicals, metals,
#              steel, aluminum, mining, paper/forest, oil/gas/coal), plus
#              Semiconductors and Vehicles & Parts industry groups, plus
#              Airlines, Marine Shipping, Engineering & Construction, and
#              Residential Construction industries.
#
# Enum member names differ across LEAN versions, so each code resolves from
# a candidate-name list and FAILS LOUDLY at initialize if none match --
# never silently. P-B completes when this module initializes on QC and the
# smoke run logs the resolved code table (main.py logs it at start).



def _resolve(enum_cls, candidates):
    for name in candidates:
        value = getattr(enum_cls, name, None)
        if value is not None:
            return int(value)
    raise ValueError(
        f"industry_map (P-B): none of {candidates} exist on {enum_cls.__name__}; "
        "fix the candidate list against the QC datalib and rerun"
    )


SECTOR_FINANCIAL = _resolve(MorningstarSectorCode, ["FINANCIAL_SERVICES", "FinancialServices"])
SECTOR_REAL_ESTATE = _resolve(MorningstarSectorCode, ["REAL_ESTATE", "RealEstate"])

CYCLICAL_SECTORS = {
    _resolve(MorningstarSectorCode, ["BASIC_MATERIALS", "BasicMaterials"]),
    _resolve(MorningstarSectorCode, ["ENERGY", "Energy"]),
}

CYCLICAL_INDUSTRY_GROUPS = {
    _resolve(MorningstarIndustryGroupCode, ["SEMICONDUCTORS", "Semiconductors"]),
    _resolve(MorningstarIndustryGroupCode, ["VEHICLES_AND_PARTS", "VehiclesAndParts"]),
}

CYCLICAL_INDUSTRIES = {
    _resolve(MorningstarIndustryCode, ["AIRLINES", "Airlines"]),
    _resolve(MorningstarIndustryCode, ["MARINE_SHIPPING", "MarineShipping", "MARINE", "Marine"]),
    _resolve(MorningstarIndustryCode, [
        "ENGINEERING_AND_CONSTRUCTION", "EngineeringConstruction", "ENGINEERING_CONSTRUCTION",
    ]),
    _resolve(MorningstarIndustryCode, ["RESIDENTIAL_CONSTRUCTION", "ResidentialConstruction"]),
}


def resolved_codes() -> str:
    """One-line code table for the smoke-run log (P-B evidence)."""
    return (
        f"fin={SECTOR_FINANCIAL} reit={SECTOR_REAL_ESTATE} "
        f"cyc_sec={sorted(CYCLICAL_SECTORS)} cyc_grp={sorted(CYCLICAL_INDUSTRY_GROUPS)} "
        f"cyc_ind={sorted(CYCLICAL_INDUSTRIES)}"
    )


def industry_label(fundamental) -> str:
    """Synthetic industry label for scoring_v5 from MorningStar codes."""
    try:
        ac = fundamental.asset_classification
        sector = int(ac.morningstar_sector_code or 0)
        group = int(ac.morningstar_industry_group_code or 0)
        industry = int(ac.morningstar_industry_code or 0)
    except Exception:
        return "Diversified"
    if sector == SECTOR_FINANCIAL:
        return "Banks"
    if sector == SECTOR_REAL_ESTATE:
        return "REIT"
    if sector in CYCLICAL_SECTORS or group in CYCLICAL_INDUSTRY_GROUPS or industry in CYCLICAL_INDUSTRIES:
        return "Semiconductors"
    return "Diversified"


# ===== experiments/QR-008-strength-risk-v5/main.py =====
# QR-008: shipped Strength/Risk v5 composite, Strong-tier EW portfolio.
# Preregistration: docs/preregistrations/QR-008-strength-risk-v5.md.
# Do NOT run the full period until the prereg DRAFT marker is removed.
#
# QC project manifest (4 files -- see README.md in this directory):
#   main.py         this file
#   industry_map.py this directory (P-B)
#   scoring_v5.py   verbatim copy of quant_research/scoring_v5.py
#   core.py         verbatim copy of quant_research/core.py
#
# Design (frozen by the prereg):
#   - 2006-2010 warm-up accumulates the derived 5Y operating-margin baseline;
#     no books exist before 2011.
#   - Monthly: universe = top 500 by market cap, price > $5. Fundamentals are
#     mapped to the frozen scorer inputs (QR-D02/QR-D02b scales); ytd/range
#     come from a 260-bar adjusted history call ending the prior close.
#   - Synthetic books (no orders), QR-D01 accounting: candidate (all Strong-
#     tier, EW), 100 hold-random controls (seed base QR008, breadth-matched),
#     EW-universe, EW-top-100. Held names keep subscriptions via union
#     selection; each holding resolves monthly via price or terminal event;
#     an unresolved name voids that book-month (gross=None -> INVALID).
#   - Entry rule: a target with no valid price at execution is not entered
#     that month (logged); this governs entries only, never exits.
#   - Month m: turnover to[m] paid entering at step m; gross[m] realized at
#     step m+1. Primary window: months with start date in 2011-2022.
#   - Full series saved to ObjectStore key "qr008/results.json"; the Debug
#     log carries the preregistered verdict and summary tables.

# region imports
import json
import math
import pandas as pd
from random import Random

# endregion

# SMOKE = True runs only through 2011-06-30: verifies the industry map
# resolves (P-B), the field map populates, and the books rebalance. The full
# frozen run uses SMOKE = False and must not happen while the prereg is DRAFT.
SMOKE = False

EVAL_START_YEAR = 2011
PRIMARY_LAST_YEAR = 2022
TOP_N = 500
TOP_100 = 100
MIN_PRICE = 5.0
BASE_BPS = 10.0
STRESS_BPS = 20.0
N_CONTROLS = 100
SEED_BASE = "QR008"
MARGIN_MIN_OBS = 36
MARGIN_WINDOW = 60
HISTORY_BARS = 260

MISS_FIELDS = [
    "trailingPE", "forwardPE", "fcfYieldPercent", "evToEbitda",
    "revenueGrowthTTM", "revenueGrowthQuarterly", "operatingMarginTTM",
    "operatingMargin5Y", "interestCoverage", "debtToEquity",
    "ytdReturn", "rangePosition",
]

SUBPERIODS = [(2011, 2015), (2016, 2019), (2020, 2022)]


def _walk(obj, path):
    for part in path.split("."):
        obj = getattr(obj, part, None)
        if obj is None:
            return None
    if isinstance(obj, bool) or not isinstance(obj, (int, float)):
        return None
    return obj if math.isfinite(obj) else None


class QR008StrengthRiskV5(QCAlgorithm):

    def initialize(self):
        self.set_start_date(2006, 1, 1)
        if SMOKE:
            self.set_end_date(2011, 6, 30)
        else:
            self.set_end_date(2026, 6, 30)
        self.set_cash(100_000)
        self._spy = self.add_equity("SPY", Resolution.DAILY).symbol
        self.universe_settings.resolution = Resolution.DAILY
        self.add_universe(self._select)
        self.schedule.on(self.date_rules.month_start("SPY"),
                         self.time_rules.after_market_open("SPY", 90),
                         self._step)

        self._sel_month = -1
        self._universe_cache = []
        self._margins = {}            # symbol -> trailing monthly op-margin %
        self._pending = None          # symbol -> partial scorer row
        self._u_eligible = []
        self._u_top100 = []
        self._terminal = {}           # symbol -> terminal price (persistent)
        self._books = None
        self._rngs = [Random(f"{SEED_BASE}-{i}") for i in range(N_CONTROLS)]
        self._dates = []              # step dates (rebalance times)
        self._records = []            # per-step coverage/breadth/holdings
        self._spy_series = []
        self._spy_prev = None
        self._entry_skips = 0
        self.debug(f"QR-008 start; industry map codes: {resolved_codes()}")

    # ---- universe selection: monthly measurement + union retention ----

    def _select(self, fundamentals):
        if self.time.month == self._sel_month:
            return self._universe_cache
        self._sel_month = self.time.month

        rows = []
        for f in fundamentals:
            m = _walk(f, "operation_ratios.operation_margin.one_year")
            if m is not None:
                hist = self._margins.setdefault(f.symbol, [])
                hist.append(m * 100.0)
                if len(hist) > MARGIN_WINDOW:
                    del hist[0]
            p = _walk(f, "price")
            mc = _walk(f, "market_cap")
            if p is None or p <= MIN_PRICE or mc is None or mc <= 0:
                continue
            rows.append((mc, f))

        if self.time.year < EVAL_START_YEAR:
            self._universe_cache = []
            return self._universe_cache

        rows.sort(key=lambda x: x[0], reverse=True)
        top = [f for _, f in rows[:TOP_N]]
        self._u_eligible = [f.symbol for f in top]
        self._u_top100 = [f.symbol for f in top[:TOP_100]]
        self._pending = {f.symbol: self._row(f) for f in top}

        held = set()
        if self._books:
            for book in self._books.values():
                held.update(book["members"])
        self._universe_cache = self._u_eligible + [
            s for s in held if s not in set(self._u_eligible)
        ]
        return self._universe_cache

    def _row(self, f):
        def pos(path):
            v = _walk(f, path)
            return v if v is not None and v > 0 else None

        def x100(path):
            v = _walk(f, path)
            return v * 100.0 if v is not None else None

        div = x100("valuation_ratios.trailing_dividend_yield")
        margins = self._margins.get(f.symbol, [])
        return {
            "ticker": f.symbol.value,
            "industry": industry_label(f),
            "marketCap": _walk(f, "market_cap"),
            "trailingPE": pos("valuation_ratios.pe_ratio"),
            "forwardPE": pos("valuation_ratios.forward_pe_ratio"),
            "dividendYieldPercent": div if div is not None else 0.0,
            "fcfYieldPercent": x100("valuation_ratios.fcf_yield"),
            "evToEbitda": pos("valuation_ratios.ev_to_ebitda"),
            "revenueGrowthTTM": x100("operation_ratios.revenue_growth.one_year"),
            "revenueGrowthQuarterly": x100("operation_ratios.revenue_growth.three_months"),
            "operatingMarginTTM": x100("operation_ratios.operation_margin.one_year"),
            "operatingMargin5Y": (
                sum(margins) / len(margins) if len(margins) >= MARGIN_MIN_OBS else None
            ),
            "interestCoverage": _walk(f, "operation_ratios.interest_coverage.one_year"),
            "debtToEquity": _walk(f, "operation_ratios.total_debt_equity_ratio.three_months"),
            "ytdReturn": None,       # filled at the step from history
            "rangePosition": None,   # filled at the step from history
            "currentPrice": None,
        }

    # ---- terminal events (QR-D01 mechanics) ----

    def on_data(self, slice: Slice):
        for sym, d in slice.delistings.items():
            if d.type == DelistingType.WARNING:
                continue
            p = self._price(sym)
            if p is None and d.price > 0:
                p = d.price
            self._terminal[sym] = p
            self.debug(f"DELISTED {sym.value} {self.time.date()} terminal={p}")

    def _price(self, sym):
        try:
            sec = self.securities[sym]
        except Exception:
            return None
        p = sec.price
        return p if sec.has_data and isinstance(p, (int, float)) and p > 0 else None

    # ---- monthly step: resolve, score, rebalance ----

    def _step(self):
        if self.time.year < EVAL_START_YEAR or self._pending is None:
            return
        if self._books is None:
            self._init_books()

        first = not self._dates
        if not first:
            for book in self._books.values():
                self._resolve(book)
            spy_p = self._price(self._spy)
            self._spy_series.append(
                spy_p / self._spy_prev - 1
                if spy_p is not None and self._spy_prev is not None else None
            )
            if spy_p is not None:
                self._spy_prev = spy_p
        else:
            self._spy_prev = self._price(self._spy)
        self._dates.append(self.time.date().isoformat())

        strong, record = self._score_universe()
        breadth = len(strong)
        uni_sorted = sorted(self._u_eligible, key=lambda s: s.value)
        uni_set = set(uni_sorted)

        self._rebalance(self._books["cand"], sorted(strong, key=lambda s: s.value))
        self._rebalance(self._books["ew_univ"], uni_sorted)
        self._rebalance(self._books["ew_top100"],
                        sorted(self._u_top100, key=lambda s: s.value))
        for i in range(N_CONTROLS):
            book = self._books[f"c{i:02d}"]
            self._rebalance(book, self._control_targets(i, book, uni_sorted, uni_set, breadth))

        record["d"] = self._dates[-1]
        record["skips_cum"] = self._entry_skips
        self._records.append(record)
        if self.time.month == 1:
            cand = self._books["cand"]
            self.debug(f"HB {self._dates[-1]} months={len(cand['gross'])} "
                       f"breadth={breadth} invalid={cand['invalid']} "
                       f"skips={self._entry_skips}")

    def _score_universe(self):
        stats = self._price_stats(self._u_eligible)
        strong = []
        miss = {k: 0 for k in MISS_FIELDS}
        n_insufficient = 0
        n_suspect = 0
        cand_industries = {}
        for sym in self._u_eligible:
            row = self._pending.get(sym)
            if row is None:
                continue
            row["ytdReturn"], row["rangePosition"] = stats.get(sym, (None, None))
            for k in MISS_FIELDS:
                if row.get(k) is None:
                    miss[k] += 1
            scored = score_row(row)
            if scored["flags"]["insufficientData"]:
                n_insufficient += 1
            if scored["flags"]["suspectRevenueGrowth"]:
                n_suspect += 1
            if scored["tier"] == "strong":
                strong.append(sym)
                bucket = row["industry"]
                cand_industries[bucket] = cand_industries.get(bucket, 0) + 1
        record = {
            "breadth": len(strong),
            "insufficient": n_insufficient,
            "suspect": n_suspect,
            "miss": miss,
            "cand": sorted(s.value for s in strong),
            "cand_buckets": cand_industries,
        }
        return strong, record

    def _price_stats(self, symbols):
        """(ytdReturn %, rangePosition) per symbol from adjusted daily closes
        ending at the prior close (point-in-time at execution)."""
        out = {s: (None, None) for s in symbols}
        try:
            df = self.history(list(symbols), HISTORY_BARS, Resolution.DAILY)
        except Exception as err:
            self.debug(f"HISTORY-ERR {self.time.date()} {err}")
            return out
        if df is None or len(df) == 0 or "close" not in df:
            return out
        closes = df["close"]
        year = self.time.year
        for sym in symbols:
            try:
                series = closes.loc[sym]
            except Exception:
                continue
            if not hasattr(series, "values") or len(series) == 0:
                continue
            values = [float(v) for v in series.values]
            last = values[-1]
            window = values[-252:]
            low, high = min(window), max(window)
            range_pos = (last - low) / (high - low) if high > low else None
            base = None
            for stamp, value in zip(series.index, values):
                # Daily bars are stamped at end time (next midnight); the
                # close's calendar day is one tick earlier.
                if (stamp - pd.Timedelta(seconds=1)).year < year:
                    base = float(value)
                else:
                    break
            ytd = (last / base - 1) * 100.0 if base is not None and base > 0 else None
            out[sym] = (ytd, range_pos)
        return out

    # ---- synthetic books ----

    def _init_books(self):
        def book():
            return {"members": [], "entry": {}, "gross": [], "to": [], "invalid": 0}

        self._books = {"cand": book(), "ew_univ": book(), "ew_top100": book()}
        for i in range(N_CONTROLS):
            self._books[f"c{i:02d}"] = book()

    def _resolve(self, book):
        if not book["members"]:
            book["gross"].append(0.0)
            return
        rets = []
        for sym in book["members"]:
            p = self._price(sym)
            if p is None:
                p = self._terminal.get(sym)
            if p is None:
                book["invalid"] += 1
                book["gross"].append(None)
                self.debug(f"UNRESOLVED {sym.value} {self.time.date()}")
                return
            rets.append(p / book["entry"][sym] - 1)
        book["gross"].append(sum(rets) / len(rets))

    def _rebalance(self, book, targets):
        entered = []
        entry = {}
        for sym in targets:
            p = self._price(sym)
            if p is None:
                self._entry_skips += 1
                continue
            entered.append(sym)
            entry[sym] = p
        book["to"].append(equal_weight_turnover(book["members"], entered))
        book["members"] = entered
        book["entry"] = entry

    def _control_targets(self, i, book, uni_sorted, uni_set, breadth):
        rng = self._rngs[i]
        kept = [s for s in book["members"] if s in uni_set]
        if len(kept) > breadth:
            kept = rng.sample(kept, breadth)
        elif len(kept) < breadth:
            kept_set = set(kept)
            pool = [s for s in uni_sorted if s not in kept_set]
            need = min(breadth - len(kept), len(pool))
            kept = kept + rng.sample(pool, need)
        return kept

    # ---- verdict ----

    def _net(self, book, bps):
        return [
            apply_cost(g, book["to"][m], bps) if g is not None else None
            for m, g in enumerate(book["gross"])
        ]

    def on_end_of_algorithm(self):
        if not self._books or not self._books["cand"]["gross"]:
            self.debug("QR-008: no evaluated months; nothing to report")
            return
        n_months = len(self._books["cand"]["gross"])
        month_year = [int(d[:4]) for d in self._dates[:n_months]]

        def sliced(series, lo, hi):
            return [series[m] for m in range(n_months) if lo <= month_year[m] <= hi]

        def stats_line(name, series, lo, hi):
            part = sliced(series, lo, hi)
            if any(v is None for v in part):
                return f"{name} {lo}-{hi}: INVALID ({sum(1 for v in part if v is None)} void months)"
            if len(part) < 2:
                return f"{name} {lo}-{hi}: <2 months"
            st = return_stats(part, 12)
            return (f"{name} {lo}-{hi}: sharpe={st.sharpe:.3f} cagr={st.cagr:.2%} "
                    f"mdd={st.max_drawdown:.2%} n={st.observations}")

        cand_net = self._net(self._books["cand"], BASE_BPS)
        cand_stress = self._net(self._books["cand"], STRESS_BPS)
        ew100_net = self._net(self._books["ew_top100"], BASE_BPS)
        ewu_net = self._net(self._books["ew_univ"], BASE_BPS)

        lo, hi = EVAL_START_YEAR, PRIMARY_LAST_YEAR
        primary_cand = sliced(cand_net, lo, hi)
        verdict = "INVALID"
        detail = ""
        if not any(v is None for v in primary_cand) and len(primary_cand) >= 2:
            cand_sharpe = return_stats(primary_cand, 12).sharpe
            ew100_part = sliced(ew100_net, lo, hi)
            if any(v is None for v in ew100_part):
                detail = "EW-top-100 has void months"
            else:
                ew100_sharpe = return_stats(ew100_part, 12).sharpe
                ctrl_sharpes = []
                dropped = 0
                for i in range(N_CONTROLS):
                    part = sliced(self._net(self._books[f"c{i:02d}"], BASE_BPS), lo, hi)
                    if any(v is None for v in part):
                        dropped += 1
                        continue
                    ctrl_sharpes.append(return_stats(part, 12).sharpe)
                if not ctrl_sharpes:
                    detail = "all controls void"
                else:
                    p75 = percentile(ctrl_sharpes, 75)
                    passed = cand_sharpe > p75 and cand_sharpe > ew100_sharpe
                    verdict = "PASS" if passed else "FAIL"
                    detail = (f"cand={cand_sharpe:.3f} ctrl_p75={p75:.3f} "
                              f"ew100={ew100_sharpe:.3f} ctrl_dropped={dropped}")
        else:
            detail = f"candidate has {sum(1 for v in primary_cand if v is None)} void months"

        self.debug(f"PRIMARY VERDICT: {verdict} ({detail})")
        self.debug(stats_line("CAND-net", cand_net, lo, hi))
        self.debug(stats_line("CAND-2xcost", cand_stress, lo, hi))
        self.debug(stats_line("EW100-net", ew100_net, lo, hi))
        self.debug(stats_line("EWUNIV-net", ewu_net, lo, hi))
        self.debug(stats_line("SPY", self._spy_series, lo, hi))
        for sub_lo, sub_hi in SUBPERIODS:
            self.debug(stats_line("CAND-net", cand_net, sub_lo, sub_hi))
        self.debug(stats_line("CAND-net OOS", cand_net, 2023, 2026))
        self.debug(stats_line("EW100-net OOS", ew100_net, 2023, 2026))
        self.debug(stats_line("SPY OOS", self._spy_series, 2023, 2026))

        for year in range(EVAL_START_YEAR, month_year[-1] + 1):
            def yr(series):
                part = sliced(series, year, year)
                if not part or any(v is None for v in part):
                    return "na"
                total = 1.0
                for v in part:
                    total *= 1 + v
                return f"{total - 1:.1%}"
            breadths = [r["breadth"] for r, y in zip(self._records, month_year) if y == year]
            avg_b = sum(breadths) / len(breadths) if breadths else 0
            self.debug(f"YR {year} cand={yr(cand_net)} ew100={yr(ew100_net)} "
                       f"ewu={yr(ewu_net)} spy={yr(self._spy_series)} breadth~{avg_b:.0f}")

        payload = {
            "experiment": "QR-008",
            "scoring_version": 5,
            "seed_base": SEED_BASE,
            "base_bps": BASE_BPS,
            "dates": self._dates,
            "spy": self._spy_series,
            "books": {
                name: {"gross": b["gross"], "to": b["to"], "invalid": b["invalid"]}
                for name, b in self._books.items()
            },
            "records": self._records,
            "entry_skips": self._entry_skips,
        }
        self.object_store.save("qr008/results.json", json.dumps(payload))
        self.debug("QR-008 series saved to ObjectStore key qr008/results.json; "
                   "record the backtest ID in docs/ledger.md")
