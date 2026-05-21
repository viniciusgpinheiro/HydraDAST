import requests
import json


def _requisicao_generica(payload, url, metodo, usar_json=False):

    metodo = metodo.upper()
    headers = {
        "User-Agent": "Mozilla/5.0",
    }
    
    if metodo in ["POST", "PUT"]:
        if usar_json:
            headers["Content-Type"] = "application/json"
        else:
            headers["Content-Type"] = "application/x-www-form-urlencoded"

    try:
        if metodo == "GET":      
            resposta = requests.get(url, params=payload, headers=headers)     
        elif metodo == "POST": 
            if usar_json:
                resposta = requests.post(url, json=payload, headers=headers)
            else:
                resposta = requests.post(url, data=payload, headers=headers)
        elif metodo == "PUT":  
            if usar_json:
                resposta = requests.put(url, json=payload, headers=headers)
            else:
                resposta = requests.put(url, data=payload, headers=headers)
        else: 
            return None

        try:
            corpo_formatado = resposta.json()
        except ValueError:
            corpo_formatado = resposta.text

        return {
            "status_code": resposta.status_code,
            "status_texto": resposta.reason,
            "url_final": resposta.url,
            "tempo_resposta_segundos": resposta.elapsed.total_seconds(),
            "headers_resposta": dict(resposta.headers),
            "cookies_resposta": requests.utils.dict_from_cookiejar(resposta.cookies),
            "corpo": corpo_formatado,
            "redirecionamentos": [res.url for res in resposta.history],
            "requisicao_enviada": {
                "metodo": resposta.request.method,
                "url_origem": url,
                "headers_enviados": dict(resposta.request.headers),
                "corpo_enviado": resposta.request.body.decode('utf-8') if resposta.request.body else None
            }
        }
    except requests.exceptions.RequestException as e:
        return {"erro": True, "mensagem": f"Falha de rede: {e}"}


def execute_sql_injection(payload, url, metodo):
    """Processa validações de estruturas SQL/NoSQL enviadas tanto via Body quanto Query."""
    return _requisicao_generica(payload, url, metodo, usar_json=False)

def execute_command_injection(payload, url, metodo):
    """Executa testes baseados em inputs de sistema operacional (Normalmente em Body)."""
    return _requisicao_generica(payload, url, metodo, usar_json=False)

def execute_file_inclusion_and_extensions(payload, url, metodo):
    """Gerencia mutações de caminhos (Path) ou parâmetros de consulta."""
    return _requisicao_generica(payload, url, metodo, usar_json=False)

def execute_client_side_xss(payload, url, metodo):
    """Valida reflexão de tags diretamente nos parâmetros recebidos da URL ou campos de entrada."""
    return _requisicao_generica(payload, url, metodo, usar_json=False)

def execute_server_side_injection(payload, url, metodo):
    """Utiliza estruturas de dados estritas como JSON/XML devido à natureza das engines (ex: Jinja2, SOAP)."""
    return _requisicao_generica(payload, url, metodo, usar_json=True)

def execute_generic_fuzzing(payload, url, metodo):
    """Dispara sequências amplas de caracteres especiais em múltiplos formatos."""
    return _requisicao_generica(payload, url, metodo, usar_json=False)


