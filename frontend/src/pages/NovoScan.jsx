import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, Loader2, Circle, ExpandIcon } from 'lucide-react';
import { motores, etapasProgresso } from '../data/mock';
import { iniciarPentest } from '../js/main';

const user = "admin";

function EtapaIcon({ status }) {
  if (status === 'done') return <Check size={18} className="status-icon sev-safe" />;
  if (status === 'running') return <Loader2 size={18} className="status-icon sev-medium hd-spin" />;
  return <Circle size={16} className="status-icon" style={{ color: 'var(--hd-text-muted)' }} />;
}

export default function NovoScan() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ url: '', linguagem: '', login: '', senha: '' });
  const [selecionados, setSelecionados] = useState({ SQL_Injection_Master: true, XSS_Master: true });
  const [rodando, setRodando] = useState(false);

  const update = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const toggle = (k) => setSelecionados((s) => ({ ...s, [k]: !s[k] }));

  const todosSelecionados = motores.every((m) => selecionados[m.key]);
  const toggleTodos = () =>
    setSelecionados(todosSelecionados ? {} : Object.fromEntries(motores.map((m) => [m.key, true])));

  const iniciar = async (e) => {
    e.preventDefault();
    setRodando(true);
    try {
      const resultado = await iniciarPentest(user, form.url);
      console.log('Pentest iniciado com sucesso:', resultado);
    } catch (error) {
      console.error('Falha ao iniciar o pentest:', error);
      alert('Não foi possível iniciar o escaneamento.');
    } finally {
      setRodando(false);
    }
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
            <div className="hd-flex-between" style={{ marginBottom: 16 }}>
              <div className="hd-section-title" style={{ marginBottom: 0 }}>Seleção de motores</div>
              <button type="button" className="hd-btn hd-btn-ghost hd-btn-auto" style={{ padding: '6px 12px', fontSize: '0.85rem' }} onClick={toggleTodos}>
                {todosSelecionados ? 'Limpar todos' : 'Selecionar todos'}
              </button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(210px, 1fr))', gap: 14 }}>
              {motores.map((m) => (
                <label key={m.key} className="hd-check" title={m.file}>
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
