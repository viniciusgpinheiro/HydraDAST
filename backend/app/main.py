import asyncio
import os
import re

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import Json

from services.crawler import run_smart_crawler
from services.nlp_service import NLPService


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


def _classificar_campo(input_obj) -> str:
    texto = " ".join(
        [
            input_obj.html_name or "",
            input_obj.html_id or "",
            input_obj.label_text or "",
            input_obj.placeholder or "",
            input_obj.type or "",
        ]
    ).lower()

    if any(chave in texto for chave in ["senha", "password"]):
        return "credencial_senha"
    if any(chave in texto for chave in ["email", "usuario", "username", "login"]):
        return "credencial_identificador"
    if any(chave in texto for chave in ["token", "api", "key"]):
        return "segredo_api"
    return "campo_generico"


def _to_pgvector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(f"{float(x):.8f}" for x in embedding) + "]"


def main() -> None:
    load_dotenv()
    conn_string = os.getenv("DATABASE_URL")
    db_schema = os.getenv("HYDRA_DB_SCHEMA", "public")
    if not conn_string:
        raise RuntimeError("Defina DATABASE_URL no .env")

    url_vulneravel = "https://the-internet.herokuapp.com/login"

    # 1) Crawler + NLP
    resultado = asyncio.run(run_smart_crawler(url_vulneravel))
    nlp = NLPService()
    lista_com_vetores = nlp.process_page(resultado)

    for res in lista_com_vetores:
        print(f"Campo: {res['input_original'].html_name} -> Vetor de {len(res['embedding'])} posições.")

    # 2) Persistência no banco
    with psycopg2.connect(conn_string) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            print(f"Conectado ao banco de dados: {version[0]}")

            tabela_usuario = _find_table_by_required_columns(
                cur,
                {"nome", "email", "senha_hash", "chave_api", "limite_requisicoes"},
                schema=db_schema,
            )
            tabela_teste = _find_table_by_required_columns(
                cur,
                {"id_usuario", "url_alvo", "linguagem", "login_info", "status"},
                schema=db_schema,
            )
            tabela_resultado_nlp = _find_table_by_required_columns(
                cur,
                {"id_teste", "classificacao_sugerida", "embedding_semantico", "conteudo_extraido"},
                schema=db_schema,
            )

            tabela_usuario = _safe_ident(tabela_usuario)
            tabela_teste = _safe_ident(tabela_teste)
            tabela_resultado_nlp = _safe_ident(tabela_resultado_nlp)

            nome_usuario = os.getenv("HYDRA_USER_NOME", "Usuário Teste Hydra")
            email_usuario = os.getenv("HYDRA_USER_EMAIL", "teste.hydradast@example.com")
            senha_hash = os.getenv("HYDRA_USER_SENHA_HASH", "hash_temporario_substituir")
            chave_api = os.getenv("HYDRA_USER_API_KEY", "")
            limite_requisicoes = int(os.getenv("HYDRA_USER_LIMITE", "100"))
            usuario_existente_id = os.getenv("HYDRA_USER_ID")

            if usuario_existente_id:
                cur.execute(
                    f"SELECT id FROM {tabela_usuario} WHERE id = %s",
                    (usuario_existente_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise RuntimeError(f"HYDRA_USER_ID não encontrado na tabela {tabela_usuario}: {usuario_existente_id}")
                id_usuario = row[0]
            else:
                # Cria/atualiza usuário e pega id
                cur.execute(
                    f"""
                    INSERT INTO {tabela_usuario} (nome, email, senha_hash, chave_api, limite_requisicoes)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (email)
                    DO UPDATE SET
                        nome = EXCLUDED.nome,
                        senha_hash = EXCLUDED.senha_hash,
                        chave_api = EXCLUDED.chave_api,
                        limite_requisicoes = EXCLUDED.limite_requisicoes
                    RETURNING id
                    """,
                    (nome_usuario, email_usuario, senha_hash, chave_api, limite_requisicoes),
                )
                id_usuario = cur.fetchone()[0]
            print(f"Usuário para teste: {id_usuario}")

            # Sempre cria um NOVO teste para a URL
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
                classificacao = _classificar_campo(input_original)
                embedding_literal = _to_pgvector_literal(embedding)

                conteudo_extraido = {
                    "html_name": input_original.html_name,
                    "html_id": input_original.html_id,
                    "html_class": input_original.html_class,
                    "type": input_original.type,
                    "value": input_original.value,
                    "placeholder": input_original.placeholder,
                    "label_text": input_original.label_text,
                    "title": input_original.title,
                    "aria_label": input_original.aria_label,
                    "maxlength": input_original.maxlength,
                    "minlength": input_original.minlength,
                    "required": input_original.required,
                    "disabled": input_original.disabled,
                    "parent_form_id": input_original.parent_form_id,
                    "parent_form_action": input_original.parent_form_action,
                    "parent_form_method": input_original.parent_form_method,
                }

                cur.execute(
                    f"""
                    INSERT INTO {tabela_resultado_nlp}
                    (id_teste, classificacao_sugerida, embedding_semantico, conteudo_extraido)
                    VALUES (%s, %s, %s::vector, %s)
                    """,
                    (id_teste, classificacao, embedding_literal, Json(conteudo_extraido)),
                )
                inseridos += 1

            conn.commit()
            print(f"Registros NLP inseridos: {inseridos}")


if __name__ == "__main__":
    main()