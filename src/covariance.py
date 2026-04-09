from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf


def nearest_psd(matrix: np.ndarray, floor: float = 1e-10) -> np.ndarray:
    """Project a matrix to the nearest positive semi-definite matrix."""
    symmetric = (np.asarray(matrix, dtype=float) + np.asarray(matrix, dtype=float).T) / 2.0
    eigenvalues, eigenvectors = np.linalg.eigh(symmetric)
    clipped = np.clip(eigenvalues, floor, None)
    repaired = eigenvectors @ np.diag(clipped) @ eigenvectors.T
    return (repaired + repaired.T) / 2.0


def corr_from_cov(cov: np.ndarray) -> np.ndarray:
    """Extract correlation matrix from covariance matrix."""
    vol = np.sqrt(np.clip(np.diag(cov), 0.0, None))
    denom = np.outer(vol, vol)
    with np.errstate(divide="ignore", invalid="ignore"):
        corr = np.divide(cov, denom, out=np.zeros_like(cov), where=denom > 0)
    np.fill_diagonal(corr, 1.0)
    return corr


def ledoit_wolf_cov(returns: pd.DataFrame) -> np.ndarray:
    """Estimate covariance matrix using Ledoit-Wolf shrinkage."""
    clean = returns.dropna(how="any")
    if clean.empty:
        raise ValueError("Returns matrix is empty after dropping missing values.")
    lw = LedoitWolf()
    lw.fit(clean.values)
    return nearest_psd(lw.covariance_)


def ewma_cov(returns: pd.DataFrame, decay: float = 0.94) -> np.ndarray:
    """Estimate covariance matrix using exponentially weighted moving average."""
    clean = returns.dropna(how="any")
    if clean.shape[0] < 2:
        raise ValueError("EWMA requires at least two observations.")
    values = clean.values
    n_obs, n_assets = values.shape
    cov = np.cov(values[:2].T, ddof=1)
    if np.isscalar(cov):
        cov = np.array([[float(cov)]], dtype=float)
    for idx in range(2, n_obs):
        r_t = values[idx].reshape(n_assets, 1)
        cov = decay * cov + (1.0 - decay) * (r_t @ r_t.T)
    return nearest_psd(cov)


def annualize_covariance(cov: np.ndarray, periods_per_year: int = 252) -> np.ndarray:
    return np.asarray(cov, dtype=float) * float(periods_per_year)
