import { useEffect, useMemo, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Info, ChevronDown, Search } from 'lucide-react';
import { riscoClass } from '../lib/format';
import { obterScan } from '../api';
import BarChart from '../components/BarChart';
import CodeBlock from '../components/CodeBlock';

const ORDEM_RISCO = { 'Crítico': 0, 'Alto': 1, 'Médio': 2, 'Baixo': 3 };

function media(arr) {
  if (!arr || !arr.length) return 0;
  return Math.round(arr.reduce((a, b) => a + b, 0) / arr.length);
}

function VulnItem({ v, aberto, onToggle }) {
  const d = v.ataqueDetalhe;
  return (
    <div className="hd-acc-item">
      <div className="hd-acc-head" onClick={onToggle} role="button" tabIndex={0}
           onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onToggle()}>
        <span className="col-head">{v.ataque}</span>
        <span className="col-head" style={{ color: 'var(--hd-text-muted)' }}>{v.metodo}</span>
        <span className="col-head"><a href="#" onClick={(e) => e.preventDefault()}>{v.rota}</a></span>
        <span className={`col-head sev-${riscoClass(v.risco)}`}>{v.risco}</span>
        <ChevronDown size={18} style={{ color: 'var(--hd-text-muted)', transform: aberto ? 'rotate(180deg)' : 'none', transition: 'transform .15s' }} />
      </div>

      {aberto && (
        <div className="hd-acc-body">
          <h6>Problema</h6>
          <p>&gt; {v.problema}</p>

          <h6>Solução</h6>
          <p>&gt; {v.solucao}</p>

          <CodeBlock code={v.codigo} />

          <h6>Ataque</h6>
          <div className="hd-attack">
            <div><span className="k">url:</span> <a href="#" onClick={(e) => e.preventDefault()}>{d.url}</a></div>
            <div><span className="k">parâmetro:</span> {d.parametro}</div>
            <div><span className="k">payload:</span> {d.payload}</div>
            <div><span className="k">resposta:</span> {d.resposta}</div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Relatorio() {
  const { id } = useParams();
  const [dados, setDados] = useState(null);
  const [carregando, setCarregando] = useState(!!id);
  const [erro, setErro] = useState(null);
  const [aberto, setAberto] = useState(null);
  const [q, setQ] = useState('');
  const [ordem, setOrdem] = useState('risco');

  useEffect(() => {
    if (!id) return;
    let ativo = true;
    setCarregando(true);
    obterScan(id)
      .then((r) => {
        if (!ativo) return;
        setDados({
          url: r.url,
          resumo: r.resumo,
          acuraciaBars: r.acuraciaBars,
          acuracia: media(r.acuraciaBars),
          vulnerabilidades: r.vulnerabilidades || [],
        });
        setAberto((r.vulnerabilidades || [])[0]?.id ?? null);
      })
      .catch((e) => ativo && setErro(e.message))
      .finally(() => ativo && setCarregando(false));
    return () => { ativo = false; };
  }, [id]);

  const lista = useMemo(() => {
    if (!dados) return [];
    let arr = dados.vulnerabilidades.filter(
      (item) => item.ataque.toLowerCase().includes(q.toLowerCase()) || item.rota.toLowerCase().includes(q.toLowerCase()),
    );
    if (ordem === 'risco') arr = [...arr].sort((a, b) => ORDEM_RISCO[a.risco] - ORDEM_RISCO[b.risco]);
    if (ordem === 'ataque') arr = [...arr].sort((a, b) => a.ataque.localeCompare(b.ataque));
    return arr;
  }, [dados, q, ordem]);

  if (!id) {
    return (
      <>
        <h1 className="hd-page-title">Relatório</h1>
        <div className="hd-card" style={{ color: 'var(--hd-text-muted)' }}>
          Nenhum relatório selecionado. Veja a lista em <Link to="/relatorios">Relatórios</Link> ou
          {' '}<Link to="/novo-scan">inicie um novo escaneamento</Link>.
        </div>
      </>
    );
  }

  if (carregando) {
    return (
      <>
        <h1 className="hd-page-title">Relatório</h1>
        <div className="hd-card">Carregando resultado do scan…</div>
      </>
    );
  }

  if (erro) {
    return (
      <>
        <h1 className="hd-page-title">Relatório</h1>
        <div className="hd-card" style={{ color: 'var(--hd-critical)' }}>
          Não foi possível carregar o scan: {erro}
        </div>
      </>
    );
  }

  const { url, resumo: v, acuracia, acuraciaBars } = dados;

  return (
    <>
      <h1 className="hd-page-title">Relatório</h1>

      <div style={{ marginBottom: 24 }}>
        <label className="hd-label">url</label>
        <div className="hd-input" style={{ display: 'flex', alignItems: 'center' }}>
          <a href="#" onClick={(e) => e.preventDefault()}>{url}</a>
        </div>
      </div>

      {/* Cards de resumo */}
      <div className="hd-grid-2">
        <div className="hd-card">
          <div className="hd-card-label">
            Vulnerabilidades encontradas
            <Info size={18} className="hd-info-icon" />
          </div>
          <div className="hd-flex-between" style={{ alignItems: 'flex-start' }}>
            <div>
              <div className="hd-metric">{v.total}</div>
              <div className="hd-metric-sub">{v.nivel}</div>
            </div>
            <div className="hd-breakdown">
              <div className="hd-breakdown-row"><span className="sev-critical">Críticas</span><span className="val sev-critical">{v.criticas}</span></div>
              <div className="hd-breakdown-row"><span className="sev-high">Altas</span><span className="val sev-high">{v.altas}</span></div>
              <div className="hd-breakdown-row"><span className="sev-medium">Médias</span><span className="val sev-medium">{v.medias}</span></div>
              <div className="hd-breakdown-row"><span className="sev-safe">Baixas</span><span className="val sev-safe">{v.baixas}</span></div>
            </div>
          </div>
        </div>

        <div className="hd-card">
          <div className="hd-card-label">
            Acurácia
            <Info size={18} className="hd-info-icon" />
          </div>
          <div className="hd-flex-between" style={{ alignItems: 'center' }}>
            <div className="hd-metric hd-metric-safe">{acuracia}%</div>
            <div style={{ width: 200, height: 120 }}>
              <BarChart values={acuraciaBars} />
            </div>
          </div>
        </div>
      </div>

      {/* Vulnerabilidades */}
      <div className="hd-mt-32">
        <div className="hd-section-title" style={{ fontSize: '1.4rem' }}>Vulnerabilidades</div>

        <div className="hd-flex-between hd-mt-24" style={{ marginBottom: 16 }}>
          <div style={{ position: 'relative', flex: 1, maxWidth: 480 }}>
            <Search size={18} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--hd-text-muted)' }} />
            <input
              className="hd-input"
              style={{ paddingLeft: 42 }}
              placeholder="Pesquisar vulnerabilidade…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </div>
          <select className="hd-select" style={{ width: 220 }} value={ordem} onChange={(e) => setOrdem(e.target.value)}>
            <option value="risco">classificar por: risco</option>
            <option value="ataque">classificar por: ataque</option>
          </select>
        </div>

        <div className="hd-acc-headings">
          <span>ataque</span>
          <span>método</span>
          <span>url</span>
          <span>risco</span>
          <span></span>
        </div>

        <div className="hd-acc">
          {lista.map((item) => (
            <VulnItem
              key={item.id}
              v={item}
              aberto={aberto === item.id}
              onToggle={() => setAberto(aberto === item.id ? null : item.id)}
            />
          ))}
        </div>
      </div>
    </>
  );
}
