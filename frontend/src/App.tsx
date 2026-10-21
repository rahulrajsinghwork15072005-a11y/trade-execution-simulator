import { useEffect, useState } from "react";
import Plot, { baseLayout, plotConfig } from "./components/Plot";
import {
  getCompare,
  getFrontier,
  getMonteCarlo,
  getSchedule,
  getSimulate,
  getStrategies,
} from "./api/client";

const chartStyle = { width: "100%", height: "300px" };
const COLORS: Record<string, string> = {
  TWAP: "#4da3ff",
  VWAP: "#2ec4b6",
  POV: "#a371f7",
  AlmgrenChriss: "#f0a500",
};

export default function App() {
  const [strategies, setStrategies] = useState<string[]>([]);
  const [strategy, setStrategy] = useState("VWAP");
  const [schedule, setSchedule] = useState<any>(null);
  const [sim, setSim] = useState<any>(null);
  const [mc, setMc] = useState<any>(null);
  const [frontier, setFrontier] = useState<any>(null);
  const [compare, setCompare] = useState<any>(null);

  useEffect(() => {
    getStrategies().then((d) => setStrategies(d.strategies));
    getSchedule().then(setSchedule);
    getFrontier().then(setFrontier);
    getCompare().then(setCompare);
  }, []);

  useEffect(() => {
    getSimulate(strategy).then(setSim);
    getMonteCarlo(strategy).then(setMc);
  }, [strategy]);

  const intervals = sim ? sim.base_prices.map((_: number, i: number) => i) : [];

  return (
    <>
      <header className="app-header">
        <div>
          <h1>Trade Execution Simulator</h1>
          <div className="sub">TWAP / VWAP / POV / Almgren–Chriss with impact, slippage, TCA.</div>
        </div>
        <select value={strategy} onChange={(e) => setStrategy(e.target.value)}>
          {strategies.map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
      </header>

      <div className="grid">
        <div className="card full">
          <h2>Execution schedule &amp; volume curve</h2>
          {schedule && (
            <Plot
              data={[
                ...Object.entries<any>(schedule.strategies).map(([name, xs]) => ({
                  x: schedule.intervals,
                  y: xs,
                  name,
                  type: "scatter",
                  line: { color: COLORS[name] || "#888" },
                })),
                {
                  x: schedule.intervals,
                  y: schedule.volume,
                  name: "mkt volume",
                  type: "bar",
                  yaxis: "y2",
                  marker: { color: "rgba(139,152,165,.25)" },
                },
              ]}
              layout={{
                ...baseLayout,
                yaxis: { ...baseLayout.yaxis, title: "shares" },
                yaxis2: { overlaying: "y", side: "right", showgrid: false, title: "volume" },
              }}
              config={plotConfig}
              style={chartStyle}
            />
          )}
        </div>

        <div className="card">
          <h2>Fills over the price path</h2>
          {sim && (
            <Plot
              data={[
                { x: intervals, y: sim.base_prices, name: "mid", type: "scatter", line: { color: "#8b98a5" } },
                {
                  x: intervals,
                  y: sim.exec_prices,
                  name: "fills",
                  mode: "markers",
                  type: "scatter",
                  marker: { color: "#2ec4b6", size: 6 },
                },
                {
                  x: intervals,
                  y: intervals.map(() => sim.benchmarks.arrival),
                  name: "arrival",
                  type: "scatter",
                  line: { color: "#f85149", dash: "dash" },
                },
              ]}
              layout={{ ...baseLayout }}
              config={plotConfig}
              style={chartStyle}
            />
          )}
        </div>

        <div className="card">
          <h2>Implementation-shortfall (bps)</h2>
          {sim && (
            <Plot
              data={[
                {
                  x: ["spread", "temporary", "permanent", "timing", "TOTAL"],
                  y: [
                    sim.tca.spread_cost_bps,
                    sim.tca.temporary_impact_bps,
                    sim.tca.permanent_impact_bps,
                    sim.tca.timing_bps,
                    sim.tca.implementation_shortfall_bps,
                  ],
                  type: "bar",
                  marker: { color: ["#4da3ff", "#2ec4b6", "#a371f7", "#8b98a5", "#f0a500"] },
                },
              ]}
              layout={{ ...baseLayout, yaxis: { ...baseLayout.yaxis, title: "bps" } }}
              config={plotConfig}
              style={chartStyle}
            />
          )}
        </div>

        <div className="card">
          <h2>Almgren–Chriss efficient frontier</h2>
          {frontier && (
            <Plot
              data={[
                {
                  x: frontier.points.map((p: any) => p.std),
                  y: frontier.points.map((p: any) => p.expected_cost),
                  mode: "lines+markers",
                  type: "scatter",
                  line: { color: "#f0a500" },
                },
              ]}
              layout={{
                ...baseLayout,
                xaxis: { ...baseLayout.xaxis, title: "risk (std of cost)" },
                yaxis: { ...baseLayout.yaxis, title: "expected cost" },
              }}
              config={plotConfig}
              style={chartStyle}
            />
          )}
        </div>

        <div className="card">
          <h2>Monte-Carlo cost distribution (bps)</h2>
          {mc && (
            <Plot
              data={[{ x: mc.samples, type: "histogram", marker: { color: "#2ec4b6" }, nbinsx: 40 }]}
              layout={{
                ...baseLayout,
                xaxis: {
                  ...baseLayout.xaxis,
                  title: `bps (mean ${mc.mean.toFixed(2)}, p5 ${mc.p5.toFixed(2)}, p95 ${mc.p95.toFixed(2)})`,
                },
              }}
              config={plotConfig}
              style={chartStyle}
            />
          )}
        </div>

        <div className="card full">
          <h2>Strategy comparison (TCA)</h2>
          {compare && (
            <table>
              <thead>
                <tr>
                  <th>Strategy</th>
                  <th>Avg price</th>
                  <th>IS (bps)</th>
                  <th>VWAP slip (bps)</th>
                  <th>Arrival slip (bps)</th>
                </tr>
              </thead>
              <tbody>
                {compare.rows.map((r: any) => (
                  <tr key={r.strategy}>
                    <td>{r.strategy}</td>
                    <td>{r.avg_price.toFixed(4)}</td>
                    <td>{r.is_bps.toFixed(2)}</td>
                    <td>{r.vwap_slippage_bps.toFixed(2)}</td>
                    <td>{r.arrival_slippage_bps.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </>
  );
}
