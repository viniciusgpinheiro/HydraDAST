"""Popula public.cache_payloads com as novas categorias de ataque (item 1 do
pedido: NoSQLi, Command Injection, LFI, upload malicioso, XXE, SSTI, LDAP,
SSI, Format String, Java Deserialization, fuzzing genérico) a partir do
arsenal já baixado em backend/app/data/arsenal_inteligente (com fallback
para arsenal_final). Sem isso, `FeedbackService.escolher_top_n_payloads` não
tem o que ranquear além das 3 categorias antigas (credencial_senha,
credencial_identificador, campo_generico).

Pré-requisito: rode a migração
`scripts/migrations/003_categorias_ataque_e_orcamento.sql` antes (ela cria a
coluna `cache_payloads.ponto_injecao` usada aqui).

Depois de rodar este script, rode `populate_cache_payloads_embeddings.py`
para gerar os embeddings dos registros novos (ele já cobre as categorias
novas em DESCRICOES_POR_TIPO).
"""

import os
import random

import psycopg2
from dotenv import load_dotenv

load_dotenv()

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR_INTELIGENTE = os.path.join(_BASE_DIR, "..", "data", "arsenal_inteligente")
_DATA_DIR_FINAL = os.path.join(_BASE_DIR, "..", "data", "arsenal_final")

# categoria -> (arquivos candidatos, ponto de injeção, quantos payloads amostrar)
FONTES_POR_CATEGORIA: dict[str, tuple[list[str], str, int]] = {
    "nosqli": (["NoSQL Injection.txt", "NoSQL_Master.txt"], "body", 15),
    "command_injection": (
        ["command-injection-commix.txt", "UnixAttacks_fuzzdb.txt", "Linux.txt"], "body", 15,
    ),
    "lfi_path_traversal": (["LFI.txt", "LFI_PathTraversal_Master.txt"], "query", 15),
    "upload_extension": (
        ["file-extensions.txt", "extensions-Bo0oM.txt", "Extensions_Master.txt"], "body", 15,
    ),
    "xxe": (["XXE-Fuzzing.txt", "XML-FUZZ.txt"], "body", 10),
    "ssti": (["Template_Injection_Master.txt", "template-engines-expression.txt"], "body", 15),
    "ldap_injection": (["LDAP_Fuzzing.txt"], "query", 10),
    "ssi_injection": (["SSI-Injection-Jhaddix.txt"], "body", 10),
    "format_string": (["FormatString-Jhaddix.txt"], "query", 10),
    "java_deserialization": (["fully-qualified-java-classes.txt"], "body", 10),
    "fuzzing_generico": (
        ["big-list-of-naughty-strings.txt", "Unicode.txt", "special-chars___urlencoded.txt"], "body", 15,
    ),
    "xss": (["HTML5sec-Injections-Jhaddix.txt", "URI-XSS_fuzzdb.txt", "Polyglots.txt"], "query", 15),
}


def _ler_linhas(nome_arquivo: str) -> list[str]:
    for base in (_DATA_DIR_INTELIGENTE, _DATA_DIR_FINAL):
        caminho = os.path.join(base, nome_arquivo)
        if os.path.isfile(caminho):
            with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
                return [linha.strip() for linha in f if linha.strip() and not linha.startswith("#")]
    return []


def main() -> None:
    conn_string = os.getenv("DATABASE_URL")
    if not conn_string:
        raise RuntimeError("Defina DATABASE_URL no .env")

    random.seed(42)  # amostragem reprodutível entre execuções

    with psycopg2.connect(conn_string) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT tipo_ataque, payload FROM public.cache_payloads;")
            existentes = {(tipo, payload) for tipo, payload in cur.fetchall()}

            inseridos = 0
            for categoria, (arquivos, ponto_injecao, amostra) in FONTES_POR_CATEGORIA.items():
                linhas: list[str] = []
                for arquivo in arquivos:
                    linhas.extend(_ler_linhas(arquivo))
                if not linhas:
                    print(f"[!] Nenhum arquivo encontrado para '{categoria}' ({arquivos}); pulando.")
                    continue

                candidatos = list(dict.fromkeys(linhas))  # remove duplicatas mantendo ordem
                amostrados = random.sample(candidatos, min(amostra, len(candidatos)))

                for payload in amostrados:
                    if len(payload) > 500 or (categoria, payload) in existentes:
                        continue
                    cur.execute(
                        """
                        INSERT INTO public.cache_payloads (origem_api, payload, tipo_ataque, ponto_injecao)
                        VALUES (%s, %s, %s, %s)
                        """,
                        ("seed_arsenal", payload, categoria, ponto_injecao),
                    )
                    inseridos += 1
                print(f"  [✔] {categoria}: {len(amostrados)} payloads amostrados de {len(candidatos)} disponíveis.")

            conn.commit()
            print(f"[+] {inseridos} novos payloads inseridos em cache_payloads (categorias novas do item 1).")


if __name__ == "__main__":
    main()
