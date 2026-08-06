import asyncio
import os
import re

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import Json

from services.crawler import run_smart_crawler
from services.nlp_service import NLPService
from services.feedback_service import FeedbackService
from services.input_classifier import classificar_campo_hibrido


def _safe_ident(name: str) -> str:
    if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", name):
        raise ValueError(f"Identificador SQL inválido: {name}")
    return name


def _find_table_by_required_columns(cur, required_cols: set[str], schema: str = "public") -> str:
    cur.execute(
        """
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = %s
        """,
        (schema,),
    )
    rows = cur.fetchall()

    columns_by_table: dict[str, set[str]] = {}
    for table_name, column_name in rows:
        columns_by_table.setdefault(table_name, set()).add(column_name)

    for table_name, cols in columns_by_table.items():
        if required_cols.issubset(cols):
            return table_name

    available = ", ".join(sorted(columns_by_table.keys())) or "(nenhuma tabela no schema public)"
    raise RuntimeError(
        f"Não encontrei tabela com colunas {sorted(required_cols)}. Tabelas disponíveis: {available}"
    )


def _to_pgvector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(f"{float(x):.8f}" for x in embedding) + "]"


def main() -> None:
    load_dotenv()
    conn_string = os.getenv("DATABASE_URL")
    db_schema = os.getenv("HYDRA_DB_SCHEMA", "public")
    if not conn_string:
        raise RuntimeError("Defina DATABASE_URL no .env")

    url_vulneravel = "https://the-internet.herokuapp.com/login"

    resultado = asyncio.run(run_smart_crawler(url_vulneravel))
    nlp = NLPService()
    lista_com_vetores = nlp.process_page(resultado)

    for res in lista_com_vetores:
        print(f"Campo: {res['input_original'].html_name} -> Vetor de {len(res['embedding'])} posições.")

    with psycopg2.connect(conn_string) as conn:
        feedback_engine = FeedbackService(db_connection=conn)
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print(f"Conectado ao banco de dados: {version[0]}")

            cur.execute("SELECT COUNT(*) FROM public.cache_payloads;")
            total = cur.fetchone()[0]
            print(f"[DEBUG] Total de payloads na tabela cache_payloads: {total}")

            tabela_usuario = _find_table_by_required_columns(
                cur, {"nome", "email", "senha_hash", "chave_api", "limite_requisicoes"}, schema=db_schema,
            )
            tabela_teste = _find_table_by_required_columns(
                cur, {"id_usuario", "url_alvo", "linguagem", "login_info", "status"}, schema=db_schema,
            )
            tabela_resultado_nlp = _find_table_by_required_columns(
                cur, {"id_teste", "classificacao_sugerida", "embedding_semantico", "conteudo_extraido"}, schema=db_schema,
            )

            tabela_usuario = _safe_ident(tabela_usuario)
            tabela_teste = _safe_ident(tabela_teste)
            tabela_resultado_nlp = _safe_ident(tabela_resultado_nlp)

            inseridos = 0
            for res in lista_com_vetores:
                input_original = res["input_original"]
                embedding = res["embedding"]
                nome_campo = input_original.html_name or "(campo sem nome)"

                resultado_ia = feedback_engine.classificar_e_obter_payload_por_ia(embedding)

                if resultado_ia:
                    categoria = resultado_ia["categoria_ia"]
                    payload_alvo = resultado_ia["payload"]
                    distancia = resultado_ia["distancia"]

                    print(f"\n[CLASSIFICAÇÃO VIA PGVECTOR]")
                    print(f"|> Campo Detectado: {nome_campo}")
                    print(f"|> Categoria IA: {categoria} (Distância: {distancia:.4f})")
                    print(f"|> Payload Escolhido: {payload_alvo}")

                    # Exemplo de uso — troque pelos valores reais retornados
                    # ao efetivamente submeter payload_alvo no formulário alvo.
                    status_simulado = 200
                    html_simulado = "<html>...</html>"

                    resultado_analise = feedback_engine.analisar_resposta(
                        status_simulado, html_simulado, payload=payload_alvo
                    )
                    print(f"|> Classificação: {resultado_analise['classificacao']} "
                        f"(recompensa: {resultado_analise['recompensa']})")
                else:
                    print(f"\n[!] Nenhuma categoria semântica correspondente para o campo {nome_campo}")

                inseridos += 1

            print(f"Registros NLP inseridos: {inseridos}")


if __name__ == "__main__":
    main()