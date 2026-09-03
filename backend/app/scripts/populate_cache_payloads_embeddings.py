import os, psycopg2
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()
conn_str = os.getenv('DATABASE_URL')

# MESMO modelo usado no NLPService — senão as distâncias não fazem sentido
model = SentenceTransformer('all-MiniLM-L6-v2')

# Descrição em linguagem natural de cada categoria — precisa "soar" parecido
# com o texto que o NLPService gera pros campos do form (name/id/label/placeholder/type)
DESCRICOES_POR_TIPO = {
    "credencial_identificador": "name:username id:username label:usuário login email placeholder:usuário type:text",
    "credencial_senha": "name:password id:password label:senha placeholder:senha type:password",
    "campo_generico": "name:search id:comment label:campo de texto genérico busca comentário type:text",
    # Categorias novas (item 1 do pedido) — não mapeiam pra um TIPO de campo
    # específico como as 3 acima, então a descrição foca no tipo de
    # parâmetro/uso onde aquele ataque costuma ser efetivo. A diferenciação
    # fina entre elas fica por conta do score_confianca (RL) ao longo dos scans.
    "sqli": "name:id name:search campo de texto genérico id busca filtro parâmetro de consulta ao banco de dados",
    "nosqli": "name:username name:filter campo de login ou busca que consulta um banco de dados tipo:text",
    "command_injection": "name:host name:ip campo que aciona uma ação no servidor ping diagnóstico nome de arquivo comando",
    "lfi_path_traversal": "name:file name:page name:template campo que referencia um arquivo caminho página idioma incluído",
    "upload_extension": "name:file name:avatar type:file campo de upload de arquivo anexo imagem documento",
    "xxe": "name:xml name:import campo que aceita XML importação de dados feed upload de documento estruturado",
    "ssti": "name:name name:comment campo de texto genérico renderizado de volta na página nome comentário mensagem",
    "ldap_injection": "name:username name:search campo de login usuário busca de diretório corporativo autenticação",
    "ssi_injection": "name:comment name:message campo de texto genérico refletido em página HTML do servidor",
    "format_string": "name:message name:log campo de texto genérico usado em mensagens de log notificação template",
    "java_deserialization": "name:token name:session campo que recebe dados serializados cookie de sessão token estado",
    "fuzzing_generico": "campo de entrada de texto número e-mail busca comentário formulário genérico qualquer tipo",
    "xss": "name:search name:comment campo de busca comentário mensagem nome texto livre refletido na página",
}

with psycopg2.connect(conn_str) as conn:
    with conn.cursor() as cur:
        cur.execute('SELECT id, tipo_ataque FROM public.cache_payloads;')
        rows = cur.fetchall()

        for row_id, tipo in rows:
            texto = DESCRICOES_POR_TIPO.get(tipo, tipo).lower()
            vetor = model.encode(texto).tolist()
            vetor_str = '[' + ','.join(f'{x:.8f}' for x in vetor) + ']'

            cur.execute(
                'UPDATE public.cache_payloads SET embedding_semantico = %s::vector WHERE id = %s;',
                (vetor_str, row_id)
            )
        conn.commit()
        print('[+] Embeddings da tabela cache_payloads atualizados com sucesso!')