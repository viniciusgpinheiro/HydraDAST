import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, Loader2, Circle } from 'lucide-react';
import { motores, etapasProgresso } from '../data/mock';

function EtapaIcon({ status }) {
  if (status === 'done') return <Check size={18} className="status-icon sev-safe" />;
  if (status === 'running') return <Loader2 size={18} className="status-icon sev-medium hd-spin" />;
  return <Circle size={16} className="status-icon" style={{ color: 'var(--hd-text-muted)' }} />;
}

export default function NovoScan() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ url: '', linguagem: '', login: '', senha: '' });
  const [selecionados, setSelecionados] = useState({ sql: true, xss: true });
  const [rodando, setRodando] = useState(false);

  const update = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const toggle = (k) => setSelecionados((s) => ({ ...s, [k]: !s[k] }));

  const iniciar = (e) => {
    e.preventDefault();
    setRodando(true);
  };

  return (
    <>
      <h1 className="hd-page-title">Novo escaneamento</h1>

      <form onSubmit={iniciar}>
        <div className="hd-card">
          <div style={{ marginBottom: 20 }}>
            <label className="hd-label" htmlFor="url">url</label>
            <input id="url" className="hd-input" placeholder="https://exemplo.com" value={form.url} onChange={update('url')} />
          </div>

          <div style={{ marginBottom: 20 }}>
            <label className="hd-label" htmlFor="linguagem">linguagem</label>
            <input id="linguagem" className="hd-input" placeholder="Ex.: Python, PHP, Node.js" value={form.linguagem} onChange={update('linguagem')} />
          </div>

          <fieldset className="hd-fieldset">
            <legend>Configurações de Autenticação</legend>
            <div style={{ marginBottom: 16 }}>
              <label className="hd-label" htmlFor="login">Login</label>
              <input id="login" className="hd-input" value={form.login} onChange={update('login')} />
            </div>
            <div>
              <label className="hd-label" htmlFor="senha">Senha</label>
              <input id="senha" type="password" className="hd-input" value={form.senha} onChange={update('senha')} />
            </div>
          </fieldset>

          <div className="hd-mt-32">
            <div className="hd-section-title">Seleção de motores</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 16 }}>
              {motores.map((m) => (
                <label key={m.key} className="hd-check">
                  <input type="checkbox" checked={!!selecionados[m.key]} onChange={() => toggle(m.key)} />
                  {m.label}
                </label>
              ))}
            </div>
          </div>

          <div className="hd-mt-32">
            <button type="submit" className="hd-btn hd-btn-primary" disabled={rodando}>
              {rodando ? 'Pentest em andamento…' : 'Iniciar pentest'}
            </button>
          </div>
        </div>

        {/* Progresso */}
        <div className="hd-card hd-mt-24">
          <div className="hd-section-title">Progresso</div>
          <div className="hd-progress">
            {etapasProgresso.map((et) => (
              <div key={et.key} className={`hd-progress-row ${et.status}`}>
                <EtapaIcon status={et.status} />
                {et.label}
              </div>
            ))}
          </div>
        </div>

        <div className="hd-mt-24">
          <button type="button" className="hd-btn hd-btn-ai" onClick={() => navigate('/relatorio')}>
            Abrir relatório
          </button>
        </div>
      </form>
    </>
  );
}
