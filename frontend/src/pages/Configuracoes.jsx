import { useState } from 'react';
import { Link, MoveRight } from 'lucide-react';
import { configuracoes, mapeamento } from '../data/mock';

const iconMap = { 'Lucide Link': Link, MoveRight };

export default function Configuracoes() {
  const [cfg, setCfg] = useState(configuracoes);
  const update = (k) => (e) => setCfg((c) => ({ ...c, [k]: e.target.value }));

  return (
    <>
      <h1 className="hd-page-title">Configurações</h1>

      <div className="hd-card">
        <div style={{ marginBottom: 20 }}>
          <label className="hd-label" htmlFor="chave">Chave de api</label>
          <input id="chave" className="hd-input" value={cfg.chaveApi} onChange={update('chaveApi')} />
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
      </div>

      <div className="hd-mt-32">
        <div className="hd-section-title">Tabela de mapeamento</div>
        <table className="hd-table bordered">
          <thead>
            <tr>
              <th>Entrada Identificada</th>
              <th>Ícone de Conexão</th>
              <th>Significado Semântico</th>
              <th>Confiança</th>
            </tr>
          </thead>
          <tbody>
            {mapeamento.map((row) => {
              const Icon = iconMap[row.icone] || Link;
              return (
                <tr key={row.entrada}>
                  <td style={{ fontFamily: 'ui-monospace, monospace' }}>{row.entrada}</td>
                  <td>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, color: 'var(--hd-brand)' }}>
                      <Icon size={16} /> {row.icone}
                    </span>
                  </td>
                  <td style={{ fontFamily: 'ui-monospace, monospace', color: 'var(--hd-ai-2)' }}>{row.semantica}</td>
                  <td className="sev-safe">{row.confianca}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
