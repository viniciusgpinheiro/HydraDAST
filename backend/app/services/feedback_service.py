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
        """Busca o payload mais adequado combinando similaridade semântica + histórico de eficácia (RL)."""
        if not self.conn:
            return None

        vetor_str = "[" + ",".join(f"{float(x):.8f}" for x in vetor_nlp) + "]"

        # score_confianca começa em 0.5 (neutro). PESO_RL controla o quanto o
        # histórico de eficácia pesa vs. a similaridade semântica pura.
        PESO_RL = 0.15

        query = """
            SELECT id, tipo_ataque, payload, score_confianca,
                   (embedding_semantico <=> %s::vector) AS distancia
            FROM public.cache_payloads
            WHERE embedding_semantico IS NOT NULL
            ORDER BY (embedding_semantico <=> %s::vector) - (%s * (score_confianca - 0.5)) ASC
            LIMIT 1;
        """

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (vetor_str, vetor_str, PESO_RL))
                resultado = cursor.fetchone()

                if resultado:
                    payload_id, tipo_ataque, payload, score_confianca, distancia = resultado
                    distancia = float(distancia) if str(distancia) != 'nan' else 0.0

                    if distancia <= limite_distancia:
                        return {
                            "payload_id": payload_id,
                            "categoria_ia": tipo_ataque,
                            "payload": payload,
                            "score_confianca": float(score_confianca),
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

    def atualizar_score_confianca(self, payload_id: str, recompensa: int, taxa_aprendizado: float = 0.05) -> float | None:
        """
        Aplica a recompensa do RL ao score_confianca do payload usado.
        Recompensa é normalizada para o intervalo [-1, 1] (maior recompensa possível é 20),
        aplicada com uma taxa de aprendizado, e o score fica sempre entre 0.0 e 1.0.
        """
        if not self.conn:
            return None

        recompensa_normalizada = max(-1.0, min(1.0, recompensa / 20))

        query = """
            UPDATE public.cache_payloads
            SET score_confianca = GREATEST(0.0, LEAST(1.0,
                score_confianca + %s * %s
            ))
            WHERE id = %s
            RETURNING score_confianca;
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (taxa_aprendizado, recompensa_normalizada, payload_id))
                novo_score = cursor.fetchone()[0]
                self.conn.commit()
                logger.info(f"[RL] Score do payload {payload_id} atualizado para {novo_score:.4f}")
                return float(novo_score)
        except Exception as e:
            logger.error(f"Erro ao atualizar score_confianca: {e}")
            self.conn.rollback()
            return None