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