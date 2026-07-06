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
  const stateRows = useMemo(() => buildStateRows(result), [result]);
  const tapeRows = useMemo(() => buildTapeRows(result), [result]);
  const ticker = result?.ticker ?? formValues.ticker.toUpperCase();
  const hasResult = Boolean(result);

  return (
    <main className="terminal-shell">
      <aside className="analysis-panel">
        <div className="brand-mark">
          <span>HMM</span>
          <strong>Regime Desk</strong>
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

        <section className="panel-card compact-list">
          <div className="panel-heading">
            <span>04</span>
            <h2>State tape</h2>
          </div>
          {stateRows.map((row) => (
            <div className="state-row" key={`${row.state}-${row.share}`}>
              <span className="state-dot" style={{ backgroundColor: row.color }} />
              <strong>State {row.state}</strong>
              <span>{row.share}</span>
            </div>
          ))}
        </section>
      </aside>

      <section className="workspace">
        <header className="terminal-topbar">
          <span>Live research terminal</span>
          <strong>{ticker} / daily regime model</strong>
          <em>{status === "loading" ? "Running" : "Online"}</em>
        </header>

        <section className="market-strip">
          <div className="quote-block">
            <span>Regime analysis</span>
            <h1>{ticker}</h1>
            <p>{formatRange(formValues)}</p>
          </div>
          <MetricTile label="Latest close" value={summary.latestClose} />
          <MetricTile label="Latest return" value={summary.latestReturn} tone={summary.returnTone} />
          <MetricTile label="Current regime" value={summary.latestRegime} wide />
          <MetricTile label="States" value={summary.states} />
        </section>

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

      <aside className="right-console">
        <section className="console-card">
          <div className="console-heading">
            <h2>Regime Stream</h2>
            <span>{ticker}</span>
          </div>
          <div className="signal-list">
            {tapeRows.map((row) => (
              <div className="signal-row" key={`${row.date}-${row.label}`}>
                <div>
                  <strong>{row.label}</strong>
                  <span>{row.date}</span>
                </div>
                <em className={row.returnValue >= 0 ? "positive" : "negative"}>
                  {(row.returnValue * 100).toFixed(2)}%
                </em>
              </div>
            ))}
          </div>
        </section>

        <section className="console-card">
          <div className="console-heading">
            <h2>Engine</h2>
            <span>Stack</span>
          </div>
          <div className="engine-grid">
            <DataRow label="API" value="FastAPI" />
            <DataRow label="Workers" value="Ray ready" />
            <DataRow label="Solver" value="OR-Tools" />
            <DataRow label="Charts" value="Plotly" />
          </div>
        </section>

        <section className="console-card note-card">
          <div className="console-heading">
            <h2>Interpretation</h2>
          </div>
          <p>
            High-volatility states indicate wider return dispersion and greater model-estimated stress.
            Transition probabilities describe how sticky each market state is across sessions.
          </p>
        </section>
      </aside>
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

function buildStateRows(result) {
  if (!result || result.hidden_states.length === 0) {
    return [
      { state: "-", share: "-", color: "#65758b" },
      { state: "-", share: "-", color: "#65758b" },
      { state: "-", share: "-", color: "#65758b" },
    ];
  }

  const total = result.hidden_states.length;
  const colors = ["#63d471", "#f4c430", "#ff6b5f", "#63a4ff", "#b28cff"];
  const counts = result.hidden_states.reduce((map, state) => {
    map.set(state, (map.get(state) ?? 0) + 1);
    return map;
  }, new Map());

  return [...counts.entries()]
    .sort(([a], [b]) => a - b)
    .map(([state, count]) => ({
      state,
      share: `${((count / total) * 100).toFixed(1)}%`,
      color: colors[Math.abs(Number(state)) % colors.length],
    }));
}

function buildTapeRows(result) {
  if (!result || result.dates.length === 0) {
    return [
      { date: "Waiting", label: "No run loaded", returnValue: 0 },
      { date: "Waiting", label: "Submit ticker", returnValue: 0 },
      { date: "Waiting", label: "Model idle", returnValue: 0 },
    ];
  }

  const start = Math.max(result.dates.length - 8, 0);
  return result.dates
    .slice(start)
    .map((date, offset) => {
      const index = start + offset;
      return {
        date,
        label: result.predicted_regime_labels[index] ?? `State ${result.hidden_states[index]}`,
        returnValue: Number(result.returns[index] ?? 0),
      };
    })
    .reverse();
}

function buildSummary(result) {
  if (!result || result.close_prices.length === 0) {
    return {
      observations: "-",
      latestClose: "-",
      latestCloseRaw: "-",
      latestReturn: "-",
      latestRegime: "-",
      states: "-",
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
