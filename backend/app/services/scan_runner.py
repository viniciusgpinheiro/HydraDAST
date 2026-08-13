"""Executor de scan enxuto para a demo de integração front <-> back.

Diferente do pipeline completo (crawler + NLP + pgvector + RL), este módulo
dispara alguns ataques HTTP REAIS contra a URL alvo usando apenas `requests`
e reaproveita a classificação já existente em `FeedbackService.analisar_resposta`
(regex puro, sem banco de dados nem modelos pesados).

O texto de "problema/solução/código" de cada vulnerabilidade vem de uma base de
conhecimento estática; o que é medido de verdade é a requisição enviada e a
resposta do alvo (status, corpo, classificação).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from urllib.parse import urlparse, urlunparse

import requests

from services.feedback_service import FeedbackService


# Mapeia a classificação do FeedbackService para o nível de risco exibido no front.
_CLASSIFICACAO_PARA_RISCO = {
    "VULNERABILIDADE_CONFIRMADA": "Crítico",
    "SUCESSO_BYPASS": "Alto",
    "POTENCIAL_ERRO_INTERNO": "Médio",
    "FALHA_RESPOSTA_COMUM": "Baixo",
    "FALHA_GENERICA": "Baixo",
    "BLOQUEADO_PELO_WAF": "Baixo",
}

_ORDEM_RISCO = {"Crítico": 0, "Alto": 1, "Médio": 2, "Baixo": 3}


# Base de conhecimento estática (remediação). O ataque em si é executado de verdade.
_BASE_CONHECIMENTO = {
    "sql": {
        "ataque": "SQL Injection",
        "parametro": "id",
        "payload": "' OR '1'='1",
        "problema": (
            "O parâmetro é concatenado diretamente na query SQL, permitindo que "
            "um atacante altere a lógica do comando (ex.: ' OR '1'='1) para "
            "burlar filtros ou extrair dados do banco."
        ),
        "solucao": (
            "Utilize queries parametrizadas (prepared statements) para que o valor "
            "seja tratado como dado, nunca como comando."
        ),
        "codigo": (
            "# Vulnerável\n"
            "query = f\"SELECT * FROM users WHERE id = {id_usuario}\"\n\n"
            "# Seguro (parametrizado)\n"
            "cursor.execute(\"SELECT * FROM users WHERE id = ?\", (id_usuario,))"
        ),
    },
    "xss": {
        "ataque": "XSS",
        "parametro": "q",
        "payload": "<script>alert(1)</script>",
        "problema": (
            "Conteúdo do usuário é refletido na página sem sanitização, permitindo "
            "injeção de scripts no navegador da vítima (roubo de sessão, ações em "
            "nome do usuário)."
        ),
        "solucao": (
            "Escape a saída HTML e aplique uma Content-Security-Policy restritiva. "
            "Nunca insira entrada do usuário diretamente no DOM."
        ),
        "codigo": (
            "# Vulnerável\n"
            "resposta = f\"<div>Resultado: {termo}</div>\"\n\n"
            "# Seguro\n"
            "import html\n"
            "resposta = f\"<div>Resultado: {html.escape(termo)}</div>\""
        ),
    },
    "header": {
        "ataque": "Segurança de header",
        "parametro": "—",
        "payload": "Requisição inspecionando cabeçalhos de segurança",
        "problema": (
            "Cabeçalhos de segurança ausentes (X-Frame-Options, X-Content-Type-Options, "
            "Strict-Transport-Security) expõem a aplicação a clickjacking e downgrade "
            "de protocolo."
        ),
        "solucao": (
            "Adicione os cabeçalhos de segurança na camada de resposta (middleware)."
        ),
        "codigo": (
            "@app.middleware(\"http\")\n"
            "async def add_security_headers(request, call_next):\n"
            "    response = await call_next(request)\n"
            "    response.headers[\"X-Frame-Options\"] = \"DENY\"\n"
            "    response.headers[\"X-Content-Type-Options\"] = \"nosniff\"\n"
            "    response.headers[\"Strict-Transport-Security\"] = \"max-age=31536000\"\n"
            "    return response"
        ),
    },
}

# Cabeçalhos de segurança verificados no motor "header".
_HEADERS_SEGURANCA = [
    "x-frame-options",
    "x-content-type-options",
    "strict-transport-security",
    "content-security-policy",
]


def _normalizar_url(url: str) -> str:
    if not url:
        raise ValueError("URL vazia")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def _rota_de(url: str) -> str:
    caminho = urlparse(url).path or "/"
    return caminho


def _com_query(url: str, param: str, valor: str) -> str:
    partes = urlparse(url)
    query = f"{param}={valor}"
    nova = partes._replace(query=query)
    return urlunparse(nova)


def _executar_sql(url: str, feedback: FeedbackService) -> dict:
    kb = _BASE_CONHECIMENTO["sql"]
    alvo = _com_query(url, kb["parametro"], kb["payload"])
    try:
        r = requests.get(alvo, timeout=8, headers={"User-Agent": "HydraDAST/1.0"})
        analise = feedback.analisar_resposta(r.status_code, r.text, payload=kb["payload"])
        resposta_txt = f"GET {_rota_de(alvo)} - {r.status_code}"
        metodo = "GET"
    except requests.exceptions.RequestException as e:
        analise = {"classificacao": "FALHA_GENERICA"}
        resposta_txt = f"Falha de rede: {e}"
        metodo = "GET"
    return _montar_vuln("sql", kb, metodo, url, alvo, analise, resposta_txt)


def _executar_xss(url: str, feedback: FeedbackService) -> dict:
    kb = _BASE_CONHECIMENTO["xss"]
    alvo = _com_query(url, kb["parametro"], kb["payload"])
    reflexao = False
    try:
        r = requests.get(alvo, timeout=8, headers={"User-Agent": "HydraDAST/1.0"})
        reflexao = kb["payload"] in r.text
        # Reflexão do payload sem escape é indício direto de XSS.
        if reflexao:
            classificacao = "VULNERABILIDADE_CONFIRMADA"
        else:
            analise = feedback.analisar_resposta(r.status_code, r.text, payload=kb["payload"])
            classificacao = analise["classificacao"]
        resposta_txt = f"GET {_rota_de(alvo)} - {r.status_code}" + (
            " (payload refletido)" if reflexao else ""
        )
        metodo = "GET"
    except requests.exceptions.RequestException as e:
        classificacao = "FALHA_GENERICA"
        resposta_txt = f"Falha de rede: {e}"
        metodo = "GET"
    return _montar_vuln("xss", kb, metodo, url, alvo, {"classificacao": classificacao}, resposta_txt)


def _executar_header(url: str, feedback: FeedbackService) -> dict:
    kb = _BASE_CONHECIMENTO["header"]
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": "HydraDAST/1.0"})
        presentes = {h.lower() for h in r.headers.keys()}
        faltando = [h for h in _HEADERS_SEGURANCA if h not in presentes]
        if faltando:
            classificacao = "POTENCIAL_ERRO_INTERNO"  # -> Médio
            resposta_txt = f"GET {_rota_de(url)} - {r.status_code} (faltando: {', '.join(faltando)})"
        else:
            classificacao = "FALHA_RESPOSTA_COMUM"  # -> Baixo (protegido)
            resposta_txt = f"GET {_rota_de(url)} - {r.status_code} (todos os cabeçalhos presentes)"
        metodo = "GET"
    except requests.exceptions.RequestException as e:
        classificacao = "FALHA_GENERICA"
        resposta_txt = f"Falha de rede: {e}"
        metodo = "GET"
    return _montar_vuln("header", kb, metodo, url, url, {"classificacao": classificacao}, resposta_txt)


def _montar_vuln(vid, kb, metodo, url_base, url_alvo, analise, resposta_txt) -> dict:
    risco = _CLASSIFICACAO_PARA_RISCO.get(analise.get("classificacao", "FALHA_GENERICA"), "Baixo")
    return {
        "id": vid,
        "ataque": kb["ataque"],
        "metodo": metodo,
        "rota": _rota_de(url_base),
        "risco": risco,
        "problema": kb["problema"],
        "solucao": kb["solucao"],
        "codigo": kb["codigo"],
        "ataqueDetalhe": {
            "url": url_alvo,
            "parametro": kb["parametro"],
            "payload": kb["payload"],
            "resposta": resposta_txt,
        },
    }


_MOTORES = {
    "sql": _executar_sql,
    "xss": _executar_xss,
    "header": _executar_header,
}

_LABEL_MOTOR = {
    "sql": "SQL Injection",
    "xss": "XSS",
    "header": "Segurança de header",
}


def _snapshot(scan_id, url, status, etapas, vulnerabilidades):
    """Estado atual do scan, no formato consumido pelo front."""
    resumo = _resumir(url, vulnerabilidades)
    return {
        "id": scan_id,
        "url": url,
        "criadoEm": datetime.now().isoformat(timespec="seconds"),
        "status": status,  # "running" | "done" | "error"
        "etapas": etapas,
        "resumo": resumo,
        "acuraciaBars": _acuracia_bars(vulnerabilidades),
        "vulnerabilidades": sorted(
            vulnerabilidades, key=lambda v: _ORDEM_RISCO.get(v["risco"], 3)
        ),
    }


def executar_scan(url: str, motores: list[str] | None = None, on_progress=None, scan_id=None, **_ignorados) -> dict:
    """Executa os ataques selecionados, reportando o progresso etapa a etapa.

    Se `on_progress` for fornecido, ele é chamado com um snapshot completo do
    scan após cada etapa (para o polling do front). Retorna o relatório final.
    """
    url = _normalizar_url(url)
    motores = [m for m in (motores or ["sql", "xss", "header"]) if m in _MOTORES]
    if not motores:
        motores = list(_MOTORES.keys())
    scan_id = scan_id or str(uuid.uuid4())
    feedback = FeedbackService(db_connection=None)

    # Monta as etapas: conexão -> um passo por motor -> relatório.
    etapas = [{"key": "conexao", "label": "Conectando ao alvo", "status": "pending"}]
    for m in motores:
        etapas.append({"key": m, "label": _LABEL_MOTOR[m], "status": "pending"})
    etapas.append({"key": "relatorio", "label": "Gerando relatório", "status": "pending"})

    vulnerabilidades: list[dict] = []

    def _set(chave, status):
        for et in etapas:
            if et["key"] == chave:
                et["status"] = status
        if on_progress:
            estado = "done" if chave == "relatorio" and status == "done" else "running"
            on_progress(_snapshot(scan_id, url, estado, etapas, vulnerabilidades))

    # Etapa de conexão.
    _set("conexao", "running")
    _set("conexao", "done")

    # Executa cada motor selecionado.
    for chave in motores:
        _set(chave, "running")
        vulnerabilidades.append(_MOTORES[chave](url, feedback))
        _set(chave, "done")

    # Relatório final.
    _set("relatorio", "running")
    _set("relatorio", "done")

    return _snapshot(scan_id, url, "done", etapas, vulnerabilidades)


def _resumir(url: str, vulns: list[dict]) -> dict:
    contagem = {"Crítico": 0, "Alto": 0, "Médio": 0, "Baixo": 0}
    for v in vulns:
        contagem[v["risco"]] = contagem.get(v["risco"], 0) + 1

    relevantes = sum(1 for v in vulns if v["risco"] in ("Crítico", "Alto", "Médio"))
    if contagem["Crítico"]:
        nivel = "Risco crítico"
    elif contagem["Alto"]:
        nivel = "Risco alto"
    elif contagem["Médio"]:
        nivel = "Risco moderado"
    else:
        nivel = "Risco baixo"

    return {
        "url": url,
        "total": relevantes,
        "nivel": nivel,
        "criticas": contagem["Crítico"],
        "altas": contagem["Alto"],
        "medias": contagem["Médio"],
        "baixas": contagem["Baixo"],
    }


def _acuracia_bars(vulns: list[dict]) -> list[int]:
    # Placeholder visual derivado dos riscos encontrados (o modelo de eficácia
    # real — XGBoost — entra numa etapa posterior).
    peso = {"Crítico": 95, "Alto": 80, "Médio": 60, "Baixo": 40}
    base = [peso.get(v["risco"], 40) for v in vulns] or [50]
    barras = []
    for i in range(12):
        barras.append(base[i % len(base)])
    return barras
