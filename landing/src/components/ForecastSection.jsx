import ScrollReveal from "./ScrollReveal";
import ForecastChart from "./charts/ForecastChart";

export default function ForecastSection({ data }) {
  const bestEntity = data?.kpis?.overall?.best_entity || "";
  const forecast = data?.forecast?.[bestEntity];
  if (!forecast) return null;

  const horizon = data?.metadata?.forecast_horizon || 12;
  const hasResidAuto = forecast?.has_residual_autocorrelation;
  const isHealthy = !hasResidAuto;
  const badgeText = isHealthy ? "Modelo confiável" : "Possível má especificação";
  const badgeClass = isHealthy ? "badge-success" : "badge-warning";
  const badgeEmoji = isHealthy ? "\u2705" : "\u26a0\ufe0f";

  const fcEnd = forecast?.price_forecast?.[forecast.price_forecast.length - 1] || 0;
  const lastPrice = data?.entity_series?.[bestEntity]?.Close?.slice(-1)[0] || 0;
  const change = lastPrice ? ((fcEnd - lastPrice) / lastPrice) * 100 : 0;

  const rmse = forecast?.rmse;
  const cvRmse = forecast?.cv_rmse;
  const lbPval = forecast?.ljung_box_pval;

  return (
    <section
      id="forecast"
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        padding: "80px 0",
      }}
    >
      <div className="container">
        <ScrollReveal>
          <span className="badge badge-success" style={{ marginBottom: 16 }}>
            Projeção
          </span>
          <h2>O Que Esperar nos Próximos {horizon} Meses</h2>
          <p>
            Modelo ARIMA ajustado para cada ativo com validação cruzada e diagnóstico
            de resíduos. A projeção abaixo mostra o intervalo de confiança de 95%
            para o preço.
          </p>
        </ScrollReveal>

        <ScrollReveal delay={0.3}>
          <div style={{ marginTop: 32 }}>
            <div
              style={{
                display: "flex",
                gap: 24,
                flexWrap: "wrap",
                marginBottom: 24,
                alignItems: "center",
              }}
            >
              <span className={`badge ${badgeClass}`} style={{ fontSize: "1rem", padding: "6px 16px" }}>
                {badgeEmoji} {badgeText}
              </span>
              <span className="text-muted" style={{ fontSize: "0.9rem" }}>
                Ljung-Box p={lbPval?.toFixed(3) || "N/A"}
              </span>
            </div>

            <ForecastChart forecast={forecast} />

            <div
              style={{
                display: "flex",
                gap: 32,
                marginTop: 24,
                flexWrap: "wrap",
              }}
            >
              <div>
                <div className="text-muted" style={{ fontSize: "0.8rem" }}>Projeção</div>
                <div style={{ fontSize: "1.3rem", fontWeight: 700 }}>
                  R$ {fcEnd.toFixed(2)}
                  <span style={{ color: change >= 0 ? "var(--green-light)" : "var(--red)", fontSize: "0.9rem", marginLeft: 8 }}>
                    ({change >= 0 ? "+" : ""}{change.toFixed(1)}%)
                  </span>
                </div>
              </div>
              {rmse != null && (
                <div>
                  <div className="text-muted" style={{ fontSize: "0.8rem" }}>RMSE (in-sample)</div>
                  <div style={{ fontSize: "1.3rem", fontWeight: 700 }}>{rmse.toFixed(4)}</div>
                </div>
              )}
              {cvRmse != null && (
                <div>
                  <div className="text-muted" style={{ fontSize: "0.8rem" }}>RMSE (Walk-Forward CV)</div>
                  <div style={{ fontSize: "1.3rem", fontWeight: 700 }}>{cvRmse.toFixed(4)}</div>
                </div>
              )}
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
