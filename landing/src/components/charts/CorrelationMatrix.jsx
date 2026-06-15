export default function CorrelationMatrix({ chartData }) {
  const trace = chartData?.traces?.[0];
  const labels = trace?.x || [];
  const z = trace?.z || [];

  if (!z.length || !labels.length || !z[0]?.length) {
    return <p className="text-muted">Dados de correlação indisponíveis.</p>;
  }

  const flat = z.flat().filter((v) => v !== undefined);
  const minVal = Math.min(...flat);
  const maxVal = Math.max(...flat);
  const short = labels.map((l) => l.replace(".SA", ""));

  const cellStyle = (v) => {
    const t = maxVal === minVal ? 0.5 : (v - minVal) / (maxVal - minVal);
    const r = Math.round(30 + t * 30);
    const g = Math.round(86 + t * 160);
    const b = Math.round(219 - t * 100);
    return {
      padding: "6px 4px",
      borderRadius: 4,
      textAlign: "center",
      fontSize: 11,
      fontWeight: 500,
      color: t > 0.5 ? "#fff" : "#e8eaed",
      backgroundColor: `rgba(${r},${g},${b},0.85)`,
      cursor: "default",
    };
  };

  return (
    <div className="chart-wrapper" style={{ overflow: "auto" }}>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: `auto repeat(${labels.length}, 1fr)`,
          gap: 2,
          minWidth: 320,
        }}
      >
        <div />
        {short.map((l) => (
          <div
            key={l}
            style={{
              padding: "4px 2px",
              fontSize: 10,
              fontWeight: 700,
              textAlign: "center",
              color: "#9aa0a6",
            }}
          >
            {l}
          </div>
        ))}
        {z.map((row, i) => (
          <>
            <div
              key={`l${i}`}
              style={{
                padding: "4px 8px 4px 0",
                fontSize: 10,
                fontWeight: 700,
                textAlign: "right",
                color: "#9aa0a6",
                whiteSpace: "nowrap",
              }}
            >
              {short[i]}
            </div>
            {row.map((v, j) => (
              <div
                key={`${i}-${j}`}
                style={cellStyle(v)}
                title={`${short[i]} x ${short[j]}: ${v.toFixed(2)}`}
              >
                {v.toFixed(2)}
              </div>
            ))}
          </>
        ))}
      </div>
    </div>
  );
}
