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

from AlgorithmImports import *


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
