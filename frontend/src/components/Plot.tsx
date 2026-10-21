import createPlotlyComponent from "react-plotly.js/factory";
import Plotly from "plotly.js-dist-min";

const Plot = createPlotlyComponent(Plotly);
export default Plot;

export const baseLayout = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  font: { color: "#c9d4e3", family: "Inter, system-ui, sans-serif", size: 11 },
  margin: { l: 52, r: 48, t: 16, b: 40 },
  xaxis: { gridcolor: "#1d2926", zerolinecolor: "#33405a" },
  yaxis: { gridcolor: "#1d2926", zerolinecolor: "#33405a" },
  legend: { orientation: "h" as const, y: -0.2 },
};

export const plotConfig = { displayModeBar: false, responsive: true } as const;
