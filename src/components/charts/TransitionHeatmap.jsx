import ChartPanel from "./ChartPanel.jsx";
import Plot from "./Plot.jsx";
import { baseLayout, plotConfig } from "./chartConfig.js";

export default function TransitionHeatmap({ result }) {
  const labels = result.transition_probabilities.map((_, index) => `State ${index}`);
  const matrixSize = Math.max(labels.length * 74, 300);

  return (
    <ChartPanel title="Transition Probability Matrix">
      <Plot
        key={`transition-heatmap-${labels.length}`}
        data={[
          {
            z: result.transition_probabilities,
            x: labels,
            y: labels,
            type: "heatmap",
            colorscale: [
              [0, "#0b1220"],
              [0.25, "#13263d"],
              [0.5, "#1e5a73"],
              [0.75, "#2fb47c"],
              [1, "#b7f26a"],
            ],
            zmin: 0,
            zmax: 1,
            xgap: 2,
            ygap: 2,
            text: result.transition_probabilities.map((row) =>
              row.map((value) => value.toFixed(3)),
            ),
            texttemplate: "%{text}",
            textfont: {
              color: "#e6eefb",
              size: 14,
            },
            hovertemplate: "From %{y}<br>To %{x}<br>Probability: %{z:.4f}<extra></extra>",
            colorbar: {
              title: "Probability",
              thickness: 14,
              len: 0.68,
            },
          },
        ]}
        layout={{
          ...baseLayout,
          height: Math.max(matrixSize + 116, 416),
          hovermode: "closest",
          margin: { l: 82, r: 82, t: 18, b: 64 },
          xaxis: {
            title: "Next State",
            type: "category",
            categoryorder: "array",
            categoryarray: labels,
            gridcolor: "rgba(111, 135, 166, 0.2)",
            linecolor: "rgba(111, 135, 166, 0.34)",
            tickfont: { color: "#8fa2b8", size: 13 },
            ticks: "",
          },
          yaxis: {
            title: "Current State",
            type: "category",
            categoryorder: "array",
            categoryarray: labels,
            autorange: "reversed",
            gridcolor: "rgba(111, 135, 166, 0.2)",
            linecolor: "rgba(111, 135, 166, 0.34)",
            tickfont: { color: "#8fa2b8", size: 13 },
            ticks: "",
            scaleanchor: "x",
          },
        }}
        config={plotConfig}
        useResizeHandler
        className="plot"
      />
    </ChartPanel>
  );
}
