"""Executor de scan para a integração front <-> back.

Para cada motor (sql/xss), o fluxo "inteligente" roda primeiro:
crawler real (Playwright) -> embedding NLP de cada campo -> seleção de payload
via pgvector + score de RL (`FeedbackService`) -> execução real (`ataques_exec`)
-> classificação da resposta -> atualização do score_confianca (RL).

Se qualquer etapa desse caminho não estiver disponível (sem banco, sem
Playwright, alvo sem formulário reconhecível etc.), cada motor cai de volta
para o comportamento fixo anterior (payload único em `?id=`/`?q=`), então o
scan nunca fica sem resultado por causa da parte "IA".
"""

from __future__ import annotations

import asyncio
import os
import re
import uuid
from datetime import datetime
from urllib.parse import urlparse, urlunparse, urljoin

import requests
from dotenv import load_dotenv

from services.feedback_service import FeedbackService
from services.crawler import run_smart_crawler
from services.ataques_exec import _requisicao_generica
from services.llm_service import gerar_relatorio_llm
from services.attack_categories import BUCKET_SQL, BUCKET_XSS, NOME_EXIBICAO, KB_POR_CATEGORIA, kb_generico

load_dotenv()

_LIMITE_REQUISICOES_PADRAO = 100

_TIPOS_NAO_TESTAVEIS = {"submit", "button", "hidden", "reset", "image", "file"}

_nlp_singleton = None


def _get_nlp():
    """Carrega o NLPService uma única vez por processo (o modelo é pesado)."""
    global _nlp_singleton
    if _nlp_singleton is None:
        try:
            from services.nlp_service import NLPService
            _nlp_singleton = NLPService()
        except Exception as e:  # noqa: BLE001 - degrade para o modo fixo
            print(f"[scan_runner] NLP indisponível, motores usarão o modo fixo: {e}")
            _nlp_singleton = False
    return _nlp_singleton or None


def _abrir_conexao_db():
    conn_string = os.getenv("DATABASE_URL")
    if not conn_string:
        return None
    try:
        import psycopg2
        return psycopg2.connect(conn_string)
    except Exception as e:  # noqa: BLE001 - degrade para o modo fixo
        print(f"[scan_runner] Banco indisponível, RL/pgvector desativado nesta execução: {e}")
        return None


def _crawlear_contexto(url: str):
    """Crawleia a página uma vez por scan e classifica os campos via NLP.

    Retorna None se qualquer etapa falhar (Playwright ausente, alvo sem
    inputs testáveis, etc.) para que os motores caiam no modo fixo.
    """
    nlp = _get_nlp()
    if not nlp:
        return None
    try:
        dados = asyncio.run(run_smart_crawler(url))
    except Exception as e:  # noqa: BLE001
        print(f"[scan_runner] Crawler falhou, caindo para o modo fixo: {e}")
        return None
    if not dados.inputs:
        return None

    campos_com_vetor = nlp.process_page(dados)
    if not campos_com_vetor:
        return None

    grupos: dict[tuple[str, str], list] = {}
    for inp in dados.inputs:
        chave = (inp.parent_form_action or "", (inp.parent_form_method or "GET").upper())
        grupos.setdefault(chave, []).append(inp)

    return {"campos": campos_com_vetor, "grupos": grupos}


def _montar_corpo_formulario(campo, campos_do_form, payload_escolhido: str) -> dict:
    corpo = {}
    for c in campos_do_form:
        if not c.html_name or (c.type or "").lower() in _TIPOS_NAO_TESTAVEIS:
            continue
        corpo[c.html_name] = c.value or "teste123"
    corpo[campo.html_name] = payload_escolhido
    return corpo


