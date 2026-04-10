"""Correlation regime monitoring: rolling correlations, diversification ratio, regime detection."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class CorrelationSnapshot:
    """A single point-in-time correlation matrix."""
    date: str
    matrix: list[list[float]]
    tickers: list[str]
    avg_correlation: float


@dataclass
class RegimeAlert:
    """Alert when correlation regime changes."""
    date: str
    avg_correlation: float
    z_score: float
    level: str  # "warning" or "critical"


@dataclass
class CorrelationRegimeResult:
    """Full correlation regime analysis output."""
    current_matrix: list[list[float]]
    tickers: list[str]
    current_avg_correlation: float
    rolling_avg_correlation: list[dict]  # date, value
    diversification_ratio: list[dict]    # date, value
    pc1_variance_explained: list[dict]   # date, value
    alerts: list[dict]


def rolling_correlation_analysis(
    returns: pd.DataFrame,
    weights: dict[str, float],
    window: int = 60,
) -> CorrelationRegimeResult:
    """Compute rolling correlation analysis with regime detection."""
    tickers = list(returns.columns)
    n_assets = len(tickers)
    w = np.array([weights.get(t, 0.0) for t in tickers])

    # Current correlation matrix (full sample)
    current_corr = returns.corr().values.copy()
    np.fill_diagonal(current_corr, 1.0)

    # Extract upper triangle for average
    mask = np.triu(np.ones((n_assets, n_assets), dtype=bool), k=1)
    current_avg = float(np.mean(current_corr[mask])) if n_assets > 1 else 0.0

    # Rolling analysis
    rolling_avg_corr: list[dict] = []
    div_ratio_series: list[dict] = []
    pc1_series: list[dict] = []

    # Sample every 5 trading days to keep output manageable
    indices = list(range(window, len(returns) + 1, 5))
    if indices and indices[-1] != len(returns):
        indices.append(len(returns))

    for end_idx in indices:
        window_returns = returns.iloc[end_idx - window:end_idx]
        dt = returns.index[end_idx - 1]
        date_str = dt.strftime("%Y-%m-%d") if hasattr(dt, "strftime") else str(dt)

        # Correlation matrix for this window
        corr = window_returns.corr().values.copy()
        np.fill_diagonal(corr, 1.0)

        # Average pairwise correlation
        avg_corr = float(np.mean(corr[mask])) if n_assets > 1 else 0.0
        rolling_avg_corr.append({"date": date_str, "value": round(avg_corr, 4)})

        # Diversification ratio: DR = (w' * sigma) / sigma_p
        vols = window_returns.std().values
        cov = window_returns.cov().values
        weighted_avg_vol = float(w @ vols)
        port_var = float(w @ cov @ w)
        port_vol = float(np.sqrt(max(port_var, 0)))
        dr = weighted_avg_vol / port_vol if port_vol > 0 else 1.0
        div_ratio_series.append({"date": date_str, "value": round(dr, 4)})

        # PCA concentration: % variance explained by PC1
        eigenvalues = np.linalg.eigvalsh(cov)
        eigenvalues = np.clip(eigenvalues, 0, None)
        total_eigenval = float(np.sum(eigenvalues))
        pc1_pct = float(np.max(eigenvalues)) / total_eigenval * 100 if total_eigenval > 0 else 0.0
        pc1_series.append({"date": date_str, "value": round(pc1_pct, 2)})

    # Regime detection: z-score on rolling average correlation
    if len(rolling_avg_corr) > 20:
        avg_values = np.array([r["value"] for r in rolling_avg_corr])
        rolling_mean = pd.Series(avg_values).rolling(window=min(60, len(avg_values))).mean().values
        rolling_std = pd.Series(avg_values).rolling(window=min(60, len(avg_values))).std().values

        alerts: list[dict] = []
        for i in range(len(rolling_avg_corr)):
            if np.isnan(rolling_mean[i]) or np.isnan(rolling_std[i]) or rolling_std[i] < 0.001:
                continue
            z = (avg_values[i] - rolling_mean[i]) / rolling_std[i]
            if abs(z) > 2.5:
                alerts.append({
                    "date": rolling_avg_corr[i]["date"],
                    "avg_correlation": rolling_avg_corr[i]["value"],
                    "z_score": round(float(z), 2),
                    "level": "critical",
                })
            elif abs(z) > 2.0:
                alerts.append({
                    "date": rolling_avg_corr[i]["date"],
                    "avg_correlation": rolling_avg_corr[i]["value"],
                    "z_score": round(float(z), 2),
                    "level": "warning",
                })
    else:
        alerts = []

    return CorrelationRegimeResult(
        current_matrix=[[round(float(current_corr[i][j]), 4) for j in range(n_assets)] for i in range(n_assets)],
        tickers=tickers,
        current_avg_correlation=round(current_avg, 4),
        rolling_avg_correlation=rolling_avg_corr,
        diversification_ratio=div_ratio_series,
        pc1_variance_explained=pc1_series,
        alerts=alerts,
    )
