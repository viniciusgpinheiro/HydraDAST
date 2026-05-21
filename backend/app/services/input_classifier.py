import asyncio
import os
import re

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import Json

from services.crawler import run_smart_crawler
from services.nlp_service import NLPService
from services.feedback_service import FeedbackService

def classificar_campo_hibrido(cur, input_obj, embedding_vetor, tabela_nlp, threshold=0.7) -> str:
    """
    Tenta classificar usando o banco de dados (pgvector).
    Se não encontrar similaridade suficiente, usa uma heurística baseada em regras focada em DAST.
    """

    vetor_str = "[" + ",".join(map(str, embedding_vetor)) + "]"
    
    query = f"""
        SELECT classificacao_sugerida,
            (1 - (embedding_semantico <=> %s::vector)) as similaridade
        FROM {tabela_nlp}
        ORDER BY embedding_semantico <=> %s::vector
        LIMIT 1
    """
    
    cur.execute(query, (vetor_str, vetor_str))
    result = cur.fetchone()
    
    # Se encontrou no banco algo com similaridade maior que o threshold (ex: > 70%)
    if result and result[1] > threshold:
        return result[0]
        
    texto = " ".join([
        input_obj.html_name or "",
        input_obj.html_id or "",
        input_obj.label_text or "",
        input_obj.placeholder or "",
        input_obj.type or "",
        input_obj.parent_form_action or ""
    ]).lower()
    
    # Credenciais e Autenticação
    if any(chave in texto for chave in ["senha", "password", "pwd", "pass"]):
        return "credencial_senha"
    if any(chave in texto for chave in ["email", "usuario", "username", "login", "user"]):
        return "credencial_identificador"
        
    # Campos de Busca (Alvos clássicos de XSS e SQLi)
    if any(chave in texto for chave in ["busca", "search", "pesquisa", "query", "q"]):
        return "busca_pesquisa"
        
    # Campos de Texto Longo (Alvos de Stored XSS e HTML Injection)
    if any(chave in texto for chave in ["mensagem", "message", "comentario", "comment", "descricao", "body"]):
        return "contato_mensagem"
        
    # Vazamento ou Injeção em APIs
    if any(chave in texto for chave in ["token", "api", "key", "secret"]):
        return "segredo_api"
        
    # Identificadores do Sistema (Alvos de IDOR / BOLA)
    if input_obj.type == "hidden" or any(chave in texto for chave in ["id", "uuid", "codigo", "code"]):
        return "identificador_oculto"

    # 2.6. Se nada der match
    return "campo_generico"



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

            cur.execute(
                f"SELECT id FROM {tabela_teste} WHERE url_alvo = %s AND id_usuario = %s", 
                (url_vulneravel, id_usuario)
            )
            if cur.fetchone():
                print(f"Aviso: O teste para {url_vulneravel} já existe. Continuando para fins de demonstração...")
            
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
                embedding_literal = _to_pgvector_literal(embedding)
                
                # CHAMANDO A NOVA HEURÍSTICA HÍBRIDA
                classificacao = classificar_campo_hibrido(
                    cur=cur,
                    input_obj=input_original,
                    embedding_vetor=embedding,
                    tabela_nlp=tabela_resultado_nlp
                )

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

                # cur.execute(
                #     f"""
                #     INSERT INTO {tabela_resultado_nlp}
                #     (id_teste, classificacao_sugerida, embedding_semantico, conteudo_extraido)
                #     VALUES (%s, %s, %s::vector, %s)
                #     """,
                #     (id_teste, classificacao, embedding_literal, Json(conteudo_extraido)),
                # )
            conn.commit()
            print(f"Registros NLP inseridos: {inseridos}")

if __name__ == "__main__":
    main()
