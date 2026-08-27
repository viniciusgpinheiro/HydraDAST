// Client HTTP para a API FastAPI do HydraDAST.
// Ajuste a base pela variável VITE_API_URL se o backend rodar em outra porta.

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function req(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    let detalhe = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detalhe = body.detail;
    } catch {
      /* corpo não-JSON */
    }
    throw new Error(detalhe);
  }
  return res.json();
}

// Inicia um scan; devolve o estado inicial { id, status: 'running', ... }.
export function iniciarScan(payload) {
  return req('/api/scans', { method: 'POST', body: JSON.stringify(payload) });
}

// Consulta o estado atual de um scan (usado no polling).
export function obterScan(id) {
  return req(`/api/scans/${id}`);
}

// Lista os scans da sessão.
export function listarScans() {
  return req('/api/scans');
}

// Configurações da aplicação.
export function obterConfig() {
  return req('/api/config');
}

export function salvarConfig(cfg) {
  return req('/api/config', { method: 'PUT', body: JSON.stringify(cfg) });
}
