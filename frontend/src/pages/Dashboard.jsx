import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Info } from 'lucide-react';
import { listarScans } from '../api';
import { StatusBadge, RiscoBadge } from '../components/Badge';
import { formatData, statusLabel } from '../lib/format';

const SEVERIDADES = [
  { key: 'criticas', label: 'Críticas', cls: 'sev-critical', cor: 'var(--hd-critical)' },
  { key: 'altas', label: 'Altas', cls: 'sev-high', cor: 'var(--hd-high, #f59e0b)' },
  { key: 'medias', label: 'Médias', cls: 'sev-medium', cor: 'var(--hd-medium, #eab308)' },
  { key: 'baixas', label: 'Baixas', cls: 'sev-safe', cor: 'var(--hd-safe)' },
];

export default function Dashboard() {
  const [scans, setScans] = useState(null);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    listarScans().then(setScans).catch((e) => setErro(e.message));
  }, []);

  if (erro) {
    return (
      <>
        <h1 className="hd-page-title">Dashboard</h1>
        <div className="hd-card" style={{ color: 'var(--hd-critical)' }}>
          Não foi possível carregar os dados: {erro}. O backend está rodando?
        </div>
      </>
    );
  }

  const lista = scans || [];
  const totalScans = lista.length;
  const agg = lista.reduce(
    (a, s) => ({
      total: a.total + (s.total || 0),
      criticas: a.criticas + (s.criticas || 0),
      altas: a.altas + (s.altas || 0),
      medias: a.medias + (s.medias || 0),
      baixas: a.baixas + (s.baixas || 0),
    }),
    { total: 0, criticas: 0, altas: 0, medias: 0, baixas: 0 },
  );
  const maxSev = Math.max(1, agg.criticas, agg.altas, agg.medias, agg.baixas);

  return (
    <>
      <h1 className="hd-page-title">Dashboard</h1>

      {/* Cards de métricas */}
      <div className="hd-grid-2">
        <div className="hd-card">
          <div className="hd-card-label">
            Total de Scans
            <Info size={18} className="hd-info-icon" />
          </div>
          <div className="hd-metric">{totalScans}</div>
        </div>

        <div className="hd-card">
          <div className="hd-card-label">
            Vulnerabilidades encontradas
            <Info size={18} className="hd-info-icon" />
          </div>
          <div className="hd-flex-between" style={{ alignItems: 'center' }}>
            <div className="hd-metric">{agg.total}</div>
            <div className="hd-breakdown">
              <div className="hd-breakdown-row"><span className="sev-critical">Críticas</span><span className="val sev-critical">{agg.criticas}</span></div>
              <div className="hd-breakdown-row"><span className="sev-high">Altas</span><span className="val sev-high">{agg.altas}</span></div>
              <div className="hd-breakdown-row"><span className="sev-medium">Médias</span><span className="val sev-medium">{agg.medias}</span></div>
              <div className="hd-breakdown-row"><span className="sev-safe">Baixas</span><span className="val sev-safe">{agg.baixas}</span></div>
            </div>
          </div>
        </div>
      </div>

      {/* Distribuição por severidade (dados reais agregados) */}
      <div className="hd-card hd-mt-24">
        <div className="hd-section-title">Distribuição por severidade</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginTop: 12 }}>
          {SEVERIDADES.map((sev) => (
            <div key={sev.key} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span className={sev.cls} style={{ width: 90, fontSize: 14 }}>{sev.label}</span>
              <div style={{ flex: 1, background: 'var(--hd-border, #21262d)', borderRadius: 6, height: 14, overflow: 'hidden' }}>
                <div style={{ width: `${(agg[sev.key] / maxSev) * 100}%`, height: '100%', background: sev.cor, borderRadius: 6, transition: 'width .3s' }} />
              </div>
              <span className={sev.cls} style={{ width: 32, textAlign: 'right', fontSize: 14 }}>{agg[sev.key]}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Tabela de scans recentes */}
      <div className="hd-card hd-mt-24">
        <div className="hd-section-title">Scans recentes</div>
        <table className="hd-table">
          <thead>
            <tr>
              <th>url</th>
              <th>data</th>
              <th>Status</th>
              <th>Risco final</th>
            </tr>
          </thead>
          <tbody>
            {lista.map((s) => (
              <tr key={s.id}>
                <td><Link to={`/relatorios/${s.id}`}>{s.url}</Link></td>
                <td style={{ color: 'var(--hd-text-muted)' }}>{formatData(s.criadoEm)}</td>
                <td><StatusBadge value={statusLabel(s.status)} /></td>
                <td><RiscoBadge value={s.risco} /></td>
              </tr>
            ))}
            {scans !== null && lista.length === 0 && (
              <tr>
                <td colSpan={4} style={{ color: 'var(--hd-text-muted)', textAlign: 'center', padding: 24 }}>
                  Nenhum scan ainda. <Link to="/novo-scan">Inicie um novo escaneamento</Link>.
                </td>
              </tr>
            )}
            {scans === null && (
              <tr>
                <td colSpan={4} style={{ color: 'var(--hd-text-muted)', textAlign: 'center', padding: 24 }}>
                  Carregando…
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
