// Mini gráfico de barras (Acurácia) em SVG — reproduz as barras verdes do Figma.

export default function BarChart({ values, color = 'var(--hd-safe)' }) {
  const W = 260;
  const H = 120;
  const gap = 4;
  const barW = (W - gap * (values.length - 1)) / values.length;
  const maxV = Math.max(...values);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="100%" role="img" aria-label="Gráfico de acurácia">
      {values.map((v, i) => {
        const h = (v / maxV) * (H - 8);
        const x = i * (barW + gap);
        const y = H - h;
        return <rect key={i} x={x} y={y} width={barW} height={h} rx="2" fill={color} opacity={0.55 + (v / maxV) * 0.45} />;
      })}
    </svg>
  );
}
