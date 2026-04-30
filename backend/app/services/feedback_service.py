import re
import psycopg2
from typing import List, Optional

class FeedbackService:
    def __init__(self, db_connection=None):
        self.conn = db_connection

    def obter_payload_otimizado(self, vetor_nlp: List[float], tipo_ataque: str) -> Optional[str]:
        """
        Busca no Neon a munição mais próxima do contexto do campo (usando pgvector).
        """
        if not self.conn:
            return None
            
        try:
            with self.conn.cursor() as cursor:
                vetor_str = str(vetor_nlp)
                
                query = """
                SELECT payload
                FROM public.cache_payloads
                WHERE tipo_ataque = %s
                ORDER BY embedding_semantico <=> %s
                LIMIT 1;
                """
                cursor.execute(query, (tipo_ataque, vetor_str))
                resultado = cursor.fetchone()
                return resultado[0] if resultado else None
        except Exception as e:
            print(f"[!] Erro ao buscar payload no Neon: {e}")
            return None

    def analisar_resposta(self, status_code: int, html_content: str) -> str:

        padroes_vulnerabilidade = [
            r"SQL syntax", r"mysql_fetch", r"PostgreSQL query failed",
            r"ORA-00933", r"sqlite3.OperationalError", r"quoted string not properly terminated",
            r"unclosed quotation mark after the character string"
        ]

        # 1. Checa Erros Expostos no HTML (Regex)
        for padrao in padroes_vulnerabilidade:
            if re.search(padrao, html_content, re.IGNORECASE):
                return "VULNERABILIDADE_CONFIRMADA"

        # 2. Checa Bloqueios de Segurança
        if status_code in [403, 406, 429]:
            return "BLOQUEADO_PELO_WAF"

        # 3. Checa Comportamento de Sucesso (Ex: Login Bypass)
        if status_code == 200:
            padroes_sucesso = ["admin", "dashboard", "logout", "welcome"]
            if any(p in html_content.lower() for p in padroes_sucesso):
                return "SUCESSO_BYPASS"
            return "FALHA_RESPOSTA_COMUM"

        # 4. Erros de Servidor (Podem indicar algo, mas são inconclusivos)
        if status_code == 500:
            return "POTENCIAL_ERRO_INTERNO"

        return "FALHA_GENERICA"

    def calcular_recompensa(self, classificacao_resultado: str) -> int:

        tabela_pontos = {
            "VULNERABILIDADE_CONFIRMADA": 20,
            "SUCESSO_BYPASS": 15,
            "POTENCIAL_ERRO_INTERNO": 5,
            "FALHA_RESPOSTA_COMUM": 0,
            "FALHA_GENERICA": -1,
            "BLOQUEADO_PELO_WAF": -10 # Punição alta para evitar detecção
        }
        return tabela_pontos.get(classificacao_resultado, -2)