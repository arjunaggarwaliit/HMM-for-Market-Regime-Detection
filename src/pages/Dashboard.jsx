import { useEffect, useMemo, useState } from "react";
import OptimizationPanel from "../components/OptimizationPanel.jsx";
import TickerForm from "../components/TickerForm.jsx";
import HiddenStateTimeline from "../components/charts/HiddenStateTimeline.jsx";
import RegimeDistributionChart from "../components/charts/RegimeDistributionChart.jsx";
import RegimePriceChart from "../components/charts/RegimePriceChart.jsx";
import ReturnsChart from "../components/charts/ReturnsChart.jsx";
import StockPriceChart from "../components/charts/StockPriceChart.jsx";
import TransitionHeatmap from "../components/charts/TransitionHeatmap.jsx";
import { predictTickerRegimes } from "../services/regimeApi.js";

const initialForm = {
  ticker: "SPY",
  startDate: "2023-01-01",
  endDate: "2024-01-01",
};

const views = [
  { id: "price", label: "Price" },
  { id: "regimes", label: "Regime Price" },
  { id: "states", label: "Hidden States" },
  { id: "returns", label: "Returns" },
  { id: "transition", label: "Transition Matrix" },
  { id: "distribution", label: "Regime Distribution" },
  { id: "optimization", label: "Optimization" },
];

export default function Dashboard() {
  const [formValues, setFormValues] = useState(initialForm);
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const [activeView, setActiveView] = useState("price");

  useEffect(() => {
    handleSubmit(initialForm);
  }, []);

  async function handleSubmit(submittedValues) {
    setFormValues(submittedValues);
    setStatus("loading");
    setError("");

    try {
      const data = await predictTickerRegimes(submittedValues);
      setResult(data);
      setStatus("success");
    } catch (requestError) {
      setResult(null);
      setError(requestError.message);
      setStatus("error");
    }
  }

  const summary = useMemo(() => buildSummary(result), [result]);
  const ticker = result?.ticker ?? formValues.ticker.toUpperCase();
  const hasResult = Boolean(result);

  return (
    <main className="research-app">
      <aside className="analysis-panel">
        <div className="brand-mark">
          <span>HMM</span>
          <strong>Market Regime Lab</strong>
        </div>

        <section className="panel-card">
          <div className="panel-heading">
            <span>01</span>
            <h2>Run analysis</h2>
          </div>
          <TickerForm values={formValues} isLoading={status === "loading"} onSubmit={handleSubmit} />
          {error && <div className="alert">{error}</div>}
        </section>

        <section className="panel-card">
          <div className="panel-heading">
            <span>02</span>
            <h2>Model defaults</h2>
          </div>
          <ParameterGrid />
        </section>

        <section className="panel-card subdued">
          <div className="panel-heading">
            <span>03</span>
            <h2>Output status</h2>
          </div>
          <DataRow label="Run state" value={status === "loading" ? "Running" : hasResult ? "Complete" : "Ready"} />
          <DataRow label="Observations" value={summary.observations} />
          <DataRow label="Latest regime" value={summary.latestRegime} />
        </section>
      </aside>

      <section className="workspace">
        <header className="market-strip">
          <div className="quote-block">
            <span>Regime analysis</span>
            <h1>{ticker}</h1>
            <p>{formatRange(formValues)}</p>
          </div>
          <MetricTile label="Latest close" value={summary.latestClose} />
          <MetricTile label="Latest return" value={summary.latestReturn} tone={summary.returnTone} />
          <MetricTile label="Current regime" value={summary.latestRegime} wide />
          <MetricTile label="States" value={summary.states} />
        </header>

        <nav className="view-switcher" aria-label="Analysis views">
          {views.map((view) => (
            <button
              className={activeView === view.id ? "active" : ""}
              key={view.id}
              onClick={() => setActiveView(view.id)}
              type="button"
            >
              {view.label}
            </button>
          ))}
        </nav>

        <div className="context-row">
          <ContextPill label="Close" value={summary.latestClose} />
          <ContextPill label="Regime" value={summary.latestRegime} />
          <ContextPill label="Sample" value={`${summary.observations} sessions`} />
        </div>

        <section className="chart-surface">
          {status === "loading" && (
            <div className="loading-panel">
              <div className="loader" />
              <span>Fitting regime model</span>
            </div>
          )}

          {hasResult && status !== "loading" && (
            <ActiveView activeView={activeView} key={`${activeView}-${result.ticker}-${result.dates.length}`} result={result} />
          )}

          {!hasResult && status !== "loading" && (
            <div className="empty-state">
              <h2>Ready for market data</h2>
              <p>Submit a ticker and date range to generate regime output.</p>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}

function ActiveView({ activeView, result }) {
  if (activeView === "price") return <StockPriceChart result={result} />;
  if (activeView === "regimes") return <RegimePriceChart result={result} />;
  if (activeView === "states") return <HiddenStateTimeline result={result} />;
  if (activeView === "returns") return <ReturnsChart result={result} />;
  if (activeView === "transition") return <TransitionHeatmap result={result} />;
  if (activeView === "distribution") return <RegimeDistributionChart result={result} />;
  return <OptimizationPanel regimeResult={result} />;
}

function ParameterGrid() {
  return (
    <div className="parameter-grid">
      <DataRow label="n_states" value="3" />
      <DataRow label="n_iter" value="100" />
      <DataRow label="tol" value="1e-6" />
      <DataRow label="random_state" value="42" />
    </div>
  );
}

function MetricTile({ label, value, tone = "", wide = false }) {
  return (
    <div className={`metric-tile ${tone} ${wide ? "wide" : ""}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ContextPill({ label, value }) {
  return (
    <div className="context-pill">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function DataRow({ label, value }) {
  return (
    <div className="data-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function buildSummary(result) {
  if (!result || result.close_prices.length === 0) {
    return {
      observations: "—",
      latestClose: "—",
      latestCloseRaw: "—",
      latestReturn: "—",
      latestRegime: "—",
      states: "—",
      returnTone: "",
    };
  }

  const latestClose = result.close_prices.at(-1);
  const latestReturn = result.returns.at(-1) ?? 0;
  const latestRegime = result.predicted_regime_labels.at(-1) ?? "Unknown";
  const states = new Set(result.hidden_states).size;

  return {
    observations: result.dates.length.toLocaleString(),
    latestClose: `$${latestClose.toFixed(2)}`,
    latestCloseRaw: latestClose.toFixed(2),
    latestReturn: `${(latestReturn * 100).toFixed(2)}%`,
    latestRegime,
    states,
    returnTone: latestReturn >= 0 ? "positive" : "negative",
  };
}

function formatRange(values) {
  return `${values.startDate} to ${values.endDate}`;
}
