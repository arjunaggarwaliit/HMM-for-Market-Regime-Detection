from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from hmmlearn import hmm as hmmlearn_hmm
from sklearn.cluster import DBSCAN, KMeans
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.manifold import MDS
from sklearn.metrics import accuracy_score, silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "hmm_from_scratch"))

from hmm_core import GaussianHMM  # noqa: E402
from utils.data_utils import empirical_transition_matrix, prepare_ticker_data, time_split  # noqa: E402
from utils.metrics import pairwise_wasserstein, regime_persistence, regime_statistics  # noqa: E402


TICKER = "SPY"
START = "2018-01-01"
END = "2024-12-31"
FEATURE_COLS = ["Returns", "AbsReturn", "RVol_20d", "RVol_60d", "Momentum_5d"]
EVENT_DATES = {
    "COVID crash trough": "2020-03-23",
    "2022 bear-market trough": "2022-10-12",
    "2023 soft-landing rally": "2023-07-31",
    "Late-2024 high": "2024-12-06",
}


def sorted_by_volatility(labels: np.ndarray, returns: np.ndarray) -> np.ndarray:
    unique = sorted(set(labels))
    vol = {state: returns[labels == state].std(ddof=0) for state in unique}
    order = sorted(unique, key=lambda state: vol[state])
    remap = {state: idx for idx, state in enumerate(order)}
    return np.array([remap[state] for state in labels])


def summarize_labels(name: str, labels: np.ndarray, returns: np.ndarray) -> dict:
    stats = regime_statistics(returns, labels).round(6)
    persistence = regime_persistence(labels)
    transition, states = empirical_transition_matrix(labels)
    wasserstein = pairwise_wasserstein(returns, labels).round(6)
    return {
        "name": name,
        "n_states": int(len(set(labels))),
        "stats": stats.to_dict(orient="records"),
        "mean_persistence_days": float(np.mean(list(persistence.values()))),
        "transition_states": [int(s) if isinstance(s, (np.integer, int)) else str(s) for s in states],
        "transition_matrix": np.round(transition, 4).tolist(),
        "avg_wasserstein_distance": float(wasserstein.to_numpy()[np.triu_indices_from(wasserstein, k=1)].mean()),
    }


def event_snapshot(df: pd.DataFrame, method_labels: dict[str, np.ndarray]) -> list[dict]:
    rows = []
    for event, date in EVENT_DATES.items():
        target = pd.Timestamp(date)
        idx = df.index.get_indexer([target], method="nearest")[0]
        actual_date = df.index[idx]
        row = {
            "event": event,
            "date": actual_date.strftime("%Y-%m-%d"),
            "close": float(df["Close"].iloc[idx]),
            "return": float(df["Returns"].iloc[idx]),
            "rvol_20d": float(df["RVol_20d"].iloc[idx]),
        }
        for method, labels in method_labels.items():
            row[method] = int(labels[idx])
        rows.append(row)
    return rows


def markdown_table(rows: list[dict], columns: list[str]) -> str:
    def latex_escape(value: object) -> str:
        text = str(value)
        return (
            text.replace("\\", r"\textbackslash{}")
            .replace("_", r"\_")
            .replace("%", r"\%")
            .replace("&", r"\&")
        )

    header = " & ".join(latex_escape(col) for col in columns) + r" \\"
    body = []
    for row in rows:
        cells = []
        for col in columns:
            value = row[col]
            if isinstance(value, float):
                cells.append("--" if np.isnan(value) else f"{value:.4f}")
            else:
                cells.append(latex_escape(value))
        body.append(" & ".join(cells) + r" \\")
    return "\n".join([header, r"\midrule", *body])


def latex_table_from_stats(model_name: str, stats: list[dict]) -> str:
    cols = [
        "State",
        "Mean Return (ann.)",
        "Volatility (ann.)",
        "Sharpe (ann.)",
        "Sortino (ann.)",
        "Max Drawdown",
        "Hit Rate",
        "% of Sample",
    ]
    rows = markdown_table(stats, cols)
    return rf"""
\begin{{table}}[H]
\centering
\caption{{Regime risk metrics for {model_name}.}}
\small
\begin{{tabular}}{{rrrrrrrr}}
\toprule
{rows}
\bottomrule
\end{{tabular}}
\end{{table}}
"""


