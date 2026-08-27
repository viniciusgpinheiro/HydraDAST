import requests
import json
import websocket
import time
from playwright.sync_api import sync_playwright 


# ==========================================
# 1. MOTORES DE COMUNICAÇÃO (Motores Base)
# ==========================================
def _requisicao_generica(payload, url, metodo, usar_json=False, injetar_em="body", nome_campo=None, session=None):
    """
    Versão expandida do motor HTTP que permite escolher onde o payload será injetado:
    'body', 'query', 'header', 'cookie' ou 'method'.
    """
    metodo = metodo.upper()
    
    # 1. Configuração de Cabeçalhos Padrão
    headers = {
        "User-Agent": "Mozilla/5.0",
    }
    cookies = {}

    if metodo in ["POST", "PUT"] and usar_json:
        headers["Content-Type"] = "application/json"
    elif metodo in ["POST", "PUT"]:
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    # 2. LÓGICA DE INJEÇÃO DINÂMICA
    dados_body = None
    parametros_query = None

    if injetar_em == "header" and nome_campo:
        # Injeta o payload malicioso diretamente no cabeçalho especificado (ex: User-Agent, X-Forwarded-For)
        headers[nome_campo] = str(payload)
    elif injetar_em == "cookie" and nome_campo:
        # Injeta o payload dentro de um cookie específico
        cookies[nome_campo] = str(payload)
    elif injetar_em == "method":
        # Altera o próprio verbo HTTP para o payload (HTTP Verb Tampering)
        metodo = str(payload).upper()
    elif injetar_em == "query":
        parametros_query = payload
    else:
        # Padrão: Injeta no corpo da requisição
        dados_body = payload

    client = session if session else requests

    try:
        # Execução dinâmica baseada no método resolvido
        if metodo == "GET":
            resposta = client.get(url, params=parametros_query, headers=headers, cookies=cookies)
        elif metodo == "POST":
            if usar_json and dados_body:
                resposta = client.post(url, json=dados_body, headers=headers, cookies=cookies)
            else:
                resposta = client.post(url, data=dados_body, headers=headers, cookies=cookies)
        elif metodo == "PUT":
            if usar_json and dados_body:
                resposta = client.put(url, json=dados_body, headers=headers, cookies=cookies)
            else:
                resposta = client.put(url, data=dados_body, headers=headers, cookies=cookies)
        elif metodo in ["DELETE", "OPTIONS", "HEAD", "PATCH"]:
            # Suporte expandido para verbos adicionais
            resposta = client.request(metodo, url, data=dados_body, headers=headers, cookies=cookies, params=parametros_query)
        else:
            return {"erro": True, "mensagem": f"Método HTTP '{metodo}' customizado não gerenciado."}

        # [O restante do tratamento de resposta e retorno do dicionário continua idêntico ao seu código]
        # Corpo maior que 200 chars: a classificação por regex (FeedbackService.analisar_resposta)
        # precisa de contexto suficiente pra achar erros de banco/reflexão de payload.
        return {"status_code": resposta.status_code, "url_final": resposta.url, "corpo": resposta.text[:5000]}

    except requests.exceptions.RequestException as e:
        return {"erro": True, "mensagem": f"Falha de rede: {e}"}
    

def _requisicao_websocket(payload, url, usar_json=False, timeout=5):
    if not (url.startswith("ws://") or url.startswith("wss://")):
        return {"erro": True, "mensagem": "URL inválida para WebSocket. Deve começar com ws:// ou wss://"}

    resultado = {
        "status_code": 101,  # Switching Protocols estatístico
        "url_final": url,
        "tempo_resposta_segundos": 0,
        "corpo": None,
        "requisicao_enviada": {"metodo": "WEBSOCKET", "corpo_enviado": payload}
    }

    inicio = time.time()
    ws = None
    try:
        ws = websocket.create_connection(url, timeout=timeout)
        dado_enviar = json.dumps(payload) if usar_json else str(payload)
        ws.send(dado_enviar)
        
        resposta = ws.recv()
        resultado["tempo_resposta_segundos"] = time.time() - inicio
        
        try:
            resultado["corpo"] = json.loads(resposta)
        except ValueError:
            resultado["corpo"] = resposta

    except Exception as e:
        return {"erro": True, "mensagem": f"Erro na conexão WebSocket: {e}"}
    finally:
        if ws:
            ws.close()

    return resultado


