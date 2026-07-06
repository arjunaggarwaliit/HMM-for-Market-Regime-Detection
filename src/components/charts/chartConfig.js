export const regimePalette = [
  "#63d471",
  "#f4c430",
  "#ff6b5f",
  "#63a4ff",
  "#b28cff",
  "#52d6c5",
  "#d77946",
  "#8ea4c4",
];

export const baseLayout = {
  autosize: true,
  margin: { l: 48, r: 24, t: 18, b: 42 },
  paper_bgcolor: "#090f18",
  plot_bgcolor: "#090f18",
  font: {
    family: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
    color: "#c9d6e6",
  },
  hovermode: "x unified",
  xaxis: {
    gridcolor: "rgba(111, 135, 166, 0.2)",
    linecolor: "rgba(111, 135, 166, 0.34)",
    zeroline: false,
    tickfont: { color: "#8fa2b8" },
  },
  yaxis: {
    gridcolor: "rgba(111, 135, 166, 0.2)",
    linecolor: "rgba(111, 135, 166, 0.34)",
    zeroline: false,
    tickfont: { color: "#8fa2b8" },
  },
  legend: {
    bgcolor: "rgba(9, 15, 24, 0.72)",
    bordercolor: "rgba(111, 135, 166, 0.24)",
    borderwidth: 1,
    font: { color: "#c9d6e6" },
  },
};

export const plotConfig = {
  displaylogo: false,
  responsive: true,
  modeBarButtonsToRemove: ["lasso2d", "select2d"],
};

export function colorForState(state) {
  return regimePalette[Math.abs(Number(state)) % regimePalette.length];
}
