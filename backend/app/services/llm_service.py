"""Geração do relatório final (problema/solução/código) via Gemini.

Liga no toggle "Resposta com LLM" que já existe em Configurações
(`GET/PUT /api/config`, campo `respostaLLM`) e na chave colada no campo
"chaveApi" da mesma tela — com fallback pra variável de ambiente
GEMINI_API_KEY se o campo estiver vazio (útil para testes locais).

Qualquer falha (sem chave, LLM desativado, erro de rede, resposta fora do
formato esperado) devolve None silenciosamente — quem chama mantém o texto
estático da base de conhecimento como fallback, então isso nunca derruba o
scan.
"""

from __future__ import annotations

import json
import os
import re

_PROMPT = """Você é um analista de segurança revisando o resultado de um teste de
intrusão automatizado (DAST). Com base nos dados reais do ataque abaixo, escreva
em português do Brasil uma explicação técnica e objetiva do problema, a solução
recomendada e um trecho de código curto (vulnerável + corrigido).

Tipo de ataque: {ataque}
Campo/parâmetro testado: {parametro}
Payload utilizado: {payload}
Requisição: {metodo} {url}
Resposta obtida: {resposta}
Classificação do resultado: {classificacao}

Responda ESTRITAMENTE em JSON, sem markdown, no formato:
{{"problema": "...", "solucao": "...", "codigo": "..."}}
"""


def _extrair_json(texto: str) -> dict | None:
    texto = texto.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```[a-zA-Z]*\n?|```$", "", texto.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(texto)
    except (ValueError, TypeError):
        return None


def _obter_chave_api() -> str | None:
    try:
        from api.routes.config import _CONFIG
        chave = (_CONFIG.get("chaveApi") or "").strip()
        if chave:
            return chave
    except Exception:  # noqa: BLE001
        pass
    return os.getenv("GEMINI_API_KEY") or None


def _llm_habilitado() -> bool:
    try:
        from api.routes.config import _CONFIG
        return _CONFIG.get("respostaLLM") == "ativado"
    except Exception:  # noqa: BLE001
        return False


def gerar_relatorio_llm(*, ataque: str, parametro: str, payload: str, metodo: str,
                         url: str, resposta: str, classificacao: str) -> dict:
    """Tenta gerar {"problema","solucao","codigo"} via Gemini.

    Retorna sempre um dict com duas chaves:
        - "dados": o texto gerado, ou None se desativado/falhou.
        - "erro": motivo curto da falha, só quando o LLM estava LIGADO e a
          chamada falhou de verdade (None quando está simplesmente desligado
          ou quando gerou com sucesso) — é o que diferencia "desligado" de
          "erro" pra quem exibe isso no relatório.

    Nunca levanta exceção — quem chama sempre recebe uma resposta usável."""
    if not _llm_habilitado():
        return {"dados": None, "erro": None}

    chave = _obter_chave_api()
    if not chave:
        return {"dados": None, "erro": "Chave de API do Gemini não configurada em Configurações."}

    try:
        from google import genai
        from google.genai import types

        # Timeout curto e poucas tentativas: uma falha/lentidão do Gemini nunca
        # pode travar o scan inteiro (o motor já rodou o ataque real; isso é
        # só o texto do relatório, com fallback estático sempre disponível).
        client = genai.Client(
            api_key=chave,
            http_options=types.HttpOptions(
                timeout=12000,
                retry_options=types.HttpRetryOptions(attempts=2, initial_delay=1, max_delay=3),
            ),
        )
        prompt = _PROMPT.format(
            ataque=ataque, parametro=parametro, payload=payload,
            metodo=metodo, url=url, resposta=resposta, classificacao=classificacao,
        )
        resposta_llm = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
        )
        dados = _extrair_json(resposta_llm.text or "")
        if not dados or not all(k in dados for k in ("problema", "solucao", "codigo")):
            return {"dados": None, "erro": "Resposta do Gemini veio fora do formato esperado."}
        return {"dados": dados, "erro": None}
    except Exception as e:  # noqa: BLE001 - nunca derruba o scan por causa do relatório
        motivo = str(e).split("\n")[0][:200]
        print(f"[llm_service] Falha ao gerar relatório via Gemini, mantendo texto estático: {e}")
        return {"dados": None, "erro": motivo}
