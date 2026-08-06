import re
import logging
from typing import List, Optional

logger = logging.getLogger("HydraDAST.FeedbackService")

class FeedbackService:
    _PADROES_VULNERABILIDADE = re.compile(
        r"SQL syntax|mysql_fetch|PostgreSQL query failed|ORA-00933|"
        r"sqlite3\.OperationalError|quoted string not properly terminated|"
        r"unclosed quotation mark after the character string",
        re.IGNORECASE
    )

    _STATUS_BLOQUEIO_WAF = {403, 406, 429}
    _PADROES_SUCESSO_BYPASS = ["admin", "dashboard", "logout", "welcome"]

    _TABELA_RECOMPENSAS = {
        "VULNERABILIDADE_CONFIRMADA": 20,
        "SUCESSO_BYPASS": 15,
        "POTENCIAL_ERRO_INTERNO": 5,
        "FALHA_RESPOSTA_COMUM": 0,
        "FALHA_GENERICA": -1,
        "BLOQUEADO_PELO_WAF": -10
    }

    def __init__(self, db_connection=None):
        self.conn = db_connection

    def classificar_e_obter_payload_por_ia(self, vetor_nlp: list[float], limite_distancia: float = 0.8) -> dict | None:
        """Busca no pgvector o payload mais próximo semanticamente do campo detectado."""
        if not self.conn:
            return None

        vetor_str = "[" + ",".join(f"{float(x):.8f}" for x in vetor_nlp) + "]"

        query = """
            SELECT tipo_ataque, payload, (embedding_semantico <=> %s::vector) AS distancia
            FROM public.cache_payloads
            WHERE embedding_semantico IS NOT NULL
            ORDER BY embedding_semantico <=> %s::vector ASC
            LIMIT 1;
        """

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (vetor_str, vetor_str))
                resultado = cursor.fetchone()

                if resultado and resultado[2] is not None:
                    tipo_ataque, payload, distancia = resultado
                    distancia = float(distancia) if str(distancia) != 'nan' else 0.0

                    if distancia <= limite_distancia:
                        return {
                            "categoria_ia": tipo_ataque,
                            "payload": payload,
                            "distancia": distancia
                        }
                return None
        except Exception as e:
            logger.error(f"Erro na classificação por IA via pgvector: {e}")
            return None

    def calcular_recompensa(self, classificacao_resultado: str) -> int:
        """Retorna o score de Reinforcement Learning baseado no resultado obtido."""
        return self._TABELA_RECOMPENSAS.get(classificacao_resultado, -2)

    def analisar_resposta(self, status_code: int, response_body: str, payload: Optional[str] = None) -> dict:
        """
        Analisa a resposta HTTP recebida após o envio de um payload e classifica
        o resultado (vulnerabilidade confirmada, bypass, bloqueio de WAF, etc.),
        já retornando a recompensa de RL correspondente.
        """
        response_body = response_body or ""
        corpo_lower = response_body.lower()

        if status_code in self._STATUS_BLOQUEIO_WAF:
            classificacao = "BLOQUEADO_PELO_WAF"
        elif self._PADROES_VULNERABILIDADE.search(response_body):
            classificacao = "VULNERABILIDADE_CONFIRMADA"
        elif any(padrao in corpo_lower for padrao in self._PADROES_SUCESSO_BYPASS):
            classificacao = "SUCESSO_BYPASS"
        elif 500 <= status_code < 600:
            classificacao = "POTENCIAL_ERRO_INTERNO"
        elif status_code in (200, 302):
            classificacao = "FALHA_RESPOSTA_COMUM"
        else:
            classificacao = "FALHA_GENERICA"

        recompensa = self.calcular_recompensa(classificacao)

        logger.info(f"Payload '{payload}' -> {classificacao} (status={status_code}, recompensa={recompensa})")

        return {
            "classificacao": classificacao,
            "recompensa": recompensa,
            "status_code": status_code,
            "payload": payload,
        }