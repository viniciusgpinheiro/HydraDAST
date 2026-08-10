// Gráfico de tendência em SVG puro — reproduz o "Gráfico de Tendência" do Figma
// (duas linhas suaves com área, eixos discretos), sem dependências externas.

const W = 900;
const H = 300;
const PAD = { top: 20, right: 24, bottom: 34, left: 56 };

function buildPath(values, maxY) {
  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;
  const step = innerW / (values.length - 1);
  return values.map((v, i) => {
    const x = PAD.left + i * step;
    const y = PAD.top + innerH - (v / maxY) * innerH;
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
}

export default function TrendChart({ data }) {
  const { labels, series, yTicks } = data;
  const maxY = Math.max(...yTicks);
  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;
  const step = innerW / (labels.length - 1);

  return (
    <div style={{ width: '100%', overflowX: 'auto' }}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Gráfico de tendência">
        {/* grid + rótulos Y */}
        {yTicks.map((t) => {
          const y = PAD.top + innerH - (t / maxY) * innerH;
          return (
            <g key={t}>
              <line x1={PAD.left} y1={y} x2={W - PAD.right} y2={y} stroke="#21262d" strokeWidth="1" />
              <text x={PAD.left - 12} y={y + 4} textAnchor="end" fontSize="12" fill="#8b949e">
                {t.toLocaleString('pt-BR')}
              </text>
            </g>
          );
        })}

        {/* rótulos X */}
        {labels.map((lb, i) => (
          <text key={lb} x={PAD.left + i * step} y={H - 10} textAnchor="middle" fontSize="12" fill="#8b949e">
            {lb}
          </text>
        ))}

        {/* linhas */}
        {series.map((s) => (
          <path
            key={s.name}
            d={buildPath(s.values, maxY)}
            fill="none"
            stroke={s.color}
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        ))}
      </svg>

      <div style={{ display: 'flex', gap: 20, marginTop: 8, paddingLeft: PAD.left }}>
        {series.map((s) => (
          <span key={s.name} style={{ display: 'inline-flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--hd-text-muted)' }}>
            <span style={{ width: 12, height: 3, borderRadius: 2, background: s.color, display: 'inline-block' }} />
            {s.name}
          </span>
        ))}
      </div>
    </div>
  );
}
