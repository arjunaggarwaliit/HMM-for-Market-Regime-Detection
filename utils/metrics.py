import numpy as np
import pandas as pd
from scipy.stats import wasserstein_distance
from typing import Dict, List, Optional, Tuple

def aic(log_likelihood: float, n_params: int) -> float:
    return 2 * n_params - 2 * log_likelihood

def bic(log_likelihood: float, n_params: int, n_obs: int) -> float:
    return n_params * np.log(n_obs) - 2 * log_likelihood

def hmm_n_params(N: int) -> int:
    return N ** 2 + 2 * N

def regime_persistence(labels: np.ndarray) -> Dict:
    durations: Dict = {}
    i = 0
    while i < len(labels):
        j = i + 1
        while j < len(labels) and labels[j] == labels[i]:
            j += 1
        lbl = labels[i]
        durations.setdefault(lbl, []).append(j - i)
        i = j
    return {lbl: np.mean(v) for lbl, v in durations.items()}

def regime_persistence_summary(labels: np.ndarray) -> pd.DataFrame:
    durations: Dict = {}
    i = 0
    while i < len(labels):
        j = i + 1
        while j < len(labels) and labels[j] == labels[i]:
            j += 1
        lbl = labels[i]
        durations.setdefault(lbl, []).append(j - i)
        i = j
    rows = []
    for lbl, durs in durations.items():
        rows.append({
            "State": lbl,
            "Mean Duration (days)": np.mean(durs),
            "Median Duration (days)": np.median(durs),
            "Max Duration (days)": np.max(durs),
            "# Episodes": len(durs),
        })
    return pd.DataFrame(rows).sort_values("State").reset_index(drop=True)

def conditional_sharpe(
    returns: np.ndarray,
    labels: np.ndarray,
    annualise: bool = True,
) -> Dict:
    factor = np.sqrt(252) if annualise else 1.0
    result = {}
    for lbl in set(labels):
        mask = labels == lbl
        r = returns[mask]
        if r.std() > 0:
            result[lbl] = (r.mean() / r.std()) * factor
        else:
            result[lbl] = np.nan
    return result

def _max_drawdown(returns: np.ndarray) -> float:
    if len(returns) == 0:
        return np.nan
    equity_curve = np.exp(np.cumsum(returns))
    running_peak = np.maximum.accumulate(equity_curve)
    drawdowns = equity_curve / running_peak - 1.0
    return float(drawdowns.min())

def downside_deviation(returns: np.ndarray, annualise: bool = True) -> float:
    r = np.asarray(returns, dtype=float)
    downside = r[r < 0]
    if len(downside) == 0:
        return 0.0
    deviation = downside.std(ddof=0)
    return float(deviation * np.sqrt(252)) if annualise else float(deviation)

def value_at_risk(returns: np.ndarray, level: float = 0.05) -> float:
    r = np.asarray(returns, dtype=float)
    if len(r) == 0:
        return np.nan
    return float(np.quantile(r, level))

def conditional_value_at_risk(returns: np.ndarray, level: float = 0.05) -> float:
    r = np.asarray(returns, dtype=float)
    if len(r) == 0:
        return np.nan
    threshold = np.quantile(r, level)
    tail = r[r <= threshold]
    return float(tail.mean()) if len(tail) else np.nan

def regime_statistics(
    returns: np.ndarray,
    labels: np.ndarray,
) -> pd.DataFrame:
    rows = []
    for lbl in sorted(set(labels), key=str):
        mask = labels == lbl
        r = returns[mask]
        annual_return = r.mean() * 252
        annual_volatility = r.std(ddof=0) * np.sqrt(252)
        downside = downside_deviation(r)
        max_drawdown = _max_drawdown(r)
        rows.append({
            "State": lbl,
            "Mean Return (ann.)": annual_return,
            "Volatility (ann.)": annual_volatility,
            "Sharpe (ann.)": annual_return / annual_volatility if annual_volatility > 0 else np.nan,
            "Sortino (ann.)": annual_return / downside if downside > 0 else np.nan,
            "Max Drawdown": max_drawdown,
            "Calmar": annual_return / abs(max_drawdown) if max_drawdown < 0 else np.nan,
            "Hit Rate": (r > 0).mean(),
            "VaR 5%": value_at_risk(r, 0.05),
            "CVaR 5%": conditional_value_at_risk(r, 0.05),
            "Skewness": pd.Series(r).skew(),
            "Excess Kurtosis": pd.Series(r).kurt(),
            "# Days": mask.sum(),
            "% of Sample": mask.mean() * 100,
        })
    return pd.DataFrame(rows)

def pairwise_wasserstein(
    returns: np.ndarray,
    labels: np.ndarray,
) -> pd.DataFrame:
    unique = sorted(set(labels), key=str)
    N = len(unique)
    W = np.zeros((N, N))
    for i, a in enumerate(unique):
        for j, b in enumerate(unique):
            if i != j:
                W[i, j] = wasserstein_distance(returns[labels == a], returns[labels == b])
    return pd.DataFrame(W, index=unique, columns=unique)

def regime_purity(pred_labels: np.ndarray, true_labels: np.ndarray) -> float:
    total, n = 0, len(pred_labels)
    for lbl in set(pred_labels):
        mask = pred_labels == lbl
        if mask.sum() == 0:
            continue
        counts = np.bincount(pd.Categorical(true_labels[mask]).codes)
        total += counts.max()
    return total / n

def model_comparison_table(results: List[Dict]) -> pd.DataFrame:
    rows = []
    for r in results:
        ll = r.get("log_likelihood", np.nan)
        k  = r.get("n_params", np.nan)
        T  = r.get("n_obs", np.nan)
        rows.append({
            "Model":             r.get("model", "?"),
            "States":            r.get("n_states", "?"),
            "Log-Likelihood":    round(ll, 2) if not np.isnan(ll) else "—",
            "AIC":               round(aic(ll, k), 1) if not np.isnan(ll) else "—",
            "BIC":               round(bic(ll, k, T), 1) if not np.isnan(ll) else "—",
            "Mean Persistence":  round(r.get("mean_persistence", np.nan), 1),
            "Purity vs Vol":     round(r.get("purity", np.nan), 3),
        })
    return pd.DataFrame(rows)