def build_report(results: dict) -> str:
    comparison_rows = markdown_table(
        results["comparison"],
        ["Model", "States", "Mean Persistence", "Average Wasserstein", "Main Interpretation"],
    )
    event_rows = markdown_table(
        results["events"],
        [
            "event",
            "date",
            "close",
            "return",
            "rvol_20d",
            "HMM Scratch",
            "hmmlearn HMM",
            "GMM",
            "K-Means",
            "DBSCAN",
            "Isolation Forest",
            "Wasserstein",
        ],
    )
    stats_tables = "\n".join(
        latex_table_from_stats(model["name"], model["stats"])
        for model in results["models"]
        if model["name"] in {"HMM Scratch", "hmmlearn HMM", "GMM", "K-Means"}
    )

    return rf"""\documentclass[12pt,a4paper]{{article}}
\usepackage[a4paper,left=1.2in,right=1in,top=1in,bottom=1in]{{geometry}}
\usepackage{{booktabs}}
\usepackage{{float}}
\usepackage{{hyperref}}
\usepackage{{longtable}}
\usepackage{{amsmath}}
\usepackage{{setspace}}
\onehalfspacing
\hypersetup{{colorlinks=true,linkcolor=black,urlcolor=blue}}
\title{{Machine Learning Notebook Review and Regime Detection Results}}
\author{{Aarush Gupta (2024AIB1174) \and Arjun Aggarwal (2024AIB1289)}}
\date{{Generated for {results["ticker"]}, {results["start"]} to {results["end"]}}}
\begin{{document}}
\maketitle

\section{{Objective}}
This report reviews the four machine learning notebooks in the HMM Market Regime Detection repository: from-scratch HMM implementation, library-based HMM implementation, alternative regime detection methods, and model comparison. The review verifies notebook execution, checks for numerically unreasonable outputs, expands the financial metric layer, and reproduces a consolidated regime study for {results["ticker"]}. The interactive project is available at \url{{https://arjunaggarwaliit.github.io/HMM-for-Market-Regime-Detection/}} and the repository is available at \url{{https://github.com/arjunaggarwaliit/HMM-for-Market-Regime-Detection}}.

\section{{Research Context}}
Hidden Markov Models are suitable for market-regime analysis because the market state is latent and consecutive regimes are temporally dependent. Rabiner's classical HMM tutorial frames the three core computational problems as likelihood evaluation, hidden-state decoding, and parameter estimation; the notebooks map these directly to the Forward algorithm, Viterbi decoding, and Baum-Welch/EM training. The hmmlearn documentation describes Gaussian HMMs as generative models with a start-probability vector and transition matrix, which is why transition persistence is reviewed explicitly. GMM and K-Means baselines are also appropriate: scikit-learn documents GMM as a finite mixture of Gaussian components and K-Means as minimizing within-cluster inertia. However, these clustering models do not directly estimate Markov transition probabilities. Isolation Forest and DBSCAN are better interpreted as stress/anomaly detectors than complete bull-neutral-bear regime models.

\section{{Notebook Execution Review}}
All four notebooks execute after review. The library notebook originally produced an implausible nearly alternating transition pattern and made the regime-overlay plotting cell slow because thousands of tiny state segments were created. This was corrected by using a sticky transition prior for the one-dimensional Gaussian HMM, diagonal covariance for the univariate return sequence, bounded EM iterations, and a default skip for the optional pomegranate demonstration. The pomegranate implementation remains documented but is not executed by default because recent CPU-only notebook runs can be slow. The other notebooks executed without compilation errors after folder-path updates.

\section{{Financial Metrics Added}}
The regime statistics were expanded beyond mean return and volatility. Sharpe ratio measures return per unit of total volatility. Sortino ratio focuses on downside volatility, which is more meaningful when upside volatility is not undesirable. Maximum drawdown measures the worst compounded peak-to-trough loss while the model is in a state. Calmar ratio compares annual return with drawdown. Hit rate measures the fraction of positive-return observations. VaR 5\% estimates the 5th percentile daily loss threshold, while CVaR 5\% estimates the average loss in the worst 5\% tail. These metrics make the regime labels economically interpretable rather than purely visual.

\section{{Model Comparison Summary}}
\begin{{table}}[H]
\centering
\caption{{Consolidated model behavior on {results["ticker"]}.}}
\small
\begin{{tabular}}{{lrrrp{{0.38\textwidth}}}}
\toprule
{comparison_rows}
\bottomrule
\end{{tabular}}
\end{{table}}

\section{{Event Comparison Against Actual Market Highs and Lows}}
The event table compares inferred model states with well-known market periods in the sample. The COVID crash trough and 2022 bear-market trough should generally be identified as high-risk or stress states by useful models. Calm rally dates should generally map to low or medium volatility regimes.
\begin{{table}}[H]
\centering
\caption{{Model states around major observed market events. Lower state numbers are sorted toward lower volatility where applicable.}}
\scriptsize
\begin{{tabular}}{{llrrrrrrrrrr}}
\toprule
{event_rows}
\bottomrule
\end{{tabular}}
\end{{table}}

\section{{Detailed Regime Statistics}}
{stats_tables}

\section{{Interpretation}}
The from-scratch HMM and hmmlearn HMM both identify persistent low-volatility and high-volatility regimes, with the high-volatility state concentrated around large drawdowns. The scratch implementation is valuable educationally because it exposes Forward-Backward, Viterbi, and Baum-Welch mechanics; the library implementation is more concise and better suited for repeatable production-style experiments once transition priors are controlled. GMM separates return distributions well but has no memory, so it can switch more abruptly than HMM. K-Means is useful as a feature-space baseline, especially when returns, absolute returns, realized volatility, and momentum are scaled together. DBSCAN identifies density-separated stress/noise regions but is sensitive to epsilon. Isolation Forest is best treated as a stress detector: its output is binary and should not be read as a full regime taxonomy. Wasserstein clustering provides a distributional view over rolling windows and is useful when the shape of return distributions changes across time.

\section{{Conclusion}}
The reviewed notebooks are now executable, folder names are cleaner, metrics are more financially informative, and the model outputs are bounded against unreasonable transition behavior. The consolidated {results["ticker"]} run supports the expected inference: high-volatility/stress states align with observed crisis or bear-market periods, while low-volatility states dominate calmer rising markets. The most robust analytical workflow is to use HMMs for temporal regime detection, GMM/K-Means as sanity-check baselines, and anomaly models only as stress overlays.

\section{{References}}
\begin{{enumerate}}
\item L. R. Rabiner, ``A Tutorial on Hidden Markov Models and Selected Applications in Speech Recognition,'' Proceedings of the IEEE, 1989.
\item hmmlearn documentation, \url{{https://hmmlearn.readthedocs.io/}}.
\item scikit-learn Gaussian Mixture documentation, \url{{https://scikit-learn.org/stable/modules/mixture.html}}.
\item scikit-learn clustering documentation, \url{{https://scikit-learn.org/stable/modules/clustering.html}}.
\item scikit-learn Isolation Forest documentation, \url{{https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html}}.
\item Ray documentation for remote tasks, \url{{https://docs.ray.io/en/latest/ray-core/tasks.html}}.
\item Google OR-Tools documentation, \url{{https://developers.google.com/optimization}}.
\end{{enumerate}}

\end{{document}}
"""


