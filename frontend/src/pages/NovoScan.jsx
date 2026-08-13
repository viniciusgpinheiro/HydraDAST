import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, Loader2, Circle } from 'lucide-react';
import { motores, MOTORES_SUPORTADOS } from '../data/motores';
import { iniciarScan, obterScan } from '../api';

function EtapaIcon({ status }) {
  if (status === 'done') return <Check size={18} className="status-icon sev-safe" />;
  if (status === 'running') return <Loader2 size={18} className="status-icon sev-medium hd-spin" />;
  return <Circle size={16} className="status-icon" style={{ color: 'var(--hd-text-muted)' }} />;
}

export default function NovoScan() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ url: '', linguagem: '', login: '', senha: '' });
  const [selecionados, setSelecionados] = useState({ sql: true, xss: true, header: true });
  const [rodando, setRodando] = useState(false);
  const [scanId, setScanId] = useState(null);
  const [etapas, setEtapas] = useState(null);
  const [concluido, setConcluido] = useState(false);
  const [erro, setErro] = useState(null);
  const pollRef = useRef(null);

  const update = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const toggle = (k) => setSelecionados((s) => ({ ...s, [k]: !s[k] }));

  const iniciar = async (e) => {
    e.preventDefault();
    setErro(null);
    setConcluido(false);
    setEtapas(null);

    const motoresSelecionados = Object.keys(selecionados)
      .filter((k) => selecionados[k] && MOTORES_SUPORTADOS.includes(k));

    if (!form.url.trim()) {
      setErro('Informe a URL do alvo.');
      return;
    }

    setRodando(true);
    try {
      const inicial = await iniciarScan({
        url: form.url.trim(),
        linguagem: form.linguagem || null,
        login: form.login || null,
        senha: form.senha || null,
        motores: motoresSelecionados.length ? motoresSelecionados : null,
      });
      setScanId(inicial.id);
      setEtapas(inicial.etapas || []);
    } catch (err) {
      setErro(`Falha ao iniciar o scan: ${err.message}`);
      setRodando(false);
    }
  };

  // Polling: enquanto houver scanId e não concluído, consulta o estado a cada 800ms.
  useEffect(() => {
    if (!scanId || concluido) return undefined;

    const tick = async () => {
      try {
        const estado = await obterScan(scanId);
        setEtapas(estado.etapas || []);
        if (estado.status === 'done') {
          setConcluido(true);
          setRodando(false);
          clearInterval(pollRef.current);
        } else if (estado.status === 'error') {
          setErro(estado.erro || 'Erro durante o scan.');
          setRodando(false);
          clearInterval(pollRef.current);
        }
      } catch (err) {
        setErro(`Falha ao consultar progresso: ${err.message}`);
        setRodando(false);
        clearInterval(pollRef.current);
      }
    };

    tick(); // primeira consulta imediata
    pollRef.current = setInterval(tick, 800);
    return () => clearInterval(pollRef.current);
  }, [scanId, concluido]);

  const etapasExibidas = etapas ?? [];

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
              {motores.map((m) => {
                const suportado = MOTORES_SUPORTADOS.includes(m.key);
                return (
                  <label key={m.key} className="hd-check" style={{ opacity: suportado ? 1 : 0.45 }}>
                    <input
                      type="checkbox"
                      checked={!!selecionados[m.key]}
                      disabled={!suportado}
                      onChange={() => toggle(m.key)}
                    />
                    {m.label}{!suportado && ' (em breve)'}
                  </label>
                );
              })}
            </div>
          </div>

          {erro && (
            <div className="hd-mt-24" style={{ color: 'var(--hd-critical)' }}>
              ⚠ {erro}
            </div>
          )}

          <div className="hd-mt-32">
            <button type="submit" className="hd-btn hd-btn-primary" disabled={rodando}>
              {rodando ? 'Pentest em andamento…' : 'Iniciar pentest'}
            </button>
          </div>
        </div>

        {/* Progresso (atualizado ao vivo via polling) */}
        <div className="hd-card hd-mt-24">
          <div className="hd-section-title">Progresso</div>
          <div className="hd-progress">
            {etapasExibidas.length === 0 && (
              <div className="hd-progress-row" style={{ color: 'var(--hd-text-muted)' }}>
                Aguardando início do pentest…
              </div>
            )}
            {etapasExibidas.map((et) => (
              <div key={et.key} className={`hd-progress-row ${et.status}`}>
                <EtapaIcon status={et.status} />
                {et.label}
              </div>
            ))}
          </div>
        </div>

        <div className="hd-mt-24">
          <button
            type="button"
            className="hd-btn hd-btn-ai"
            disabled={!concluido}
            style={{ opacity: concluido ? 1 : 0.5 }}
            onClick={() => navigate(`/relatorios/${scanId}`)}
          >
            Abrir relatório
          </button>
        </div>
      </form>
    </>
  );
}
