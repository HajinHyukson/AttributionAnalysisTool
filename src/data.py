from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

from .errors import DataError
from .fmp_client import FMPClient

logger = logging.getLogger(__name__)


def parse_portfolio(raw: str) -> dict[str, float]:
    """Parse 'AAPL:0.30,MSFT:0.25,...' into a weights dict."""
    holdings: dict[str, float] = {}
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        if ":" not in token:
            raise DataError(f"Invalid holding format: '{token}'. Expected 'TICKER:WEIGHT'.")
        ticker, weight_str = token.split(":", 1)
        ticker = ticker.strip().upper()
        weight_str = weight_str.strip().rstrip("%")
        try:
            weight = float(weight_str)
        except ValueError:
            raise DataError(f"Invalid weight for {ticker}: '{weight_str}'.")
        if weight > 1.0:
            weight = weight / 100.0
        holdings[ticker] = weight
    if not holdings:
        raise DataError("No holdings parsed from portfolio string.")
    return holdings


def fetch_price_matrix(
    tickers: list[str],
    years: int,
    client: FMPClient,
) -> pd.DataFrame:
    """Fetch adjusted close prices for all tickers, aligned on common dates."""
    series_list: list[pd.Series] = []
    failed: list[str] = []
    for ticker in tickers:
        try:
            s = client.get_price_series(ticker, years=years)
            series_list.append(s)
        except Exception as e:
            logger.warning("Failed to fetch %s: %s", ticker, e)
            failed.append(ticker)

    if not series_list:
        raise DataError(f"Could not fetch price data for any tickers. Failed: {failed}")

    prices = pd.concat(series_list, axis=1).sort_index()
    prices = prices.dropna(how="all")
    prices = prices.ffill().bfill()
    prices = prices.dropna(axis=1, how="any")

    if prices.shape[1] < 2:
        raise DataError(
            f"Need at least 2 tickers with overlapping data. Got {prices.shape[1]}."
        )

    return prices


def compute_returns(prices: pd.DataFrame, method: str = "simple") -> pd.DataFrame:
    """Compute returns from a price matrix."""
    if method == "log":
        returns = np.log(prices / prices.shift(1))
    else:
        returns = prices.pct_change()
    return returns.dropna(how="all").iloc[1:]


def fetch_sector_map(tickers: list[str], client: FMPClient) -> dict[str, str]:
    """Map each ticker to its GICS sector via FMP company profile."""
    sector_map: dict[str, str] = {}
    for ticker in tickers:
        try:
            profile = client.get_company_profile(ticker)
            sector = profile.get("sector", "Unknown") or "Unknown"
            sector_map[ticker] = sector
        except Exception as e:
            logger.warning("Failed to get sector for %s: %s", ticker, e)
            sector_map[ticker] = "Unknown"
    return sector_map


def fetch_benchmark_prices(
    benchmark: str,
    years: int,
    client: FMPClient,
) -> pd.Series:
    """Fetch benchmark price series (default SPY for S&P 500)."""
    return client.get_price_series(benchmark, years=years)


# S&P 500 approximate sector weights (updated periodically)
SP500_SECTOR_WEIGHTS: dict[str, float] = {
    "Technology": 0.30,
    "Healthcare": 0.13,
    "Financials": 0.13,
    "Consumer Discretionary": 0.10,
    "Communication Services": 0.09,
    "Industrials": 0.08,
    "Consumer Staples": 0.06,
    "Energy": 0.04,
    "Utilities": 0.03,
    "Real Estate": 0.02,
    "Basic Materials": 0.02,
}
