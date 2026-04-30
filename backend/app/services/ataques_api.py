import requests
import json
import os
import re
from dotenv import load_dotenv


# Carrega o token do arquivo .env
load_dotenv()
TOKEN = os.getenv("Authorization")

ataques_list = []

# MUDANÇA: Em vez de começar na raiz, focamos nas pastas de "Elite"
# Isso evita baixar lixo como 'Dates' e 'User-Agents'
PASTAS_ELITE = [
    "Fuzzing/Databases",
    "Fuzzing/XSS",
    "Fuzzing/LFI",
    "Fuzzing/Polyglots",
    "Fuzzing/template-engines-expression.txt" # Arquivo específico útil
]

headers = {
    "User-Agent": "HydraDAST-Project-Agent",
    "Authorization": f"token {TOKEN}"
}

def ler(url_api):
    response = requests.get(url_api, headers=headers)
    
    if response.status_code != 200:
        return

    dados = response.json()
    
    # Se a API retornou um dicionário (um único arquivo) em vez de uma lista
    if isinstance(dados, dict):
        dados = [dados]

    for item in dados:
        if item["type"] == "file" and item["name"].endswith(".txt"):
            print(f"  [+] Coletando payloads de: {item['name']}")
            try:
                conteudo = requests.get(item["download_url"], headers=headers).text 
                
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

        elif item["type"] == "dir":
            # Filtro rigoroso de nomes de pastas para garantir qualidade
            # permitidas = ["SQLi", "XSS", "LFI", "Injections", "Polyglots"]
            # if any(p in item["name"] for p in permitidas):
            print(f"\n📁 Entrando na subpasta: {item['name']}")
            ler(item["url"])


# --- EXECUÇÃO ---

print("[*] Iniciando mapeamento do ARSENAL DE ELITE...")

for path in PASTAS_ELITE:
    url_alvo = f"https://api.github.com/repositories/3482588/contents/{path}"
    ler(url_alvo)

# Salvar em arquivo de texto
arquivo_saida = "arsenal_limpo.txt"

if ataques_list:
    # Set para remover duplicatas
    ataques_unicos = sorted(list(set(ataques_list)))
    
    with open(arquivo_saida, "w", encoding="utf-8") as f:
        for payload in ataques_unicos:
            f.write(f"{payload}\n")
    
    print(f"\n[SUCESSO] Arsenal salvo em: {arquivo_saida}")
    print(f"[#] Total de payloads de ALTA QUALIDADE: {len(ataques_unicos)}")
else:
    print("\n[!] Nenhuma munição foi coletada. Verifique o TOKEN ou as pastas.")