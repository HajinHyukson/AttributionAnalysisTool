"""Attribution Analysis Tool — Typer CLI entry point."""
from __future__ import annotations

import json
import logging
import sys
from dataclasses import asdict
from typing import Optional

import typer

app = typer.Typer(
    name="aat",
    help="Attribution Analysis Tool — Portfolio risk analytics CLI",
)


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )


def _output_json(data: dict) -> None:
    """Print JSON result to stdout for Java to consume."""
    print(json.dumps(data, default=str))


def _load_common(portfolio: str, years: int, benchmark: str, cache: bool):
    """Shared setup: parse portfolio, fetch data."""
    from .config import get_settings
    from .data import (
        compute_returns,
        fetch_benchmark_prices,
        fetch_price_matrix,
        fetch_sector_map,
        parse_portfolio,
    )
    from .fmp_client import FMPClient

    settings = get_settings()
    client = FMPClient(settings, cache_enabled=cache)
    weights = parse_portfolio(portfolio)
    tickers = list(weights.keys())

    prices = fetch_price_matrix(tickers, years, client)
    returns = compute_returns(prices)
    sector_map = fetch_sector_map(tickers, client)

    bench_prices = fetch_benchmark_prices(benchmark, years, client)
    # Align benchmark to portfolio dates
    common_idx = returns.index.intersection(bench_prices.index)
    bench_returns = bench_prices.loc[common_idx].pct_change().dropna()
    returns = returns.loc[returns.index.intersection(bench_returns.index)]
    bench_returns = bench_returns.loc[bench_returns.index.intersection(returns.index)]

    return weights, tickers, prices, returns, sector_map, bench_returns, client


@app.command()
def risk_attribution(
    portfolio: str = typer.Option(..., help="Holdings as 'AAPL:0.3,MSFT:0.25,...'"),
    years: int = typer.Option(3, help="Years of historical data"),
    n_factors: int = typer.Option(3, help="Number of PCA factors"),
    benchmark: str = typer.Option("SPY", help="Benchmark ticker"),
    cache: bool = typer.Option(True, help="Enable FMP cache"),
    log_level: str = typer.Option("INFO", help="Log level"),
):
    """Factor-based risk decomposition."""
    _setup_logging(log_level)
    from .data import parse_portfolio
    from .risk_attribution import decompose_risk, estimate_factor_model_pca

    weights_dict, tickers, prices, returns, sector_map, _, _ = _load_common(
        portfolio, years, benchmark, cache
    )

    import numpy as np
    w = np.array([weights_dict.get(t, 0.0) for t in returns.columns])
    # Normalize weights to sum to 1
    w_sum = w.sum()
    if w_sum > 0:
        w = w / w_sum

    factor_model = estimate_factor_model_pca(returns, n_factors=n_factors)
    result = decompose_risk(w, returns, factor_model, sector_map)

    _output_json(asdict(result))


@app.command()
def performance_attribution(
    portfolio: str = typer.Option(..., help="Holdings as 'AAPL:0.3,MSFT:0.25,...'"),
    years: int = typer.Option(3, help="Years of historical data"),
    benchmark: str = typer.Option("SPY", help="Benchmark ticker"),
    period: str = typer.Option("full", help="Period: full, 1Y, YTD"),
    cache: bool = typer.Option(True, help="Enable FMP cache"),
    log_level: str = typer.Option("INFO", help="Log level"),
):
    """Brinson-Fachler performance attribution vs benchmark."""
    _setup_logging(log_level)
    from .performance_attribution import brinson_fachler, brinson_fachler_multiperiod

    weights_dict, tickers, prices, returns, sector_map, bench_returns, _ = _load_common(
        portfolio, years, benchmark, cache
    )

    # Single-period attribution
    single = brinson_fachler(weights_dict, returns, sector_map, bench_returns)

    # Multi-period attribution (monthly)
    multi = brinson_fachler_multiperiod(
        weights_dict, returns, sector_map, bench_returns, frequency="ME"
    )

    _output_json({
        "single_period": asdict(single),
        "multi_period": asdict(multi),
    })


@app.command()
def stress_test(
    portfolio: str = typer.Option(..., help="Holdings as 'AAPL:0.3,MSFT:0.25,...'"),
    years: int = typer.Option(5, help="Years of historical data (need more for older scenarios)"),
    scenarios: str = typer.Option(
        "GFC_2008,COVID_2020,RATE_HIKES_2022",
        help="Comma-separated scenario names",
    ),
    benchmark: str = typer.Option("SPY", help="Benchmark ticker"),
    cache: bool = typer.Option(True, help="Enable FMP cache"),
    log_level: str = typer.Option("INFO", help="Log level"),
):
    """Run historical stress scenarios on the portfolio."""
    _setup_logging(log_level)
    import numpy as np
    from .data import parse_portfolio
    from .risk_attribution import estimate_factor_model_pca
    from .stress_testing import (
        reverse_stress_test,
        run_historical_scenario,
    )

    weights_dict, tickers, prices, returns, sector_map, _, _ = _load_common(
        portfolio, years, benchmark, cache
    )

    # Run historical scenarios
    scenario_names = [s.strip() for s in scenarios.split(",") if s.strip()]
    scenario_results = []
    for name in scenario_names:
        result = run_historical_scenario(prices, weights_dict, name)
        scenario_results.append(asdict(result))

    # Factor model for reverse stress test
    w = np.array([weights_dict.get(t, 0.0) for t in returns.columns])
    w_sum = w.sum()
    if w_sum > 0:
        w = w / w_sum

    factor_model = estimate_factor_model_pca(returns, n_factors=3)
    factor_betas = {}
    for i, ticker in enumerate(returns.columns):
        factor_betas[ticker] = {
            fname: float(factor_model.betas.iloc[i, j])
            for j, fname in enumerate(factor_model.factor_names)
        }

    reverse = reverse_stress_test(factor_betas, weights_dict, target_loss=0.10)

    _output_json({
        "scenarios": scenario_results,
        "reverse_stress": asdict(reverse),
    })


@app.command()
def correlation_regime(
    portfolio: str = typer.Option(..., help="Holdings as 'AAPL:0.3,MSFT:0.25,...'"),
    years: int = typer.Option(3, help="Years of historical data"),
    window: int = typer.Option(60, help="Rolling window size in days"),
    benchmark: str = typer.Option("SPY", help="Benchmark ticker"),
    cache: bool = typer.Option(True, help="Enable FMP cache"),
    log_level: str = typer.Option("INFO", help="Log level"),
):
    """Rolling correlation analysis and regime detection."""
    _setup_logging(log_level)
    from .correlation_regime import rolling_correlation_analysis

    weights_dict, tickers, prices, returns, sector_map, _, _ = _load_common(
        portfolio, years, benchmark, cache
    )

    result = rolling_correlation_analysis(returns, weights_dict, window=window)
    _output_json(asdict(result))


if __name__ == "__main__":
    app()
