import { useEffect, useState } from 'react';
import { obterConfig, salvarConfig } from '../api';

export default function Configuracoes() {
  const [cfg, setCfg] = useState(null);
  const [erro, setErro] = useState(null);
  const [salvando, setSalvando] = useState(false);
  const [salvo, setSalvo] = useState(false);

  useEffect(() => {
    obterConfig().then(setCfg).catch((e) => setErro(e.message));
  }, []);

  const update = (k) => (e) => {
    setSalvo(false);
    setCfg((c) => ({ ...c, [k]: e.target.value }));
  };

  const salvar = async () => {
    setSalvando(true);
    setErro(null);
    try {
      const atualizado = await salvarConfig({
        chaveApi: cfg.chaveApi,
        respostaLLM: cfg.respostaLLM,
        limiteRequisicoes: Number(cfg.limiteRequisicoes),
      });
      setCfg(atualizado);
      setSalvo(true);
    } catch (e) {
      setErro(e.message);
    } finally {
      setSalvando(false);
    }
  };

  if (erro && !cfg) {
    return (
      <>
        <h1 className="hd-page-title">Configurações</h1>
        <div className="hd-card" style={{ color: 'var(--hd-critical)' }}>
          Não foi possível carregar as configurações: {erro}. O backend está rodando?
        </div>
      </>
    );
  }

  if (!cfg) {
    return (
      <>
        <h1 className="hd-page-title">Configurações</h1>
        <div className="hd-card">Carregando…</div>
      </>
    );
  }

  return (
    <>
      <h1 className="hd-page-title">Configurações</h1>

      <div className="hd-card">
        <div style={{ marginBottom: 20 }}>
          <label className="hd-label" htmlFor="chave">Chave de api</label>
          <input id="chave" className="hd-input" placeholder="Cole sua chave…" value={cfg.chaveApi} onChange={update('chaveApi')} />
        </div>

        <div className="hd-grid-2">
          <div>
            <label className="hd-label" htmlFor="llm">Resposta com LLM</label>
            <select id="llm" className="hd-select" value={cfg.respostaLLM} onChange={update('respostaLLM')}>
              <option value="ativado">ativado</option>
              <option value="desativado">desativado</option>
            </select>
          </div>
          <div>
            <label className="hd-label" htmlFor="limite">Limites de requisições</label>
            <input id="limite" type="number" className="hd-input" value={cfg.limiteRequisicoes} onChange={update('limiteRequisicoes')} />
          </div>
        </div>

        <div className="hd-mt-32" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <button type="button" className="hd-btn hd-btn-primary" onClick={salvar} disabled={salvando}>
            {salvando ? 'Salvando…' : 'Salvar'}
          </button>
          {salvo && <span className="sev-safe">✓ Configurações salvas.</span>}
          {erro && <span style={{ color: 'var(--hd-critical)' }}>⚠ {erro}</span>}
        </div>
      </div>
    </>
  );
}
