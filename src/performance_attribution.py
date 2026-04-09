"""Brinson-Fachler performance attribution model."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .data import SP500_SECTOR_WEIGHTS


@dataclass
class AttributionResult:
    """Single-period Brinson-Fachler attribution output."""
    sectors: list[dict]
    total_allocation: float
    total_selection: float
    total_interaction: float
    active_return: float
    portfolio_return: float
    benchmark_return: float


@dataclass
class CumulativeAttribution:
    """Multi-period cumulative attribution."""
    periods: list[dict]    # per-period attribution summaries
    cumulative: dict       # cumulative totals


def _sector_level_data(
    holdings_weights: dict[str, float],
    returns: pd.DataFrame,
    sector_map: dict[str, str],
    period_start: str | None = None,
    period_end: str | None = None,
) -> dict[str, dict]:
    """Compute sector-level weights and returns for the portfolio."""
    ret_slice = returns
    if period_start:
        ret_slice = ret_slice.loc[period_start:]
    if period_end:
        ret_slice = ret_slice.loc[:period_end]

    # Cumulative return over the period for each holding
    cum_returns = {}
    for ticker in holdings_weights:
        if ticker in ret_slice.columns:
            cum_returns[ticker] = float((1 + ret_slice[ticker]).prod() - 1)
        else:
            cum_returns[ticker] = 0.0

    # Aggregate by sector
    sectors: dict[str, dict] = {}
    for ticker, weight in holdings_weights.items():
        sector = sector_map.get(ticker, "Unknown")
        if sector not in sectors:
            sectors[sector] = {"weight": 0.0, "weighted_return": 0.0}
        sectors[sector]["weight"] += weight
        sectors[sector]["weighted_return"] += weight * cum_returns.get(ticker, 0.0)

    # Compute sector return = weighted_return / weight
    for sector in sectors:
        w = sectors[sector]["weight"]
        sectors[sector]["return"] = (
            sectors[sector]["weighted_return"] / w if w > 0 else 0.0
        )

    return sectors


def brinson_fachler(
    holdings_weights: dict[str, float],
    returns: pd.DataFrame,
    sector_map: dict[str, str],
    benchmark_returns: pd.Series,
    benchmark_sector_weights: dict[str, float] | None = None,
    benchmark_sector_returns: dict[str, float] | None = None,
) -> AttributionResult:
    """Single-period Brinson-Fachler attribution vs benchmark."""
    if benchmark_sector_weights is None:
        benchmark_sector_weights = SP500_SECTOR_WEIGHTS

    # Portfolio sector data
    port_sectors = _sector_level_data(holdings_weights, returns, sector_map)

    # Portfolio total return
    port_return = sum(
        holdings_weights[t] * float((1 + returns[t]).prod() - 1)
        for t in holdings_weights if t in returns.columns
    )

    # Benchmark total return
    bench_return = float((1 + benchmark_returns).prod() - 1)

    # If benchmark sector returns not provided, estimate proportionally
    if benchmark_sector_returns is None:
        benchmark_sector_returns = {
            s: bench_return for s in benchmark_sector_weights
        }

    # All sectors (union of portfolio and benchmark)
    all_sectors = set(port_sectors.keys()) | set(benchmark_sector_weights.keys())

    sector_results = []
    total_allocation = 0.0
    total_selection = 0.0
    total_interaction = 0.0

    for sector in sorted(all_sectors):
        w_p = port_sectors.get(sector, {}).get("weight", 0.0)
        r_p = port_sectors.get(sector, {}).get("return", 0.0)
        w_b = benchmark_sector_weights.get(sector, 0.0)
        r_b = benchmark_sector_returns.get(sector, bench_return)

        # Brinson-Fachler effects
        allocation = (w_p - w_b) * (r_b - bench_return)
        selection = w_b * (r_p - r_b)
        interaction = (w_p - w_b) * (r_p - r_b)

        total_allocation += allocation
        total_selection += selection
        total_interaction += interaction

        sector_results.append({
            "sector": sector,
            "portfolio_weight": round(w_p * 100, 2),
            "benchmark_weight": round(w_b * 100, 2),
            "portfolio_return": round(r_p * 100, 4),
            "benchmark_return": round(r_b * 100, 4),
            "allocation_effect": round(allocation * 100, 4),
            "selection_effect": round(selection * 100, 4),
            "interaction_effect": round(interaction * 100, 4),
        })

    active_return = port_return - bench_return

    return AttributionResult(
        sectors=sector_results,
        total_allocation=round(total_allocation * 100, 4),
        total_selection=round(total_selection * 100, 4),
        total_interaction=round(total_interaction * 100, 4),
        active_return=round(active_return * 100, 4),
        portfolio_return=round(port_return * 100, 4),
        benchmark_return=round(bench_return * 100, 4),
    )


def brinson_fachler_multiperiod(
    holdings_weights: dict[str, float],
    returns: pd.DataFrame,
    sector_map: dict[str, str],
    benchmark_returns: pd.Series,
    frequency: str = "M",
    benchmark_sector_weights: dict[str, float] | None = None,
) -> CumulativeAttribution:
    """Multi-period Brinson attribution with arithmetic linking."""
    if benchmark_sector_weights is None:
        benchmark_sector_weights = SP500_SECTOR_WEIGHTS

    # Group returns by period
    periods_idx = returns.resample(frequency).last().index
    period_results = []

    cum_allocation = 0.0
    cum_selection = 0.0
    cum_interaction = 0.0
    cum_active = 0.0

    prev_end = None
    for period_end in periods_idx:
        period_start = prev_end
        if period_start is not None:
            mask = (returns.index > period_start) & (returns.index <= period_end)
        else:
            mask = returns.index <= period_end
        period_returns = returns.loc[mask]
        bench_period = benchmark_returns.loc[mask] if not benchmark_returns.empty else benchmark_returns

        if period_returns.empty:
            prev_end = period_end
            continue

        # Single-period attribution for this sub-period
        port_sects = {}
        for ticker, weight in holdings_weights.items():
            if ticker in period_returns.columns:
                sector = sector_map.get(ticker, "Unknown")
                if sector not in port_sects:
                    port_sects[sector] = {"weight": 0.0, "weighted_return": 0.0}
                r = float((1 + period_returns[ticker]).prod() - 1)
                port_sects[sector]["weight"] += weight
                port_sects[sector]["weighted_return"] += weight * r

        port_ret = sum(
            holdings_weights[t] * float((1 + period_returns[t]).prod() - 1)
            for t in holdings_weights if t in period_returns.columns
        )
        bench_ret = float((1 + bench_period).prod() - 1) if not bench_period.empty else 0.0

        # Simple allocation/selection for the period
        alloc = 0.0
        selec = 0.0
        inter = 0.0
        for sector in set(list(port_sects.keys()) + list(benchmark_sector_weights.keys())):
            w_p = port_sects.get(sector, {}).get("weight", 0.0)
            w_b = benchmark_sector_weights.get(sector, 0.0)
            ps = port_sects.get(sector, {})
            r_p = ps.get("weighted_return", 0.0) / ps["weight"] if ps.get("weight", 0) > 0 else 0.0
            r_b = bench_ret  # simplified

            alloc += (w_p - w_b) * (r_b - bench_ret)
            selec += w_b * (r_p - r_b)
            inter += (w_p - w_b) * (r_p - r_b)

        cum_allocation += alloc
        cum_selection += selec
        cum_interaction += inter
        cum_active += port_ret - bench_ret

        period_results.append({
            "period": period_end.strftime("%Y-%m"),
            "portfolio_return": round(port_ret * 100, 4),
            "benchmark_return": round(bench_ret * 100, 4),
            "active_return": round((port_ret - bench_ret) * 100, 4),
            "allocation": round(alloc * 100, 4),
            "selection": round(selec * 100, 4),
            "interaction": round(inter * 100, 4),
            "cumulative_allocation": round(cum_allocation * 100, 4),
            "cumulative_selection": round(cum_selection * 100, 4),
            "cumulative_interaction": round(cum_interaction * 100, 4),
            "cumulative_active": round(cum_active * 100, 4),
        })

        prev_end = period_end

    return CumulativeAttribution(
        periods=period_results,
        cumulative={
            "allocation": round(cum_allocation * 100, 4),
            "selection": round(cum_selection * 100, 4),
            "interaction": round(cum_interaction * 100, 4),
            "active_return": round(cum_active * 100, 4),
        },
    )
