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


def _simular_envio_payload(payload_alvo: str) -> tuple[int, str]:
    """
    STUB TEMPORÁRIO — troque essa função pela integração real do seu colega
    quando ele terminar o módulo de execução de ataques. A assinatura
    (recebe o payload, devolve status_code e html) deve ser mantida igual
    pra não precisar mexer no resto do main.py.
    """
    return 200, "<html>resposta simulada</html>"


def _persistir_resultado(cur, tabela_resultado_nlp, id_teste, input_original, embedding, resultado_ia, resultado_analise):
    embedding_literal = _to_pgvector_literal(embedding)

    conteudo_extraido = {
        "html_name": input_original.html_name,
        "html_id": input_original.html_id,
        "type": input_original.type,
        "payload_id": resultado_ia["payload_id"],
        "payload_usado": resultado_ia["payload"],
        "categoria_ia": resultado_ia["categoria_ia"],
        "distancia": resultado_ia["distancia"],
        "classificacao": resultado_analise["classificacao"],
        "recompensa": resultado_analise["recompensa"],
        "status_code": resultado_analise["status_code"],
    }

    cur.execute(
        f"""
        INSERT INTO {tabela_resultado_nlp}
        (id_teste, classificacao_sugerida, embedding_semantico, conteudo_extraido)
        VALUES (%s, %s, %s::vector, %s)
        """,
        (id_teste, resultado_analise["classificacao"], embedding_literal, Json(conteudo_extraido)),
    )


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

            nome_usuario = os.getenv("HYDRA_USER_NOME", "Usuário Teste Hydra")
            email_usuario = os.getenv("HYDRA_USER_EMAIL", "teste.hydradast@example.com")
            senha_hash = os.getenv("HYDRA_USER_SENHA_HASH", "hash_temporario_substituir")
            chave_api = os.getenv("HYDRA_USER_API_KEY", "")
            limite_requisicoes = int(os.getenv("HYDRA_USER_LIMITE", "100"))

            cur.execute(
                f"""
                INSERT INTO {tabela_usuario} (nome, email, senha_hash, chave_api, limite_requisicoes)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (email)
                DO UPDATE SET nome = EXCLUDED.nome
                RETURNING id
                """,
                (nome_usuario, email_usuario, senha_hash, chave_api, limite_requisicoes),
            )
            id_usuario = cur.fetchone()[0]

            cur.execute(
                f"""
                INSERT INTO {tabela_teste} (id_usuario, url_alvo, linguagem, login_info, status)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (id_usuario, url_vulneravel, "pt-BR", Json({}), "processado"),
            )
            id_teste = cur.fetchone()[0]
            print(f"Novo teste criado: {id_teste}")

            inseridos = 0
            for res in lista_com_vetores:
                input_original = res["input_original"]
                embedding = res["embedding"]
                nome_campo = input_original.html_name or "(campo sem nome)"

                resultado_ia = feedback_engine.classificar_e_obter_payload_por_ia(embedding)

                if not resultado_ia:
                    print(f"\n[!] Nenhuma categoria semântica correspondente para o campo {nome_campo}")
                    continue

                print(f"\n[CLASSIFICAÇÃO VIA PGVECTOR]")
                print(f"|> Campo Detectado: {nome_campo}")
                print(f"|> Categoria IA: {resultado_ia['categoria_ia']} (Distância: {resultado_ia['distancia']:.4f})")
                print(f"|> Payload Escolhido: {resultado_ia['payload']}")

                # TODO: trocar _simular_envio_payload pela função real do seu colega
                status_code, html = _simular_envio_payload(resultado_ia["payload"])

                resultado_analise = feedback_engine.analisar_resposta(
                    status_code, html, payload=resultado_ia["payload"]
                )
                print(f"|> Classificação: {resultado_analise['classificacao']} (recompensa: {resultado_analise['recompensa']})")

                feedback_engine.atualizar_score_confianca(
                    resultado_ia["payload_id"], resultado_analise["recompensa"]
                )

                _persistir_resultado(
                    cur, tabela_resultado_nlp, id_teste, input_original, embedding, resultado_ia, resultado_analise
                )
                conn.commit()
                inseridos += 1

            print(f"Registros NLP inseridos: {inseridos}")


if __name__ == "__main__":
    main()