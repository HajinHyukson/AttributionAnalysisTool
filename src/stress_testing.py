"""Stress testing: historical scenarios, custom shocks, and reverse stress tests."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd


# Historical scenario date ranges
SCENARIOS: dict[str, dict] = {
    "GFC_2008": {
        "label": "Global Financial Crisis",
        "start": "2008-09-01",
        "end": "2009-03-31",
        "description": "Lehman collapse through market bottom",
    },
    "COVID_2020": {
        "label": "COVID-19 Crash",
        "start": "2020-02-19",
        "end": "2020-03-23",
        "description": "Pre-COVID peak to COVID trough",
    },
    "RATE_HIKES_2022": {
        "label": "2022 Rate Hikes",
        "start": "2022-01-03",
        "end": "2022-10-12",
        "description": "Fed tightening cycle peak-to-trough",
    },
    "TAPER_TANTRUM_2013": {
        "label": "Taper Tantrum",
        "start": "2013-05-22",
        "end": "2013-09-05",
        "description": "Bernanke taper signal to stabilization",
    },
    "DOT_COM_2000": {
        "label": "Dot-Com Bust",
        "start": "2000-03-10",
        "end": "2002-10-09",
        "description": "Tech bubble peak to market bottom",
    },
}


@dataclass
class ScenarioResult:
    """Result of applying a historical stress scenario."""
    name: str
    label: str
    description: str
    start: str
    end: str
    total_pnl_pct: float
    holdings: list[dict]
    data_available: bool


@dataclass
class CustomShockResult:
    """Result of applying custom factor shocks."""
    total_impact_pct: float
    holdings: list[dict]
    shocks_applied: dict[str, float]


@dataclass
class ReverseStressResult:
    """Result of reverse stress test."""
    target_loss_pct: float
    required_market_shock_pct: float


def run_historical_scenario(
    prices: pd.DataFrame,
    weights: dict[str, float],
    scenario_name: str,
) -> ScenarioResult:
    """Apply a historical stress scenario to the portfolio."""
    if scenario_name not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_name}. Available: {list(SCENARIOS.keys())}")

    scenario = SCENARIOS[scenario_name]
    start = scenario["start"]
    end = scenario["end"]

    # Slice prices to scenario window
    mask = (prices.index >= start) & (prices.index <= end)
    scenario_prices = prices.loc[mask]

    if scenario_prices.empty or len(scenario_prices) < 2:
        # Data doesn't cover this period
        return ScenarioResult(
            name=scenario_name,
            label=scenario["label"],
            description=scenario["description"],
            start=start,
            end=end,
            total_pnl_pct=0.0,
            holdings=[],
            data_available=False,
        )

    # Compute returns over the scenario period
    start_prices = scenario_prices.iloc[0]
    end_prices = scenario_prices.iloc[-1]

    holdings_results = []
    total_pnl = 0.0

    for ticker, weight in weights.items():
        if ticker not in scenario_prices.columns:
            holdings_results.append({
                "ticker": ticker,
                "weight": round(weight * 100, 2),
                "return_pct": 0.0,
                "pnl_contribution_pct": 0.0,
                "data_available": False,
            })
            continue

        p_start = float(start_prices[ticker])
        p_end = float(end_prices[ticker])
        if p_start > 0:
            ret = (p_end - p_start) / p_start
        else:
            ret = 0.0

        pnl_contrib = weight * ret
        total_pnl += pnl_contrib

        holdings_results.append({
            "ticker": ticker,
            "weight": round(weight * 100, 2),
            "return_pct": round(ret * 100, 2),
            "pnl_contribution_pct": round(pnl_contrib * 100, 2),
            "data_available": True,
        })

    return ScenarioResult(
        name=scenario_name,
        label=scenario["label"],
        description=scenario["description"],
        start=start,
        end=end,
        total_pnl_pct=round(total_pnl * 100, 2),
        holdings=holdings_results,
        data_available=True,
    )


def run_custom_shock(
    factor_betas: dict[str, dict[str, float]],
    weights: dict[str, float],
    shocks: dict[str, float],
) -> CustomShockResult:
    """Apply custom factor shocks using portfolio factor betas.

    shocks: e.g. {"PC1": -0.20, "PC2": 0.05}
    """
    holdings_results = []
    total_impact = 0.0

    for ticker, weight in weights.items():
        betas = factor_betas.get(ticker, {})
        impact = sum(betas.get(factor, 0.0) * shock for factor, shock in shocks.items())
        weighted_impact = weight * impact
        total_impact += weighted_impact

        holdings_results.append({
            "ticker": ticker,
            "weight": round(weight * 100, 2),
            "impact_pct": round(impact * 100, 4),
            "weighted_impact_pct": round(weighted_impact * 100, 4),
        })

    return CustomShockResult(
        total_impact_pct=round(total_impact * 100, 4),
        holdings=holdings_results,
        shocks_applied={k: round(v * 100, 2) for k, v in shocks.items()},
    )


def reverse_stress_test(
    factor_betas: dict[str, dict[str, float]],
    weights: dict[str, float],
    target_loss: float = 0.10,
    primary_factor: str = "PC1",
) -> ReverseStressResult:
    """Find the market shock magnitude that produces a target portfolio loss.

    Uses binary search on the primary factor (typically market/PC1).
    """
    lo, hi = 0.0, 1.0  # shock magnitude range (0% to 100%)

    for _ in range(50):  # binary search iterations
        mid = (lo + hi) / 2.0
        shocks = {primary_factor: -mid}
        result = run_custom_shock(factor_betas, weights, shocks)
        loss = -result.total_impact_pct / 100.0

        if abs(loss - target_loss) < 0.0001:
            break
        if loss < target_loss:
            lo = mid
        else:
            hi = mid

    required_shock = (lo + hi) / 2.0

    return ReverseStressResult(
        target_loss_pct=round(target_loss * 100, 2),
        required_market_shock_pct=round(required_shock * 100, 2),
    )
