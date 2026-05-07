import requests
import os
import re
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor 
from threading import Lock 


load_dotenv()
TOKEN = os.getenv("Authorization")

arsenal_lock = Lock()
arsenal_dinamico = {}

session = requests.Session()
headers = {
    "User-Agent": "HydraDAST-Project-Agent",
    "Authorization": f"token {TOKEN}" if TOKEN else ""
}
session.headers.update(headers)

# Configuramos onde queremos recursão total e onde queremos apenas a "superfície"
CATEGORIAS_SECLIST = {
    "Fuzzing/Databases": True,
    "Fuzzing/XSS": True,
    "Fuzzing/LFI": True,
    "Fuzzing/Polyglots": True,
    "Fuzzing/SSRF": True,
    "Fuzzing": False  # False = Pega arquivos da pasta, mas NÃO entra nas subpastas
}
CATEGORIAS_PATT = {
    "NoSQL Injection/Intruder": True,
    "Server Side Template Injection/Intruder": True,
    "SSRF Injection/Intruder": True,
    "Command Injection/Intruder": True,
    "SQL Injection/Intruder": True,
    "File Inclusion/Intruder": True,
    "XSS Injection/Intruder": True
}

# 1. LISTA NEGRA (Ruído absoluto: Dicionários, versões, datas, extensões puras)
NOISE_PATTERNS = re.compile(
    r"^(?:\.[a-zA-Z0-9]{2,5}"      # Extensões soltas (ex: .html, .txt, .json)
    r"|\d{4}-\d{2}-\d{2}.*"        # Datas/Timestamps (ex: 2023-01-01)
    r"|v?\d+\.\d+\.\d+.*"          # Versões de software (ex: 1.0.2, v2.3-beta)
    r"|[a-zA-Z0-9\s\-_]+)$"        # Dicionário puro (apenas letras/números/espaços)
)

# 2. LISTA BRANCA (Assinaturas letais de múltiplas vulnerabilidades)
ATTACK_PATTERNS = re.compile(
    r"(?:[<>\"'`/]{2,}"                                   # XSS / Path Traversal chars
    r"|\b(?:SELECT|UNION|INSERT|DROP|UPDATE|DELETE)\b"    # SQLi Clássico
    r"|\{\{.*?\}\}|\$\{.*?\}|<%.*?%>"                     # SSTI (Template Injection)
    r"|\.\.[/\\]+"                                        # LFI (Path Traversal explícito)
    r"|(?:etc/passwd|bin/sh|cmd\.exe|system32|win\.ini)"  # Arquivos críticos de SO
    r"|\b(?:alert|console|eval|prompt|confirm|fetch)\s*\("# JS / XSS Functions
    r"|1\s*=\s*1|1\s*==\s*1|'a'\s*=\s*'a"                 # SQLi Tautologias (Boolean)
    r"|%00|%0a|%0d|%2e%2e"                                # Null Byte e Encodings de quebra
    r"|\b(?:sleep|benchmark|pg_sleep|waitfor\s+delay)\b"  # Time-based SQLi / RCE
    r"|cmd=|exec=|system\(|passthru\(|shell_exec\("       # Command Injection (RCE)
    r"|\b(?:http|file|gopher|dict)://|169\.254\.169\.254" # SSRF / RFI / Cloud Metadata
    r"|<\!ENTITY|<\!DOCTYPE|<\?xml"                       # XXE (XML Injection)
    r"|\$ne|\$gt|\$lt|\$where|\$regex"                    # NoSQL Injection (MongoDB)
    r"|java\.lang|Runtime\.getRuntime"                    # Deserialização Java / OGNL
    r")", re.IGNORECASE
)



def eh_payload_util(payload):
    payload = payload.strip()
    tamanho = len(payload)
    
    if tamanho < 2 or tamanho > 1000: 
        return False

    if NOISE_PATTERNS.match(payload):
        return False

    if ATTACK_PATTERNS.search(payload):
        return True

    letras_e_numeros = sum(1 for char in payload if char.isalnum() or char.isspace())
    simbolos = tamanho - letras_e_numeros
    
    if tamanho > 0:
        taxa_simbolos = simbolos / tamanho
        if taxa_simbolos > 0.25: 
            return True

    return False



def processar_arquivo(item):
    try:
        partes = item["path"].split("/")
        pasta_pai = partes[-2] if len(partes) > 1 else "Raiz"

        if pasta_pai == "Fuzzing":
            nome_limpo = item["name"].replace(".txt", "")
            pasta_pai = re.sub(r'[^a-zA-Z0-9_-]', '_', nome_limpo)
        
        if pasta_pai == "Intruder":
            pasta_pai = partes[-3] if len(partes) > 2 else pasta_pai

        conteudo = session.get(item["download_url"]).text

        payloads_filtrados = []
        for linha in conteudo.splitlines():
            payload = linha.strip()
            if payload and not payload.startswith("#") and eh_payload_util(payload):
                payloads_filtrados.append(payload)

        with arsenal_lock:
            if pasta_pai not in arsenal_dinamico:
                arsenal_dinamico[pasta_pai] = []
            arsenal_dinamico[pasta_pai].extend(payloads_filtrados)

        print(f"  [✔] Processado: {item['name']} -> {pasta_pai}")

    except Exception as e:
        print(f"  [!] Erro ao processar {item['name']}: {e}")



def buscar_arquivos(url, recursao=True):
    arquivos_encontrados = []
    try:
        response = session.get(url)
        if response.status_code != 200: return []

        dados = response.json()
        if isinstance(dados, dict): dados = [dados]

        for item in dados:
            if item["type"] == "file" and item["name"].endswith(".txt"):
                arquivos_encontrados.append(item)

            elif item["type"] == "dir" and recursao:
                arquivos_encontrados.extend(buscar_arquivos(item["url"], True))

    except Exception as e:
        print(f"  [!] Erro na busca: {e}")
    
    return arquivos_encontrados



# --- EXECUÇÃO ---
if __name__ == "__main__":
    print("[*] Mapeando arquivos nos repositórios...")
    
    todos_arquivos = []
    for path, recursivo in CATEGORIAS_SECLIST.items():
        url_alvo = f"https://api.github.com/repositories/3482588/contents/{path}"
        todos_arquivos.extend(buscar_arquivos(url_alvo, recursao=recursivo))
    for path, recursivo in CATEGORIAS_PATT.items():
        url_alvo = f"https://api.github.com/repos/SwisskyRepo/PayloadsAllTheThings/contents/{path}"
        todos_arquivos.extend(buscar_arquivos(url_alvo, recursao=recursivo))
    

    print(f"[*] Total de arquivos para processar: {len(todos_arquivos)}")
    print("[*] Iniciando download paralelo (Max 15 workers)...")

    # Dispara múltiplas threads para baixar e filtrar os arquivos ao mesmo tempo
    with ThreadPoolExecutor(max_workers=15) as executor:
        executor.map(processar_arquivo, todos_arquivos)

    # --- SALVAMENTO (Mantido o original com melhoria no nome) ---
    output_dir = "../data/arsenal_inteligente"
    if not os.path.exists(output_dir): os.makedirs(output_dir)

    for pasta, payloads in arsenal_dinamico.items():
        if payloads:
            payloads_unicos = sorted(list(set(payloads)))
            nome_final = f"{output_dir}/{pasta}.txt"
            with open(nome_final, "w", encoding="utf-8") as f:
                for p in payloads_unicos:
                    f.write(f"{p}\n")
            print(f"  [Finalizado] {nome_final} ({len(payloads_unicos)} payloads)")
    