def _requisicao_graphql(url, query_str, variables=None, token=None):
    headers = {"Content-Type": "application/json", "User-Agent": "SecurityTester/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    payload = {"query": query_str, "variables": variables or {}}

    try:
        resposta = requests.post(url, json=payload, headers=headers, timeout=5)
        try:
            dados_resposta = resposta.json()
        except ValueError:
            dados_resposta = resposta.text

        return {
            "status_code": resposta.status_code,
            "url_final": url,
            "corpo": dados_resposta,
            "tempo_resposta_segundos": resposta.elapsed.total_seconds(),
            "requisicao_enviada": {"metodo": "GRAPHQL_POST", "corpo_enviado": payload}
        }
    except requests.exceptions.RequestException as e:
        return {"erro": True, "mensagem": f"Erro de conexão GraphQL: {e}"}
    

def _analise_dom_browser(url, payload, timeout_ms=5000):
    resultado = {
        "status_code": 200,
        "url_testada": url,
        "xss_detectado": False,
        "mensagem_alerta": None,
        "tempo_execucao_segundos": 0,
        "corpo": "Execução via browser concluída.",
        "erro": False
    }

    inicio = time.time()
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            def lidar_com_dialogo(dialog):
                nonlocal resultado
                resultado["xss_detectado"] = True
                resultado["mensagem_alerta"] = dialog.message
                dialog.dismiss()

            page.on("dialog", lidar_com_dialogo)
            
            # Concatena o payload no fragmento hash para teste DOM XSS
            url_com_payload = f"{url}#{payload}" if "#" not in url else f"{url}{payload}"
            
            page.goto(url_com_payload, timeout=timeout_ms)
            page.wait_for_timeout(1000)

            resultado["tempo_execucao_segundos"] = time.time() - inicio
            browser.close()
        except Exception as e:
            return {"erro": True, "mensagem": f"Erro no motor do Browser: {e}"}

    return resultado


# ==========================================
# 2. ROTEADORES DE FUNÇÃO (Orquestradores)
# ==========================================

def _roteador_transporte(payload, url, metodo, usar_json, transporte, session, **kwargs):
    """Encaminha dinamicamente a execução para o motor correto."""
    # Detecção automática baseada na URL se o transporte for o padrão
    if transporte == "http" and url.startswith(("ws://", "wss://")):
        transporte = "websocket"

    if transporte == "websocket":
        return _requisicao_websocket(payload, url, usar_json=usar_json)
    elif transporte == "graphql":
        # Para GraphQL o payload é tratado como a String da Query
        return _requisicao_graphql(url, query_str=payload, variables=kwargs.get("variables"), token=kwargs.get("token"))
    elif transporte == "browser":
        # Se for browser, o payload vai ser injetado/testado no DOM
        return _analise_dom_browser(url, payload)
    else:
        return _requisicao_generica(payload, url, metodo, usar_json=usar_json, session=session)


# --- Funções Wrapper Adaptadas ---

def execute_sql_injection(payload, url, metodo="POST", transporte="http", session=None, **kwargs):
    return _roteador_transporte(payload, url, metodo, usar_json=False, transporte=transporte, session=session, **kwargs)

def execute_command_injection(payload, url, metodo="POST", transporte="http", session=None, **kwargs):
    return _roteador_transporte(payload, url, metodo, usar_json=False, transporte=transporte, session=session, **kwargs)

def execute_file_inclusion_and_extensions(payload, url, metodo="GET", transporte="http", session=None, **kwargs):
    return _roteador_transporte(payload, url, metodo, usar_json=False, transporte=transporte, session=session, **kwargs)

def execute_client_side_xss(payload, url, metodo="GET", transporte="http", session=None, **kwargs):
    # Se for um teste de XSS e o usuário optar por rodar no navegador, muda o transporte automaticamente
    if transporte == "browser" or kwargs.get("forcar_browser") == True:
        transporte = "browser"
    return _roteador_transporte(payload, url, metodo, usar_json=False, transporte=transporte, session=session, **kwargs)

def execute_server_side_injection(payload, url, metodo="POST", transporte="http", session=None, **kwargs):
    # Injeções de servidor estruturadas costumam preferir JSON por padrão
    return _roteador_transporte(payload, url, metodo, usar_json=True, transporte=transporte, session=session, **kwargs)

def execute_generic_fuzzing(payload, url, metodo="GET", transporte="http", session=None, **kwargs):
    return _roteador_transporte(payload, url, metodo, usar_json=False, transporte=transporte, session=session, **kwargs)


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
    from dotenv import load_dotenv
    import os
    import psycopg2
    from datetime import datetime

    load_dotenv()
    conn_string = os.getenv("DATABASE_URL")
    if not conn_string:
        raise RuntimeError("Defina DATABASE_URL no .env")

    conn = None
    try:
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()

        # --- 1. Criar dados de teste (Usuário, Teste, Relatório) ---
        print("--- CONFIGURANDO DADOS DE TESTE NO BANCO ---")

        # Criar ou obter usuário
        cur.execute("SELECT id FROM usuarios WHERE email = %s", ("usuario.teste@example.com",))
        user_id = cur.fetchone()
        if not user_id:
            cur.execute("INSERT INTO usuarios (nome, email, senha_hash) VALUES (%s, %s, %s) RETURNING id",
                        ("Usuário Teste", "usuario.teste@example.com", "senha_teste"))
            user_id = cur.fetchone()[0]
            print(f"Usuário de teste criado com ID: {user_id}")
        else:
            user_id = user_id[0]
            print(f"Usando usuário de teste existente com ID: {user_id}")

        # Criar Teste
        url_alvo = "https://the-internet.herokuapp.com/authenticate"
        cur.execute("INSERT INTO testes (id_usuario, url, linguagem) VALUES (%s, %s, %s) RETURNING id",
                    (user_id, url_alvo, "pt-br"))
        teste_id = cur.fetchone()[0]
        print(f"Teste criado com ID: {teste_id} para a URL: {url_alvo}")

        # Criar Relatório
        cur.execute("INSERT INTO relatorios (id_teste, data, status) VALUES (%s, %s, %s) RETURNING id",
                    (teste_id, datetime.now(), "em_andamento"))
        relatorio_id = cur.fetchone()[0]
        print(f"Relatório criado com ID: {relatorio_id}")
        
        conn.commit()
        print("--- DADOS DE TESTE CONFIGURADOS ---\n")

        # --- 2. Executar um ataque de exemplo ---
        print("--- EXECUTANDO ATAQUE E SALVANDO NO BANCO ---")
        
        tipo_ataque_exemplo = "SQL Injection"
        payload_exemplo = "' OR 1=1 --"
        metodo_exemplo = "POST"
        
        # Usando uma das funções existentes para executar o ataque
        resultado_ataque = execute_sql_injection(
            payload={"username": payload_exemplo, "password": "password"},
            url=url_alvo,
            metodo=metodo_exemplo
        )

        print(f"Resultado da execução: {resultado_ataque}")

        # --- 3. Inserir o resultado do ataque na tabela ataques ---
        query_str = json.dumps(resultado_ataque.get("requisicao_enviada", {}))
        erro_str = resultado_ataque.get("mensagem")
        
        # Valores de exemplo para colunas que não temos ainda
        solucao_exemplo = "Use prepared statements para evitar SQL Injection."
        risco_exemplo = "Alto"
        parametro_exemplo = "username"

        cur.execute(
            """
            INSERT INTO ataques 
            (id_relatorio, url, metodo, query, payload, erro, solucao, tipo_ataque, risco, parametro)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                relatorio_id,
                resultado_ataque.get("url_final", url_alvo),
                metodo_exemplo,
                query_str,
                payload_exemplo,
                erro_str,
                solucao_exemplo,
                tipo_ataque_exemplo,
                risco_exemplo,
                parametro_exemplo
            )
        )
        conn.commit()
        print("\n--- ATAQUE REGISTRADO COM SUCESSO NO BANCO DE DADOS ---")

    except psycopg2.Error as e:
        print(f"Erro de banco de dados: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()
            print("Conexão com o banco de dados fechada.")