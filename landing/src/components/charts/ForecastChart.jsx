import { useEffect, useRef } from "react";
import { Chart as ChartJS } from "chart.js";
import "chart.js/auto";

export default function ForecastChart({ forecast }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!forecast) return;
    const { price_forecast, price_lower, price_upper, dates } = forecast;
    if (!price_forecast?.length) return;

    if (chartRef.current) chartRef.current.destroy();

    const ctx = canvasRef.current.getContext("2d");
    const labels = dates.map((d) => d.slice(0, 10));

    chartRef.current = new ChartJS(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "IC Superior",
            data: price_upper,
            borderColor: "rgba(59, 130, 246, 0.2)",
            backgroundColor: "rgba(59, 130, 246, 0.08)",
            borderWidth: 0,
            pointRadius: 0,
            fill: "+1",
          },
          {
            label: "Forecast",
            data: price_forecast,
            borderColor: "#3b82f6",
            backgroundColor: "rgba(59, 130, 246, 0.1)",
            borderWidth: 2.5,
            pointRadius: 4,
            pointBackgroundColor: "#3b82f6",
            tension: 0.3,
          },
          {
            label: "IC Inferior",
            data: price_lower,
            borderColor: "rgba(59, 130, 246, 0.2)",
            backgroundColor: "rgba(59, 130, 246, 0.08)",
            borderWidth: 0,
            pointRadius: 0,
            fill: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: {
            labels: { color: "#9aa0a6", font: { size: 11 } },
          },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: R$ ${ctx.parsed.y.toFixed(2)}`,
            },
          },
        },
        scales: {
          x: {
            grid: { color: "rgba(255,255,255,0.05)" },
            ticks: { color: "#9aa0a6", maxTicksLimit: 6 },
          },
          y: {
            grid: { color: "rgba(255,255,255,0.05)" },
            ticks: {
              color: "#9aa0a6",
              callback: (v) => `R$ ${v.toFixed(2)}`,
            },
          },
        },
      },
    });

    return () => {
      if (chartRef.current) chartRef.current.destroy();
    };
  }, [forecast]);

  if (!forecast?.price_forecast?.length) {
    return <p className="text-muted">Previsão não disponível.</p>;
  }

  return (
    <div className="chart-wrapper" style={{ height: 320 }}>
      <canvas ref={canvasRef} />
    </div>
  );
}
