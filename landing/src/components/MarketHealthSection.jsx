import ScrollReveal from "./ScrollReveal";
import DrawdownChart from "./charts/DrawdownChart";
import CorrelationMatrix from "./charts/CorrelationMatrix";

export default function MarketHealthSection({ data }) {
  const bestEntity = data?.kpis?.overall?.best_entity || "";
  const worstEntity = data?.kpis?.overall?.worst_entity || "";
  const bestSeries = data?.entity_series?.[bestEntity];
  const worstSeries = data?.entity_series?.[worstEntity];

  const correlationChartData = data?.charts?.correlation;

  const bestLabel = bestEntity.replace(".SA", "");
  const worstLabel = worstEntity.replace(".SA", "");

  return (
    <section
      id="saude"
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        padding: "80px 0",
      }}
    >
      <div className="container">
        <ScrollReveal>
          <span className="badge badge-warning" style={{ marginBottom: 16 }}>
            Saúde do Mercado
          </span>
          <h2>Risco, Correlação e Sazonalidade</h2>
          <p>
            Três perspectivas para entender o comportamento dos ativos: o tombo de cada um,
            como eles se movem juntos, e os padrões que se repetem ao longo dos anos.
          </p>
        </ScrollReveal>

        <div style={{ marginTop: 48 }}>
          <ScrollReveal delay={0.2}>
            <h3 style={{ fontSize: "1.3rem", marginBottom: 16 }}>
              Risco — Drawdown
            </h3>
            <div className="grid-2">
              <DrawdownChart series={bestSeries} label={bestLabel} />
              <DrawdownChart series={worstSeries} label={worstLabel} />
            </div>
          </ScrollReveal>

          <ScrollReveal delay={0.4}>
            <h3 style={{ fontSize: "1.3rem", margin: "48px 0 16px" }}>
              Correlação entre Ativos
            </h3>
            <div className="grid-2">
              <CorrelationMatrix chartData={correlationChartData} />
              <div style={{ display: "flex", flexDirection: "column", justifyContent: "center" }}>
                <p>
                  Bancos (<strong>ITUB</strong>, <strong>BBDC</strong>, <strong>BBAS</strong>){" "}
                  apresentam alta correlação entre si — andam juntos.
                </p>
                <p style={{ marginTop: 16 }}>
                  <strong>VALE</strong> e <strong>PETR4</strong> seguem o ciclo de commodities,
                  com correlação moderada entre si e baixa com o setor financeiro.
                </p>
                <p style={{ marginTop: 16 }}>
                  <strong>WEGE3</strong> e <strong>RENT3</strong> têm correlação mais baixa
                  com o mercado como um todo, oferecendo diversificação.
                </p>
              </div>
            </div>
          </ScrollReveal>


        </div>
      </div>
    </section>
  );
}
