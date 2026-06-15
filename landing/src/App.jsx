import { useState, useEffect } from "react";
import { loadData } from "./data/loadData";
import Navbar from "./components/Navbar";
import HeroSection from "./components/HeroSection";
import RankingSection from "./components/RankingSection";
import MarketHealthSection from "./components/MarketHealthSection";
import ForecastSection from "./components/ForecastSection";
import CTASection from "./components/CTASection";

export default function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData()
      .then(setData)
      .catch((err) => setError(err.message));
  }, []);

  if (error) {
    return (
      <div
        style={{
          height: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column",
          gap: 16,
          padding: 24,
          textAlign: "center",
        }}
      >
        <h2>Erro ao carregar dados</h2>
        <p className="text-muted">{error}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div
        style={{
          height: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <p className="text-muted">Carregando...</p>
      </div>
    );
  }

  return (
    <>
      <Navbar />
      <HeroSection data={data} />
      <RankingSection data={data} />
      <MarketHealthSection data={data} />
      <ForecastSection data={data} />
      <CTASection data={data} />
    </>
  );
}
