import ScrollReveal from "./ScrollReveal";

export default function CTASection({ data }) {
  const generatedAt = data?.metadata?.generated_at?.slice(0, 10) || "";
  const tickerCount = data?.metadata?.tickers?.length || 9;

  return (
    <section
      style={{
        minHeight: "60vh",
        display: "flex",
        alignItems: "center",
        padding: "80px 0",
      }}
    >
      <div className="container" style={{ textAlign: "center" }}>
        <ScrollReveal>
          <h2>Explore a Análise Completa</h2>
          <p style={{ margin: "16px auto 32px", textAlign: "center" }}>
            Dashboard interativo com {tickerCount} ativos, gráficos detalhados,
            tabela de forecast, detecção de anomalias em tempo real e diagnósticos
            de modelo.
          </p>
          <a
            href="https://br-stocks-ts-pipeline-sca7v3vvdzvpfc42zdkxkg.streamlit.app/"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              padding: "14px 32px",
              background: "var(--accent)",
              color: "#fff",
              borderRadius: 8,
              textDecoration: "none",
              fontWeight: 600,
              fontSize: "1rem",
              transition: "background 0.2s",
            }}
            onMouseEnter={(e) => (e.target.style.background = "var(--accent-light)")}
            onMouseLeave={(e) => (e.target.style.background = "var(--accent)")}
          >
            Abrir Dashboard Detalhado
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M7 17l9.2-9.2M17 17V7H7" />
            </svg>
          </a>
        </ScrollReveal>

        <ScrollReveal delay={0.3}>
          <footer
            style={{
              marginTop: 80,
              paddingTop: 32,
              borderTop: "1px solid rgba(255,255,255,0.06)",
              fontSize: "0.8rem",
              color: "var(--text-muted)",
            }}
          >
            <p style={{ margin: "0 auto", textAlign: "center" }}>
              Dados: Yahoo Finance · Frequência: Semanal · Modelo: ARIMA/SARIMA · 
              Gerado em: {generatedAt} · {tickerCount} tickers analisados
            </p>
          </footer>
        </ScrollReveal>
      </div>
    </section>
  );
}