ATTACK_CLASSIFICATION = {
    # --- Banco de Dados e Autenticação (SQL / NoSQL) ---
    "SQL Injection.txt": execute_sql_injection,
    "SQLi.txt": execute_sql_injection,
    "NoSQL Injection.txt": execute_sql_injection,
    "Databases.txt": execute_sql_injection,
    "login_bypass.txt": execute_sql_injection,
    
    # --- Injeção de Comandos de Sistema (OS) ---
    "Command Injection.txt": execute_command_injection,
    "command-injection-commix.txt": execute_command_injection,
    "UnixAttacks_fuzzdb.txt": execute_command_injection,
    "Linux.txt": execute_command_injection,
    "Windows-Attacks_fuzzdb.txt": execute_command_injection,
    "Windows.txt": execute_command_injection,
    
    # --- Inclusão de Arquivos e Uploads ---
    "LFI.txt": execute_file_inclusion_and_extensions,
    "file-extensions.txt": execute_file_inclusion_and_extensions,
    "extensions-Bo0oM.txt": execute_file_inclusion_and_extensions,
    "file-extensions-all-cases.txt": execute_file_inclusion_and_extensions,
    "file-extensions-lower-case.txt": execute_file_inclusion_and_extensions,
    "file-extensions-upper-case.txt": execute_file_inclusion_and_extensions,
    
    # --- Vulnerabilidades Client-Side (XSS / HTML) ---
    "HTML5sec-Injections-Jhaddix.txt": execute_client_side_xss,
    "URI-XSS_fuzzdb.txt": execute_client_side_xss,
    "Polyglots.txt": execute_client_side_xss,
    
    # --- Injeções Estruturadas e Lógicas de Servidor ---
    "FormatString-Jhaddix.txt": execute_server_side_injection,
    "template-engines-expression.txt": execute_server_side_injection,
    "template-engines-special-vars.txt": execute_server_side_injection,
    "XML-FUZZ.txt": execute_server_side_injection,
    "XXE-Fuzzing.txt": execute_server_side_injection,
    "LDAP_Fuzzing.txt": execute_server_side_injection,
    "SSI-Injection-Jhaddix.txt": execute_server_side_injection,
    
    # --- Fuzzing Geral, Codificação e Strings Complexas ---
    "big-list-of-naughty-strings.txt": execute_generic_fuzzing,
    "JSON_Fuzzing.txt": execute_generic_fuzzing,
    "special-chars___urlencoded.txt": execute_generic_fuzzing,
    "URI-hex.txt": execute_generic_fuzzing,
    "fuzz-Bo0oM-friendly.txt": execute_generic_fuzzing,
    "fuzz-Bo0oM.txt": execute_generic_fuzzing,
    "FuzzingStrings-SkullSecurity_org.txt": execute_generic_fuzzing,
    "Unicode.txt": execute_generic_fuzzing,
    "fully-qualified-java-classes.txt": execute_generic_fuzzing,
    "robot-friendly.txt": execute_generic_fuzzing,
    "human-friendly.txt": execute_generic_fuzzing,
}


ENTRY_POINT_MAPPING = {
    "body": [
        "SQL Injection.txt", "SQLi.txt", "NoSQL Injection.txt", "Databases.txt", 
        "login_bypass.txt", "Command Injection.txt", "command-injection-commix.txt", 
        "XML-FUZZ.txt", "XXE-Fuzzing.txt", "JSON_Fuzzing.txt"
    ],
    "query": [
        "URI-XSS_fuzzdb.txt", "URI-hex.txt", "template-engines-expression.txt", 
        "template-engines-special-vars.txt", "LDAP_Fuzzing.txt", "FormatString-Jhaddix.txt"
    ],
    "path_or_upload": [
        "LFI.txt", "file-extensions.txt", "extensions-Bo0oM.txt", 
        "file-extensions-all-cases.txt", "file-extensions-lower-case.txt", 
        "file-extensions-upper-case.txt"
    ],
    "any_input_or_headers": [
        "big-list-of-naughty-strings.txt", "special-chars___urlencoded.txt", 
        "fuzz-Bo0oM-friendly.txt", "fuzz-Bo0oM.txt", "FuzzingStrings-SkullSecurity_org.txt", 
        "Unicode.txt", "Polyglots.txt", "HTML5sec-Injections-Jhaddix.txt"
    ]
}


if __name__ == "__main__":
    url = "https://the-internet.herokuapp.com/authenticate"
    metodo = "POST"
    payload = {"username": "tomsmith", "password": "SuperSecretPassword!"}

    resposta = execute_sql_injection(payload, url, metodo)
    print(json.dumps(resposta, indent=4, ensure_ascii=False))