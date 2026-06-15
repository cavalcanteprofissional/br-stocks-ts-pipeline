import { motion } from "framer-motion";
import { useCountUp } from "../hooks/useCountUp";
import ScrollReveal from "./ScrollReveal";
import heroVideo from "../assets/hero-bg.mp4";

export default function HeroSection({ data }) {
  const bestEntity = data?.kpis?.overall?.best_entity?.replace(".SA", "") || "";
  const bestReturn = data?.kpis?.overall?.best_return || 0;
  const bestReturnPct = (bestReturn * 100).toFixed(0);
  const tickerCount = data?.metadata?.tickers?.length || 9;
  const generatedAt = data?.metadata?.generated_at?.slice(0, 10) || "";

  const [counted, ref] = useCountUp(Number(bestReturnPct), 2500, 0);

  return (
    <section
      id="hero"
      style={{
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        position: "relative",
        overflow: "hidden",
        paddingTop: "var(--nav-height)",
      }}
    >
      <video
        autoPlay
        loop
        muted
        playsInline
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          objectFit: "cover",
          pointerEvents: "none",
        }}
      >
        <source src={heroVideo} type="video/mp4" />
      </video>

      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "rgba(15, 17, 23, 0.55)",
          pointerEvents: "none",
        }}
      />

      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse at 30% 50%, rgba(26, 86, 219, 0.15) 0%, transparent 60%), radial-gradient(ellipse at 70% 50%, rgba(14, 159, 110, 0.10) 0%, transparent 60%)",
          pointerEvents: "none",
        }}
      />

      <div className="container" style={{ position: "relative", zIndex: 1 }}>
        <ScrollReveal>
          <p
            style={{
              fontSize: "0.85rem",
              textTransform: "uppercase",
              letterSpacing: "0.15em",
              color: "var(--accent-light)",
              marginBottom: 16,
              fontWeight: 600,
            }}
          >
            Análise de Séries Temporais
          </p>
          <h1>
            O Mercado Brasileiro<br />
            <span style={{ color: "var(--accent-light)" }}>em Números</span>
          </h1>
          <p
            style={{
              fontSize: "1.1rem",
              marginTop: 20,
              maxWidth: 520,
              lineHeight: 1.7,
            }}
          >
            {tickerCount} ações analisadas com modelos ARIMA, decomposição sazonal,
            detecção de anomalias e projeções de curto prazo.
          </p>
        </ScrollReveal>

        <ScrollReveal delay={0.3}>
          <div
            ref={ref}
            style={{
              marginTop: 48,
              display: "flex",
              alignItems: "baseline",
              gap: 12,
            }}
          >
            <span
              style={{
                fontSize: "clamp(3rem, 8vw, 6rem)",
                fontWeight: 800,
                color: "var(--green-light)",
                lineHeight: 1,
              }}
            >
              +{counted}%
            </span>
            <span style={{ fontSize: "1.3rem", color: "var(--text-muted)" }}>
              retorno acumulado — {bestEntity}
            </span>
          </div>
        </ScrollReveal>

        <ScrollReveal delay={0.5}>
          <div
            style={{
              display: "flex",
              gap: 32,
              marginTop: 40,
              flexWrap: "wrap",
            }}
          >
            <div>
              <div style={{ fontSize: "1.8rem", fontWeight: 700 }}>
                {tickerCount}
              </div>
              <div className="text-muted" style={{ fontSize: "0.85rem" }}>
                Ações
              </div>
            </div>
            <div>
              <div style={{ fontSize: "1.8rem", fontWeight: 700 }}>575</div>
              <div className="text-muted" style={{ fontSize: "0.85rem" }}>
                Semanas de dados
              </div>
            </div>
            <div>
              <div style={{ fontSize: "1.8rem", fontWeight: 700 }}>12</div>
              <div className="text-muted" style={{ fontSize: "0.85rem" }}>
                Semanas de projeção
              </div>
            </div>
            <div>
              <div style={{ fontSize: "1.8rem", fontWeight: 700 }}>
                {generatedAt}
              </div>
              <div className="text-muted" style={{ fontSize: "0.85rem" }}>
                Data da análise
              </div>
            </div>
          </div>
        </ScrollReveal>
      </div>

      <motion.div
        className="scroll-indicator"
        animate={{ y: [0, 8, 0] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#9aa0a6" strokeWidth="2">
          <path d="M12 5v14M5 12l7 7 7-7" />
        </svg>
      </motion.div>
    </section>
  );
}
