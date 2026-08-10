import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search } from 'lucide-react';
import { listarScans } from '../api';
import { StatusBadge, RiscoBadge } from '../components/Badge';
import { formatData, statusLabel } from '../lib/format';

export default function Relatorios() {
  const [q, setQ] = useState('');
  const [scans, setScans] = useState(null);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    listarScans().then(setScans).catch((e) => setErro(e.message));
  }, []);

  const filtrados = useMemo(
    () => (scans || []).filter((s) => s.url.toLowerCase().includes(q.toLowerCase())),
    [scans, q],
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

      {erro && (
        <div className="hd-card" style={{ color: 'var(--hd-critical)' }}>
          Não foi possível carregar os relatórios: {erro}. O backend está rodando?
        </div>
      )}

      {!erro && (
        <div className="hd-card">
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
              {filtrados.map((s) => (
                <tr key={s.id}>
                  <td><Link to={`/relatorios/${s.id}`}>{s.url}</Link></td>
                  <td style={{ color: 'var(--hd-text-muted)' }}>{formatData(s.criadoEm)}</td>
                  <td><StatusBadge value={statusLabel(s.status)} /></td>
                  <td><RiscoBadge value={s.risco} /></td>
                </tr>
              ))}
              {scans === null && (
                <tr>
                  <td colSpan={4} style={{ color: 'var(--hd-text-muted)', textAlign: 'center', padding: 24 }}>
                    Carregando…
                  </td>
                </tr>
              )}
              {scans !== null && filtrados.length === 0 && (
                <tr>
                  <td colSpan={4} style={{ color: 'var(--hd-text-muted)', textAlign: 'center', padding: 24 }}>
                    Nenhum scan encontrado. <Link to="/novo-scan">Inicie um novo escaneamento</Link>.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
