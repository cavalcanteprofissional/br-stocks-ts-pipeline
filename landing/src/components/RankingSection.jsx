import ScrollReveal from "./ScrollReveal";
import RankingBar from "./charts/RankingBar";

export default function RankingSection({ data }) {
  const bestE = data?.kpis?.overall?.best_entity?.replace(".SA", "") || "";
  const worstE = data?.kpis?.overall?.worst_entity?.replace(".SA", "") || "";
  const bestR = data?.kpis?.overall?.best_return || 0;
  const worstR = data?.kpis?.overall?.worst_return || 0;
  const ratio = bestR / worstR;

  return (
    <section
      id="ranking"
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
            Ranking
          </span>
          <h2>Quem Ganhou e Quem Perdeu</h2>
          <p>
            Em {bestR.toFixed(1)}x o retorno inicial, <strong className="text-green">{bestE}</strong>{" "}
            lidera com { (bestR * 100).toFixed(0) }% de retorno acumulado —{" "}
            <strong className="text-red">{worstE}</strong> ficou em último com{" "}
            { (worstR * 100).toFixed(0) }%.
          </p>
          <p className="text-muted" style={{ marginTop: 8, fontSize: "0.9rem" }}>
            Diferença de <strong>{ratio.toFixed(0)}x</strong> entre o melhor e o pior desempenho do período.
          </p>
        </ScrollReveal>

        <ScrollReveal delay={0.3}>
          <div style={{ marginTop: 32 }}>
            <RankingBar data={data} />
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