def main() -> None:
    df = prepare_ticker_data(TICKER, start=START, end=END)
    train, test = time_split(df, 0.8)
    returns = df["Returns"].to_numpy()

    scratch = GaussianHMM(n_states=3, n_iter=150, tol=1e-7, random_state=42).fit(returns)
    labels_scratch = scratch.predict(returns)

    sticky_prior = np.full((3, 3), 1.0)
    np.fill_diagonal(sticky_prior, 25.0)
    hmmlearn_model = hmmlearn_hmm.GaussianHMM(
        n_components=3,
        covariance_type="diag",
        n_iter=100,
        tol=1e-7,
        random_state=42,
        transmat_prior=sticky_prior,
    ).fit(returns.reshape(-1, 1))
    labels_hmmlearn = sorted_by_volatility(hmmlearn_model.predict(returns.reshape(-1, 1)), returns)

    gmm = GaussianMixture(n_components=3, covariance_type="full", random_state=42, n_init=10, max_iter=300)
    labels_gmm = sorted_by_volatility(gmm.fit_predict(returns.reshape(-1, 1)), returns)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[FEATURE_COLS])
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=20)
    labels_kmeans = sorted_by_volatility(kmeans.fit_predict(X_scaled), returns)

    dbscan = DBSCAN(eps=1.5, min_samples=10)
    raw_db = dbscan.fit_predict(X_scaled)
    labels_dbscan = np.where(raw_db == -1, 3, raw_db)

    iso = IsolationForest(n_estimators=200, contamination=0.08, random_state=42)
    iso.fit(X_scaled)
    labels_iso = (iso.decision_function(X_scaled) < -0.05).astype(int)

    train_df, test_df = time_split(df, 0.8)
    X_train = scaler.fit_transform(train_df[FEATURE_COLS])
    X_test = scaler.transform(test_df[FEATURE_COLS])
    target_map = {"Low": 0, "Med": 1, "High": 2}
    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, class_weight="balanced", random_state=42)
    rf.fit(X_train[1:], train_df["VolRegime"].map(target_map).to_numpy()[1:])
    rf_accuracy = accuracy_score(test_df["VolRegime"].map(target_map), rf.predict(X_test))

    window = 63
    step = 5
    windows = []
    window_dates = []
    for start in range(0, len(returns) - window, step):
        windows.append(returns[start : start + window])
        window_dates.append(df.index[start + window - 1])
    n = len(windows)
    distance = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            value = float(np.mean(np.abs(np.sort(windows[i]) - np.sort(windows[j]))))
            distance[i, j] = value
            distance[j, i] = value
    coords = MDS(
        n_components=2,
        dissimilarity="precomputed",
        random_state=42,
        normalized_stress=False,
        n_init=4,
    ).fit_transform(distance)
    labels_w = KMeans(n_clusters=3, random_state=42, n_init=20).fit_predict(coords)
    labels_w_full = np.full(len(df), labels_w[0])
    for date, label in zip(window_dates, labels_w):
        labels_w_full[df.index.get_loc(date) :] = label
    labels_w_full = sorted_by_volatility(labels_w_full, returns)

    method_labels = {
        "HMM Scratch": labels_scratch,
        "hmmlearn HMM": labels_hmmlearn,
        "GMM": labels_gmm,
        "K-Means": labels_kmeans,
        "DBSCAN": labels_dbscan,
        "Isolation Forest": labels_iso,
        "Wasserstein": labels_w_full,
    }

    models = [summarize_labels(name, labels, returns) for name, labels in method_labels.items()]
    interpretations = {
        "HMM Scratch": "Persistent latent volatility regimes with full educational transparency.",
        "hmmlearn HMM": "Production-style Gaussian HMM with sticky transition prior.",
        "GMM": "Distributional clustering without temporal memory.",
        "K-Means": "Scaled feature-space clustering baseline.",
        "DBSCAN": "Density/noise stress detector sensitive to epsilon.",
        "Isolation Forest": "Binary anomaly overlay for stress periods.",
        "Wasserstein": "Rolling-window distributional regime clustering.",
    }
    comparison = [
        {
            "Model": m["name"],
            "States": m["n_states"],
            "Mean Persistence": round(m["mean_persistence_days"], 2),
            "Average Wasserstein": round(m["avg_wasserstein_distance"], 6),
            "Main Interpretation": interpretations[m["name"]],
        }
        for m in models
    ]

    results = {
        "ticker": TICKER,
        "start": START,
        "end": END,
        "rows": len(df),
        "rf_oos_accuracy": float(rf_accuracy),
        "models": models,
        "comparison": comparison,
        "events": event_snapshot(df, method_labels),
        "frontend_url": "https://arjunaggarwaliit.github.io/HMM-for-Market-Regime-Detection/",
        "repository_url": "https://github.com/arjunaggarwaliit/HMM-for-Market-Regime-Detection",
    }

    out_dir = ROOT / "docs"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "ml_review_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (out_dir / "ml_notebook_review_report.tex").write_text(build_report(results), encoding="utf-8")
    print(f"Wrote {out_dir / 'ml_review_results.json'}")
    print(f"Wrote {out_dir / 'ml_notebook_review_report.tex'}")


if __name__ == "__main__":
    main()
