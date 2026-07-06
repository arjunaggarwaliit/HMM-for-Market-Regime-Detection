import ChartPanel from "./ChartPanel.jsx";
import Plot from "./Plot.jsx";
import { baseLayout, plotConfig } from "./chartConfig.js";

export default function ReturnsChart({ result }) {
  return (
    <ChartPanel title="Returns Series">
      <Plot
        data={[
          {
            x: result.dates,
            y: result.returns.map((value) => value * 100),
            type: "bar",
            name: "Return",
            marker: {
              color: result.returns.map((value) => (value >= 0 ? "#63d471" : "#ff6b5f")),
            },
            hovertemplate: "%{x}<br>Return: %{y:.3f}%<extra></extra>",
          },
        ]}
        layout={{
          ...baseLayout,
          yaxis: { ...baseLayout.yaxis, title: "Return %" },
          bargap: 0,
          height: 320,
        }}
        config={plotConfig}
        useResizeHandler
        className="plot"
      />
    </ChartPanel>
  );
}
