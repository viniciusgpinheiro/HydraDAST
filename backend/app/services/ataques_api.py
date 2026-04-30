import requests
import os
import re
from dotenv import load_dotenv


# Carrega o token do arquivo .env
load_dotenv()
TOKEN = os.getenv("Authorization")

arsenal_dinamico = {}

# Configuramos onde queremos recursão total e onde queremos apenas a "superfície"
CONFIG_COLETA = {
    "Fuzzing/Databases": True,
    "Fuzzing/XSS": True,
    "Fuzzing/LFI": True,
    "Fuzzing/Polyglots": True,
    "Fuzzing/SSRF": True,
    "Fuzzing": False  # False = Pega arquivos da pasta, mas NÃO entra nas subpastas
}

headers = {
    "User-Agent": "HydraDAST-Project-Agent",
    "Authorization": f"token {TOKEN}" if TOKEN else ""
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
    
    # 1. Filtro de Tamanho Ajustado
    # Aumentado para 1000 para não perder Polyglots e WAF Bypasses codificados
    if tamanho < 2 or tamanho > 1000: 
        return False

    # 2. Filtro Rápido de Ruído (Blacklist)
    # Se bater aqui, descartamos imediatamente. Economiza processamento.
    if NOISE_PATTERNS.match(payload):
        return False

    # 3. Match de Assinaturas Específicas (Whitelist)
    # Se tem a assinatura de um ataque conhecido, é aprovado.
    if ATTACK_PATTERNS.search(payload):
        return True

    # 4. Heurística de Densidade (O "Pulo do Gato" Otimizado)
    # Em vez de re.findall (lento), usamos geradores nativos do Python (muito rápido)
    letras_e_numeros = sum(1 for char in payload if char.isalnum() or char.isspace())
    simbolos = tamanho - letras_e_numeros
    
    if tamanho > 0:
        taxa_simbolos = simbolos / tamanho
        # Ajustado para 25%. Payloads modernos usam muita ofuscação (!@#$).
        if taxa_simbolos > 0.25: 
            return True

    return False


def ler(url_api, permitir_recursao=True):
    response = requests.get(url_api, headers=headers)
    if response.status_code != 200: return

    dados = response.json()
    if isinstance(dados, dict): dados = [dados]

    for item in dados:
        # Se for ARQUIVO: Baixa e filtra
        if item["type"] == "file" and item["name"].endswith(".txt"):
            partes = item["path"].split('/')
            # Se estiver na raiz do Fuzzing, a pasta pai é 'Fuzzing'
            # Se estiver em subpasta, pega o nome dela
            pasta_pai = partes[-2] if len(partes) > 1 else "Raiz"
            
            print(f"  [+] Coletando: {item['name']} (Categoria: {pasta_pai})")
            
            try:
                conteudo = requests.get(item["download_url"], headers=headers).text 
                if pasta_pai not in arsenal_dinamico:
                    arsenal_dinamico[pasta_pai] = []

                for linha in conteudo.splitlines():
                    payload = linha.strip()
                    
                    # --- FILTRO DE CONTEÚDO ---
                    # 1. Ignora comentários (#)
                    # 2. Ignora se a linha for só números (evita o lixo que você recebeu)
                    # 3. Ignora linhas muito curtas (menos de 3 caracteres) que não sejam payloads úteis
                    if (payload and
                        not payload.startswith("#") and 
                        not payload.isdigit() and 
                        len(payload) > 2):
                        ataques_list.append(payload)
                        
            except Exception as e:
                print(f"      [!] Erro no arquivo {item['name']}: {e}")
                    if payload and not payload.startswith("#") and eh_payload_util(payload):
                        arsenal_dinamico[pasta_pai].append(payload)
            except:
                continue

        # Se for DIRETÓRIO: Só entra se a recursão for permitida para este caminho
        elif item["type"] == "dir" and permitir_recursao:
            # Aqui evitamos entrar em pastas gigantes de nomes se estivermos na raiz do Fuzzing
            ler(item["url"], permitir_recursao=True)


# --- EXECUÇÃO ---
print("[*] Iniciando coleta seletiva...")

for path, recursivo in CONFIG_COLETA.items():
    print(f"\n📂 Processando: {path} (Recursivo: {recursivo})")
    url_alvo = f"https://api.github.com/repositories/3482588/contents/{path}"
    # Chamamos a função passando se ela deve ou não entrar em subpastas
    ler(url_alvo, permitir_recursao=recursivo)

# --- SALVAMENTO ---
output_dir = "../data/arsenal_inteligente"
if not os.path.exists(output_dir): os.makedirs(output_dir)

for pasta, payloads in arsenal_dinamico.items():
    if payloads:
        payloads_unicos = sorted(list(set(payloads)))
        nome_final = f"{output_dir}/{pasta}.txt"
        with open(nome_final, "w", encoding="utf-8") as f:
            for p in payloads_unicos:
                f.write(f"{p}\n")
        print(f"  [✔] {nome_final} ({len(payloads_unicos)} payloads)")