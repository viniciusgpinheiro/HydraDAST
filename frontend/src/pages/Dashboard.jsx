import { Link } from 'react-router-dom';
import { Info } from 'lucide-react';
import { dashboardStats, trendData, scansRecentes } from '../data/mock';
import TrendChart from '../components/TrendChart';
import { StatusBadge, RiscoBadge } from '../components/Badge';

export default function Dashboard() {
  const { totalScans, vulnerabilidades: v } = dashboardStats;

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
            <div className="hd-metric">{v.total}</div>
            <div className="hd-breakdown">
              <div className="hd-breakdown-row"><span className="sev-critical">Críticas</span><span className="val sev-critical">{v.criticas}</span></div>
              <div className="hd-breakdown-row"><span className="sev-high">Altas</span><span className="val sev-high">{v.altas}</span></div>
              <div className="hd-breakdown-row"><span className="sev-medium">Médias</span><span className="val sev-medium">{v.medias}</span></div>
              <div className="hd-breakdown-row"><span className="sev-safe">Baixas</span><span className="val sev-safe">{v.baixas}</span></div>
            </div>
          </div>
        </div>
      </div>

      {/* Gráfico de tendência */}
      <div className="hd-card hd-mt-24">
        <div className="hd-section-title">Gráfico de Tendência</div>
        <TrendChart data={trendData} />
      </div>

      {/* Tabela de scans recentes */}
      <div className="hd-card hd-mt-24">
        <div className="hd-section-title">Tabela de scans recentes</div>
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
            {scansRecentes.map((s) => (
              <tr key={s.id}>
                <td><Link to={`/relatorios/${s.id}`}>{s.url}</Link></td>
                <td className="text-muted" style={{ color: 'var(--hd-text-muted)' }}>{s.data}</td>
                <td><StatusBadge value={s.status} /></td>
                <td><RiscoBadge value={s.risco} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
