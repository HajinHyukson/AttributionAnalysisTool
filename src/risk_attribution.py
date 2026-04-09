"""Factor-based risk attribution and decomposition."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from .covariance import annualize_covariance, corr_from_cov, ledoit_wolf_cov


@dataclass
class FactorModelResult:
    """Result of estimating a factor model on portfolio holdings."""
    betas: pd.DataFrame          # (n_assets, n_factors) factor loadings
    residual_var: np.ndarray     # (n_assets,) idiosyncratic variance per asset
    factor_cov: np.ndarray       # (n_factors, n_factors) factor covariance
    factor_names: list[str]
    r_squared: dict[str, float]  # per-asset R-squared


@dataclass
class RiskDecomposition:
    """Full risk attribution output."""
    total_vol_annual: float
    var_95: float
    holdings: list[dict]          # per-holding risk contribution
    factors: list[dict]           # per-factor risk contribution
    systematic_pct: float
    idiosyncratic_pct: float
    factor_betas: dict[str, dict[str, float]]  # ticker -> factor -> beta


def estimate_factor_model_pca(
    returns: pd.DataFrame,
    n_factors: int = 3,
) -> FactorModelResult:
    """Estimate a PCA-based factor model from the returns matrix itself."""
    clean = returns.dropna(how="any")
    values = clean.values
    mean = values.mean(axis=0)
    centered = values - mean

    # PCA via SVD
    U, S, Vt = np.linalg.svd(centered, full_matrices=False)
    factor_returns = U[:, :n_factors] * S[:n_factors]  # (T, n_factors)
    loadings = Vt[:n_factors, :].T                      # (n_assets, n_factors)

    # Residuals
    reconstructed = factor_returns @ loadings.T
    residuals = centered - reconstructed
    residual_var = np.var(residuals, axis=0, ddof=1)

    # Factor covariance
    factor_cov = np.cov(factor_returns.T, ddof=1)
    if np.isscalar(factor_cov):
        factor_cov = np.array([[float(factor_cov)]])

    # R-squared per asset
    total_var = np.var(centered, axis=0, ddof=1)
    r_squared = {}
    for i, ticker in enumerate(clean.columns):
        tv = total_var[i]
        r_squared[ticker] = float(1.0 - residual_var[i] / tv) if tv > 0 else 0.0

    factor_names = [f"PC{i+1}" for i in range(n_factors)]
    betas = pd.DataFrame(loadings, index=clean.columns, columns=factor_names)

    return FactorModelResult(
        betas=betas,
        residual_var=residual_var,
        factor_cov=factor_cov,
        factor_names=factor_names,
        r_squared=r_squared,
    )


def estimate_factor_model_regression(
    returns: pd.DataFrame,
    factor_returns: pd.DataFrame,
) -> FactorModelResult:
    """Estimate factor model via OLS regression of each asset on factor returns."""
    common_idx = returns.index.intersection(factor_returns.index)
    Y = returns.loc[common_idx].values        # (T, n_assets)
    X = factor_returns.loc[common_idx].values  # (T, n_factors)

    n_assets = Y.shape[1]
    n_factors = X.shape[1]
    betas = np.zeros((n_assets, n_factors))
    residual_var = np.zeros(n_assets)
    r_squared = {}

    for i in range(n_assets):
        reg = LinearRegression().fit(X, Y[:, i])
        betas[i] = reg.coef_
        predicted = reg.predict(X)
        resid = Y[:, i] - predicted
        residual_var[i] = float(np.var(resid, ddof=1))
        ss_res = np.sum(resid ** 2)
        ss_tot = np.sum((Y[:, i] - Y[:, i].mean()) ** 2)
        r_squared[returns.columns[i]] = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    factor_cov = np.cov(X.T, ddof=1)
    if np.isscalar(factor_cov):
        factor_cov = np.array([[float(factor_cov)]])

    betas_df = pd.DataFrame(
        betas,
        index=returns.columns,
        columns=factor_returns.columns,
    )

    return FactorModelResult(
        betas=betas_df,
        residual_var=residual_var,
        factor_cov=factor_cov,
        factor_names=list(factor_returns.columns),
        r_squared=r_squared,
    )


def decompose_risk(
    weights: np.ndarray,
    returns: pd.DataFrame,
    factor_model: FactorModelResult,
    sector_map: dict[str, str] | None = None,
) -> RiskDecomposition:
    """Decompose portfolio risk into factor and idiosyncratic components."""
    w = np.asarray(weights, dtype=float)
    B = factor_model.betas.values          # (n_assets, n_factors)
    F = factor_model.factor_cov            # (n_factors, n_factors)
    D = np.diag(factor_model.residual_var) # (n_assets, n_assets)

    # Total covariance: Sigma = B @ F @ B' + D
    systematic_cov = B @ F @ B.T
    total_cov = systematic_cov + D
    total_cov_annual = annualize_covariance(total_cov)

    # Portfolio variance
    port_var = float(w @ total_cov_annual @ w)
    port_vol = float(np.sqrt(max(port_var, 0)))

    # Systematic vs idiosyncratic
    systematic_var = float(w @ annualize_covariance(systematic_cov) @ w)
    idiosyncratic_var = float(w @ annualize_covariance(D) @ w)
    total = systematic_var + idiosyncratic_var
    systematic_pct = systematic_var / total * 100 if total > 0 else 0.0
    idiosyncratic_pct = idiosyncratic_var / total * 100 if total > 0 else 0.0

    # Marginal contribution to risk per holding
    mctr = (total_cov_annual @ w) / port_vol if port_vol > 0 else np.zeros_like(w)
    ctr = w * mctr  # component risk
    ctr_pct = ctr / port_vol * 100 if port_vol > 0 else np.zeros_like(w)

    tickers = list(returns.columns)
    holdings = []
    for i, ticker in enumerate(tickers):
        holdings.append({
            "ticker": ticker,
            "weight": round(float(w[i]) * 100, 2),
            "mctr": round(float(mctr[i]) * 100, 4),
            "ctr": round(float(ctr[i]) * 100, 4),
            "ctr_pct": round(float(ctr_pct[i]), 2),
            "sector": (sector_map or {}).get(ticker, "Unknown"),
        })

    # Factor-level risk contribution
    # Portfolio factor exposures: b_p = B' @ w
    b_p = B.T @ w  # (n_factors,)
    factor_var_contributions = []
    F_annual = annualize_covariance(F)
    for j, fname in enumerate(factor_model.factor_names):
        # Factor j contribution: b_p[j]^2 * F[j,j] + cross terms
        fvar = float(b_p[j] ** 2 * F_annual[j, j])
        factor_var_contributions.append({
            "factor": fname,
            "exposure": round(float(b_p[j]), 4),
            "variance_contribution": round(fvar, 6),
            "pct_of_systematic": round(fvar / systematic_var * 100, 2) if systematic_var > 0 else 0.0,
        })

    # VaR (95%) — parametric
    var_95 = round(float(port_vol * 1.645), 4)

    # Factor betas per ticker
    factor_betas = {}
    for i, ticker in enumerate(tickers):
        factor_betas[ticker] = {
            fname: round(float(B[i, j]), 4)
            for j, fname in enumerate(factor_model.factor_names)
        }

    return RiskDecomposition(
        total_vol_annual=round(port_vol * 100, 4),
        var_95=round(var_95 * 100, 4),
        holdings=holdings,
        factors=factor_var_contributions,
        systematic_pct=round(systematic_pct, 2),
        idiosyncratic_pct=round(idiosyncratic_pct, 2),
        factor_betas=factor_betas,
    )
