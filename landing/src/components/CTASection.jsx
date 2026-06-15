import ScrollReveal from "./ScrollReveal";
import AboutCard from "./AboutCard";

export default function CTASection({ data }) {
  const generatedAt = data?.metadata?.generated_at?.slice(0, 10) || "";
  const tickerCount = data?.metadata?.tickers?.length || 9;

  return (
    <section
      id="sobre"
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "120px 0 0",
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
            className="cta-btn"
          >
            Abrir Dashboard Detalhado
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M7 17l9.2-9.2M17 17V7H7" />
            </svg>
          </a>
        </ScrollReveal>
      </div>

      <div className="section-divider" />

      <div className="container" style={{ paddingBottom: 0 }}>
        <ScrollReveal delay={0.3}>
          <h3 className="about-section-title">Sobre o Desenvolvedor</h3>
          <AboutCard />
        </ScrollReveal>

        <footer className="site-footer">
          <div className="footer-inner">
            <span>
              &copy; {new Date().getFullYear()} BR Stocks &mdash; An&aacute;lise de S&eacute;ries Temporais
            </span>
            <span>
              Dados: Yahoo Finance &middot; Semanal &middot; ARIMA &middot; Gerado em: {generatedAt}
            </span>
          </div>
        </footer>
      </div>
    </section>
  );
}
