import re
import logging
from typing import List, Optional

# Configuração simples de log (boa prática para serviços)
logger = logging.getLogger("HydraDAST.FeedbackService")

class FeedbackService:
    #Compila os padrões regex apenas UMA vez na inicialização da classe (ganho de performance)
    _PADROES_VULNERABILIDADE = re.compile(
        r"SQL syntax|mysql_fetch|PostgreSQL query failed|ORA-00933|"
        r"sqlite3\.OperationalError|quoted string not properly terminated|"
        r"unclosed quotation mark after the character string",
        re.IGNORECASE
    )
    
    # Mapeamentos transformados em constantes limpas
    _STATUS_BLOQUEIO_WAF = {403, 406, 429}
    _PADROES_SUCESSO_BYPASS = ["admin", "dashboard", "logout", "welcome"]
    
    _TABELA_RECOMPENSAS = {
        "VULNERABILIDADE_CONFIRMADA": 20,
        "SUCESSO_BYPASS": 15,
        "POTENCIAL_ERRO_INTERNO": 5,
        "FALHA_RESPOSTA_COMUM": 0,
        "FALHA_GENERICA": -1,
        "BLOQUEADO_PELO_WAF": -10  # Punição alta para evitar detecção
    }

    def __init__(self, db_connection=None):
        self.conn = db_connection

    def obter_payload_otimizado(self, vetor_nlp: List[float], tipo_ataque: str) -> Optional[str]:
        """Busca no Neon a munição mais próxima do contexto do campo (usando pgvector)."""
        if not self.conn:
            return None
            
        categoria_limpa = tipo_ataque.strip().lower()
        vetor_str = f"[{','.join(map(str, vetor_nlp))}]"
        
        query = """
            SELECT payload
            FROM public.cache_payloads
            WHERE LOWER(tipo_ataque) = %s
            ORDER BY embedding_semantico <=> %s::vector
            LIMIT 1;
        """
        
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (categoria_limpa, vetor_str))
                resultado = cursor.fetchone()
                return resultado[0] if resultado else None
        except Exception as e:
            logger.error(f"Erro na busca do payload no Neon: {e}")
            return None

    def analisar_resposta(self, status_code: int, html_content: str) -> str:
        """Analisa o comportamento da aplicação alvo para classificar o resultado do ataque."""
        html_lower = html_content.lower()

        #erros Expostos no HTML (Regex unificado e pré-compilado)
        if self._PADROES_VULNERABILIDADE.search(html_content):
            return "VULNERABILIDADE_CONFIRMADA"

        #bloqueios de Segurança (WAF)
        if status_code in self._STATUS_BLOQUEIO_WAF:
            return "BLOQUEADO_PELO_WAF"

        # comportamento de Sucesso (Bypass)
        if status_code == 200:
            if any(padrone in html_lower for padrone in self._PADROES_SUCESSO_BYPASS):
                return "SUCESSO_BYPASS"
            return "FALHA_RESPOSTA_COMUM"

        # erros internos genéricos do servidor
        if status_code == 500:
            return "POTENCIAL_ERRO_INTERNO"

        return "FALHA_GENERICA"

    def calcular_recompensa(self, classificacao_resultado: str) -> int:
        """Retorna o score de Reinforcement Learning baseado no resultado obtido."""
        # O método .get() já aceita um valor padrão (-2) caso a chave não exista
        return self._TABELA_RECOMPENSAS.get(classificacao_resultado, -2)