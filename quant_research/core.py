"""Deterministic, QC-independent helpers for quant research experiments."""

from __future__ import annotations

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
