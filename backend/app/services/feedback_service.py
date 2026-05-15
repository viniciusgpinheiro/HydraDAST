import re
import psycopg2
from typing import List, Optional

class FeedbackService:
    def __init__(self, db_connection=None):
        self.conn = db_connection

    def obter_payload_otimizado(self, vetor_nlp: list[float], tipo_ataque: str) -> Optional[str]:
        if not self.conn:
            return None
        try:
            with self.conn.cursor() as cursor:
                # Limpamos a entrada do Python
                categoria_limpa = tipo_ataque.strip().lower()
                
                # Query "Inteligente": Tenta bater a categoria (ignorando case)
                # e ordena pelo vetor. Se o vetor for de zeros, ele pega o primeiro que achar da categoria.
                query = """
                SELECT payload
                FROM public.cache_payloads
                WHERE LOWER(tipo_ataque) = %s
                ORDER BY embedding_semantico <=> %s::vector
                LIMIT 1;
                """
                
                # Convertemos a lista de floats para o formato string [0.1, 0.2...] que o pgvector entende
                vetor_str = "[" + ",".join(map(str, vetor_nlp)) + "]"
                
                cursor.execute(query, (categoria_limpa, vetor_str))
                resultado = cursor.fetchone()
                
                if resultado:
                    return resultado[0]
                return None
        except Exception as e:
            print(f"[!] Erro na busca do payload: {e}")
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