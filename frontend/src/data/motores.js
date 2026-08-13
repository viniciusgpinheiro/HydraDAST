// Configuração de UI: motores de ataque oferecidos no formulário.
// (Não são dados de teste — é a lista de opções disponíveis na interface.)

export const motores = [
  { key: 'sql', label: 'SQL Injection' },
  { key: 'xss', label: 'XSS' },
  { key: 'header', label: 'Segurança de header' },
  { key: 'ddos', label: 'DDoS' },
  { key: 'prompt', label: 'Prompt' },
  { key: 'http', label: 'HTTP request' },
];

// Motores efetivamente executáveis pelo backend nesta fase.
export const MOTORES_SUPORTADOS = ['sql', 'xss', 'header'];
