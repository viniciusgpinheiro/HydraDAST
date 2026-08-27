// Helpers de formatação/apresentação usados pelas páginas e badges do HydraDAST.

const RISCO_CLASSES = {
  'Crítico': 'critical',
  'Alto': 'high',
  'Médio': 'medium',
  'Baixo': 'safe',
};

const STATUS_LABELS = {
  running: 'Em andamento',
  done: 'Concluído',
  error: 'Erro',
};

const STATUS_CLASSES = {
  'Em andamento': 'running',
  'Concluído': 'safe',
  'Erro': 'critical',
};

export function riscoClass(risco) {
  return RISCO_CLASSES[risco] || 'low';
}

export function statusLabel(status) {
  return STATUS_LABELS[status] || status;
}

export function statusClass(statusLabelValue) {
  return STATUS_CLASSES[statusLabelValue] || 'low';
}

export function formatData(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
