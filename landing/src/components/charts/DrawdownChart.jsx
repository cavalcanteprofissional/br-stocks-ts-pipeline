import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Filler,
} from "chart.js";

ChartJS.register(LineElement, PointElement, CategoryScale, LinearScale, Tooltip, Filler);

export default function DrawdownChart({ series, label }) {
  const dd = series?.Drawdown;
  const dates = series?.dates;
  if (!dd?.length || !dates?.length) return null;

  const minVal = Math.min(...dd);

  const chartData = {
    labels: dates.map((d) => d.slice(0, 7)),
    datasets: [
      {
        label: "Drawdown (%)",
        data: dd,
        borderColor: "#E02424",
        backgroundColor: "rgba(224, 36, 36, 0.1)",
        fill: true,
        borderWidth: 2,
        pointRadius: 0,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      tooltip: {
        callbacks: {
          label: (ctx) => `${ctx.parsed.y.toFixed(1)}%`,
        },
      },
    },
    scales: {
      x: {
        grid: { color: "rgba(255,255,255,0.05)" },
        ticks: { color: "#9aa0a6", maxTicksLimit: 10 },
      },
      y: {
        grid: { color: "rgba(255,255,255,0.05)" },
        ticks: { color: "#9aa0a6", callback: (v) => `${v}%` },
      },
    },
  };

  return (
    <div>
      <div className="chart-wrapper" style={{ height: 280 }}>
        <Line data={chartData} options={options} />
      </div>
      <p className="text-muted" style={{ marginTop: 12, fontSize: "0.9rem" }}>
        Drawdown máximo: <span className="text-red">{minVal.toFixed(1)}%</span> — {label}
      </p>
    </div>
  );
}
