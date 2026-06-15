import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
} from "chart.js";

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip);

export default function RankingBar({ data }) {
  const all = data?.kpis?.overall?.all_returns;
  if (!all) return null;

  const entries = Object.entries(all).sort((a, b) => b[1] - a[1]);
  const labels = entries.map(([e]) => e.replace(".SA", ""));
  const values = entries.map(([, v]) => +(v * 100).toFixed(1));

  const best = entries[0][0];
  const worst = entries[entries.length - 1][0];

  const bgColors = entries.map(([e]) => {
    if (e === best) return "#0E9F6E";
    if (e === worst) return "#E02424";
    return "#1A56DB";
  });

  const chartData = {
    labels,
    datasets: [
      {
        label: "Retorno Total (%)",
        data: values,
        backgroundColor: bgColors,
        borderRadius: 4,
      },
    ],
  };

  const options = {
    indexAxis: "y",
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      tooltip: {
        callbacks: {
          label: (ctx) => `${ctx.parsed.x}%`,
        },
      },
    },
    scales: {
      x: {
        grid: { color: "rgba(255,255,255,0.05)" },
        ticks: { color: "#9aa0a6" },
      },
      y: {
        grid: { display: false },
        ticks: { color: "#e8eaed", font: { size: 13, weight: "600" } },
      },
    },
  };

  return (
    <div className="chart-wrapper" style={{ height: 380 }}>
      <Bar data={chartData} options={options} />
    </div>
  );
}
