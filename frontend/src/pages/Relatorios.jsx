import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search } from 'lucide-react';
import { scansRecentes } from '../data/mock';
import { StatusBadge, RiscoBadge } from '../components/Badge';

export default function Relatorios() {
  const [q, setQ] = useState('');

  const filtrados = useMemo(
    () => scansRecentes.filter((s) => s.url.toLowerCase().includes(q.toLowerCase())),
    [q],
  );

  return (
    <>
      <h1 className="hd-page-title">Relatórios</h1>

      <div style={{ marginBottom: 24 }}>
        <label className="hd-label">Pesquisar</label>
        <div style={{ position: 'relative' }}>
          <Search size={18} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--hd-text-muted)' }} />
          <input
            className="hd-input"
            style={{ paddingLeft: 42 }}
            placeholder="Buscar por url…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
      </div>

      <div className="hd-card">
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
            {filtrados.map((s) => (
              <tr key={s.id}>
                <td><Link to={`/relatorios/${s.id}`}>{s.url}</Link></td>
                <td style={{ color: 'var(--hd-text-muted)' }}>{s.data}</td>
                <td><StatusBadge value={s.status} /></td>
                <td><RiscoBadge value={s.risco} /></td>
              </tr>
            ))}
            {filtrados.length === 0 && (
              <tr>
                <td colSpan={4} style={{ color: 'var(--hd-text-muted)', textAlign: 'center', padding: 24 }}>
                  Nenhum scan encontrado.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