def _orcamento_por_rota(numero_rotas: int, limite_requisicoes: int) -> int:
    """n = limite de requisições do teste dividido pelo número de rotas
    (item 2 do pedido). Esse orçamento é depois repartido entre os campos de
    cada rota (uma rota com vários campos, ex. login com usuário+senha, não
    multiplica o total de requisições)."""
    return max(1, limite_requisicoes // max(1, numero_rotas))


def _atacar_campos_multi(
    url_base: str,
    contexto: dict,
    feedback: FeedbackService,
    categorias_alvo: set[str],
    limite_requisicoes: int,
) -> list[dict]:
    """Generaliza a versão anterior (que atacava só o 1º campo compatível com
    1 payload top-1): percorre TODAS as rotas (grupos de campos por
    form_action+method), calcula o orçamento de ataques por rota (`n` =
    limite_requisicoes // número de rotas) repartido entre os campos
    testáveis daquela rota, e pede à IA os `n` melhores payloads — dentre as
    categorias de `categorias_alvo`, o universo "i" daquele bucket — para
    cada campo (item 3 do pedido: `FeedbackService.escolher_top_n_payloads`).

    Executa cada payload escolhido, classifica a resposta e atualiza o score
    de RL. Retorna a lista de vulnerabilidades encontradas (pode ter mais de
    uma por campo, ou nenhuma, se banco/crawler indisponíveis)."""
    grupos = contexto["grupos"]
    orcamento_rota = _orcamento_por_rota(len(grupos), limite_requisicoes)
    emb_por_campo = {id(item["input_original"]): item["embedding"] for item in contexto["campos"]}

    resultados: list[dict] = []
    for campos_do_form in grupos.values():
        campos_testaveis = [
            c for c in campos_do_form
            if c.html_name and (c.type or "").lower() not in _TIPOS_NAO_TESTAVEIS
        ]
        if not campos_testaveis:
            continue
        orcamento_campo = max(1, orcamento_rota // len(campos_testaveis))

        metodo_form = (campos_testaveis[0].parent_form_method or "GET").upper()
        if metodo_form not in ("GET", "POST", "PUT"):
            metodo_form = "POST"
        acao_form = campos_testaveis[0].parent_form_action
        alvo = urljoin(url_base, acao_form) if acao_form else url_base

        for campo in campos_testaveis:
            vetor = emb_por_campo.get(id(campo))
            if vetor is None:
                continue

            candidatos = feedback.escolher_top_n_payloads(vetor, orcamento_campo, categorias=categorias_alvo)
            for candidato in candidatos:
                payload_usado = candidato["payload"]
                injetar_em = candidato.get("ponto_injecao") or ("query" if metodo_form == "GET" else "body")

                if injetar_em == "body":
                    corpo = _montar_corpo_formulario(campo, campos_do_form, payload_usado)
                    resposta = _requisicao_generica(corpo, alvo, metodo_form, injetar_em="body")
                elif injetar_em == "query":
                    resposta = _requisicao_generica(
                        {campo.html_name: payload_usado}, alvo, metodo_form, injetar_em="query"
                    )
                else:
                    resposta = _requisicao_generica(
                        payload_usado, alvo, metodo_form, injetar_em=injetar_em, nome_campo=campo.html_name
                    )

                if resposta.get("erro"):
                    continue

                status_code = resposta.get("status_code", 0)
                corpo_resposta = resposta.get("corpo", "") or ""

                reflexao = payload_usado in corpo_resposta
                if reflexao:
                    classificacao = "VULNERABILIDADE_CONFIRMADA"
                else:
                    classificacao = feedback.analisar_resposta(
                        status_code, corpo_resposta, payload=payload_usado
                    )["classificacao"]

                recompensa = feedback.calcular_recompensa(classificacao)
                feedback.atualizar_score_confianca(candidato["payload_id"], recompensa)

                resposta_txt = f"{metodo_form} {_rota_de(alvo)} - {status_code}" + (
                    " (payload refletido)" if reflexao else ""
                )
                resultados.append({
                    "campo": campo.html_name,
                    "payload": payload_usado,
                    "categoria_ia": candidato["categoria_ia"],
                    "classificacao": classificacao,
                    "resposta_txt": resposta_txt,
                    "url_alvo": alvo,
                    "metodo": metodo_form,
                })

    return resultados


def _persistir_orcamento_teste(conn, url: str, limite_requisicoes: int, numero_rotas: int, orcamento_por_rota: int) -> None:
    """Guarda no banco o orçamento calculado para este teste (itens 2/3):
    limite de requisições em vigor, quantas rotas foram detectadas e quantos
    ataques por rota isso liberou. Descobre a tabela `testes` dinamicamente
    pelas colunas da migração 003 (não há ORM neste projeto) e nunca derruba
    o scan: se a migração ainda não rodou, ou a tabela tiver outra coluna
    NOT NULL que este INSERT mínimo não preenche (ex.: id_usuario), a falha
    é só logada."""
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'public'"
            )
            colunas_por_tabela: dict[str, set[str]] = {}
            for tabela, coluna in cur.fetchall():
                colunas_por_tabela.setdefault(tabela, set()).add(coluna)

            necessarias = {"limite_requisicoes", "numero_rotas_detectadas", "orcamento_por_rota"}
            tabela_testes = next(
                (t for t, cols in colunas_por_tabela.items() if necessarias.issubset(cols)), None
            )
            if not tabela_testes or not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", tabela_testes):
                return

            coluna_url = next(iter({"url", "url_alvo"} & colunas_por_tabela[tabela_testes]), None)

            campos = ["limite_requisicoes", "numero_rotas_detectadas", "orcamento_por_rota"]
            valores = [limite_requisicoes, numero_rotas, orcamento_por_rota]
            if coluna_url:
                campos.append(coluna_url)
                valores.append(url)

            placeholders = ", ".join(["%s"] * len(valores))
            cur.execute(
                f"INSERT INTO {tabela_testes} ({', '.join(campos)}) VALUES ({placeholders})",
                valores,
            )
            conn.commit()
    except Exception as e:  # noqa: BLE001 - nunca deve derrubar o scan
        print(f"[scan_runner] Não foi possível registrar orçamento do teste (rode a migração 003?): {e}")
        conn.rollback()


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


def _kb_para_categoria(categoria_ia: str) -> dict:
    """Texto de fallback (problema/solução/código) para uma categoria de
    `cache_payloads.tipo_ataque`. As duas categorias antigas usam o texto já
    existente em `_BASE_CONHECIMENTO`; as novas (item 1 do pedido) vêm de
    `attack_categories.KB_POR_CATEGORIA`."""
    if categoria_ia in ("credencial_senha", "credencial_identificador"):
        return {**_BASE_CONHECIMENTO["sql"], "ataque": NOME_EXIBICAO.get(categoria_ia, "SQL Injection")}
    if categoria_ia == "campo_generico":
        return {**_BASE_CONHECIMENTO["xss"], "ataque": NOME_EXIBICAO.get(categoria_ia, "XSS")}
    textos = KB_POR_CATEGORIA.get(categoria_ia)
    if not textos:
        return kb_generico(categoria_ia)
    return {"ataque": NOME_EXIBICAO.get(categoria_ia, categoria_ia), **textos}


def _executar_sql(
    url: str, feedback: FeedbackService, contexto: dict | None = None, limite_requisicoes: int = _LIMITE_REQUISICOES_PADRAO
) -> list[dict]:
    kb = _BASE_CONHECIMENTO["sql"]

    if contexto:
        smarts = _atacar_campos_multi(url, contexto, feedback, BUCKET_SQL, limite_requisicoes)
        if smarts:
            return [_montar_vuln_ia("sql", _kb_para_categoria(s["categoria_ia"]), s) for s in smarts]

    # Fallback: nenhum campo de credencial encontrado/classificado -> payload fixo.
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
    return [_montar_vuln("sql", kb, metodo, url, alvo, analise, resposta_txt)]


def _executar_xss(
    url: str, feedback: FeedbackService, contexto: dict | None = None, limite_requisicoes: int = _LIMITE_REQUISICOES_PADRAO
) -> list[dict]:
    kb = _BASE_CONHECIMENTO["xss"]

    if contexto:
        smarts = _atacar_campos_multi(url, contexto, feedback, BUCKET_XSS, limite_requisicoes)
        if smarts:
            return [_montar_vuln_ia("xss", _kb_para_categoria(s["categoria_ia"]), s) for s in smarts]

    # Fallback: nenhum campo genérico/busca encontrado -> payload fixo.
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
    return [_montar_vuln("xss", kb, metodo, url, alvo, {"classificacao": classificacao}, resposta_txt)]


def _executar_header(
    url: str, feedback: FeedbackService, contexto: dict | None = None, limite_requisicoes: int = _LIMITE_REQUISICOES_PADRAO
) -> list[dict]:
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
    return [_montar_vuln("header", kb, metodo, url, url, {"classificacao": classificacao}, resposta_txt)]


def _texto_relatorio(kb, *, ataque, parametro, payload, metodo, url, resposta, classificacao) -> dict:
    """Texto problema/solução/código: tenta o Gemini (se ligado em Configurações)
    e cai pro texto estático da base de conhecimento em qualquer falha.

    Sempre inclui "fonteRelatorio" ('gemini' | 'estatico' | 'erro_llm') pro
    front conseguir avisar quando o LLM estava ligado mas falhou de verdade
    (distinto de simplesmente estar desligado)."""
    resultado = gerar_relatorio_llm(
        ataque=ataque, parametro=parametro, payload=payload, metodo=metodo,
        url=url, resposta=resposta, classificacao=classificacao,
    )
    if resultado["dados"]:
        return {**resultado["dados"], "fonteRelatorio": "gemini"}

    texto = {"problema": kb["problema"], "solucao": kb["solucao"], "codigo": kb["codigo"]}
    if resultado["erro"]:
        texto["fonteRelatorio"] = "erro_llm"
        texto["erroLLM"] = resultado["erro"]
    else:
        texto["fonteRelatorio"] = "estatico"
    return texto


def _montar_vuln(vid, kb, metodo, url_base, url_alvo, analise, resposta_txt) -> dict:
    classificacao = analise.get("classificacao", "FALHA_GENERICA")
    risco = _CLASSIFICACAO_PARA_RISCO.get(classificacao, "Baixo")
    texto = _texto_relatorio(
        kb, ataque=kb["ataque"], parametro=kb["parametro"], payload=kb["payload"],
        metodo=metodo, url=url_alvo, resposta=resposta_txt, classificacao=classificacao,
    )
    return {
        "id": vid,
        "ataque": kb["ataque"],
        "metodo": metodo,
        "rota": _rota_de(url_base),
        "risco": risco,
        **texto,
        "ataqueDetalhe": {
            "url": url_alvo,
            "parametro": kb["parametro"],
            "payload": kb["payload"],
            "resposta": resposta_txt,
        },
    }


def _montar_vuln_ia(vid, kb, smart: dict) -> dict:
    """Mesmo formato de `_montar_vuln`, mas com o campo/payload/resposta reais
    escolhidos pelo pipeline de IA (crawler + NLP + pgvector + RL) em vez do
    payload fixo da base de conhecimento.

    Um único motor pode agora gerar várias vulnerabilidades (um por payload
    escolhido pelo orçamento "n"), então o id precisa ser único por entrada
    (o front usa `id` como chave de lista e para controlar o item aberto)."""
    risco = _CLASSIFICACAO_PARA_RISCO.get(smart["classificacao"], "Baixo")
    texto = _texto_relatorio(
        kb, ataque=kb["ataque"], parametro=smart["campo"], payload=smart["payload"],
        metodo=smart["metodo"], url=smart["url_alvo"], resposta=smart["resposta_txt"],
        classificacao=smart["classificacao"],
    )
    return {
        "id": f"{vid}-{uuid.uuid4().hex[:8]}",
        "ataque": kb["ataque"],
        "metodo": smart["metodo"],
        "rota": _rota_de(smart["url_alvo"]),
        "risco": risco,
        **texto,
        "ataqueDetalhe": {
            "url": smart["url_alvo"],
            "parametro": f'{smart["campo"]} (IA: {smart["categoria_ia"]})',
            "payload": smart["payload"],
            "resposta": smart["resposta_txt"],
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


def executar_scan(
    url: str,
    motores: list[str] | None = None,
    on_progress=None,
    scan_id=None,
    limite_requisicoes: int | None = None,
    **_ignorados,
) -> dict:
    """Executa os ataques selecionados, reportando o progresso etapa a etapa.

    `limite_requisicoes` é o número máximo de requisições que o usuário
    escolheu em Configurações para este teste (item 2 do pedido). É
    dividido pelo número de rotas detectadas na página para virar o
    orçamento `n` de ataques por rota/campo (item 2/3), guardado no banco
    junto do teste quando o banco está disponível.

    Se `on_progress` for fornecido, ele é chamado com um snapshot completo do
    scan após cada etapa (para o polling do front). Retorna o relatório final.
    """
    url = _normalizar_url(url)
    limite_requisicoes = limite_requisicoes or _LIMITE_REQUISICOES_PADRAO
    motores = [m for m in (motores or ["sql", "xss", "header"]) if m in _MOTORES]
    if not motores:
        motores = list(_MOTORES.keys())
    scan_id = scan_id or str(uuid.uuid4())

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

    # Etapa de conexão: abre o banco (RL/pgvector) e crawleia a página real
    # (Playwright + NLP) para os motores mirarem nos campos de verdade.
    # Qualquer falha aqui degrada silenciosamente para o modo fixo anterior.
    _set("conexao", "running")
    conn = _abrir_conexao_db()
    feedback = FeedbackService(db_connection=conn)
    contexto = _crawlear_contexto(url) if conn else None
    if conn:
        numero_rotas = len(contexto["grupos"]) if contexto else 1
        orcamento_rota = _orcamento_por_rota(numero_rotas, limite_requisicoes)
        _persistir_orcamento_teste(conn, url, limite_requisicoes, numero_rotas, orcamento_rota)
    _set("conexao", "done")

    # "sql" e "xss" são os únicos motores que gastam do orçamento de
    # cache_payloads; "header" faz sempre 1 requisição fixa e ignora o
    # limite. Se os dois estiverem selecionados, cada um recalcularia o
    # mesmo orçamento por rota a partir do limite total e, juntos,
    # poderiam somar até o dobro do que o usuário escolheu — então o
    # limite é dividido entre eles aqui para o total do teste respeitar
    # de fato o limite_requisicoes configurado.
    motores_com_orcamento = [m for m in motores if m in ("sql", "xss")]
    limite_por_motor = (
        max(1, limite_requisicoes // len(motores_com_orcamento)) if motores_com_orcamento else limite_requisicoes
    )

    try:
        # Executa cada motor selecionado.
        for chave in motores:
            _set(chave, "running")
            limite_motor = limite_por_motor if chave in ("sql", "xss") else limite_requisicoes
            vulnerabilidades.extend(_MOTORES[chave](url, feedback, contexto, limite_motor))
            _set(chave, "done")
    finally:
        if conn:
            conn.close()

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
