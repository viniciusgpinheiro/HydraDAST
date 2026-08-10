// Realce de sintaxe leve para Python — sem dependências.
// Cobre comentários (#), strings ("..."/'...') e algumas palavras-chave.

const KEYWORDS = ['import', 'from', 'def', 'return', 'for', 'in', 'if', 'else', 'as', 'async', 'await', 'None', 'True', 'False'];
const kwRegex = new RegExp(`\\b(${KEYWORDS.join('|')})\\b`, 'g');

function highlightLine(line, keyPrefix) {
  // 1) separa comentário
  const hashIdx = findComment(line);
  const codePart = hashIdx >= 0 ? line.slice(0, hashIdx) : line;
  const comment = hashIdx >= 0 ? line.slice(hashIdx) : '';

  const nodes = [];
  // 2) strings dentro da parte de código
  const strRegex = /(".*?"|'.*?')/g;
  let last = 0;
  let m;
  let i = 0;
  while ((m = strRegex.exec(codePart)) !== null) {
    if (m.index > last) nodes.push(highlightKeywords(codePart.slice(last, m.index), `${keyPrefix}-t${i++}`));
    nodes.push(<span key={`${keyPrefix}-s${i++}`} className="tok-str">{m[0]}</span>);
    last = m.index + m[0].length;
  }
  if (last < codePart.length) nodes.push(highlightKeywords(codePart.slice(last), `${keyPrefix}-t${i++}`));
  if (comment) nodes.push(<span key={`${keyPrefix}-c`} className="tok-com">{comment}</span>);
  return nodes;
}

// acha o '#' que não está dentro de string
function findComment(line) {
  let inStr = null;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (inStr) {
      if (ch === inStr) inStr = null;
    } else if (ch === '"' || ch === "'") {
      inStr = ch;
    } else if (ch === '#') {
      return i;
    }
  }
  return -1;
}

function highlightKeywords(text, keyPrefix) {
  const parts = [];
  let last = 0;
  let m;
  let i = 0;
  kwRegex.lastIndex = 0;
  while ((m = kwRegex.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    parts.push(<span key={`${keyPrefix}-k${i++}`} className="tok-kw">{m[0]}</span>);
    last = m.index + m[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return <span key={keyPrefix}>{parts}</span>;
}

export default function CodeBlock({ code }) {
  const lines = code.split('\n');
  return (
    <div className="hd-code">
      <pre>
        <code>
          {lines.map((ln, idx) => (
            <div key={idx}>{ln ? highlightLine(ln, `l${idx}`) : ' '}</div>
          ))}
        </code>
      </pre>
    </div>
  );
}
