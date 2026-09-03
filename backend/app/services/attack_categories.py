"""Catálogo das categorias de ataque (o universo "i" do item 1 do pedido).

Cada entrada de `cache_payloads.tipo_ataque` precisa de: um nome de exibição
para o relatório, e um texto de fallback (problema/solução/código) usado
quando o LLM de relatório (`services/llm_service.py`) está desligado ou
falha — no mesmo formato que `scan_runner._BASE_CONHECIMENTO` já usa para
'sql'/'xss'/'header'.

Os dois motores hoje expostos no front (`frontend/src/data/motores.js`:
sql/xss/header) continuam existindo, mas cada um agora ataca TODOS os campos
compatíveis com o seu "bucket" de categorias, escolhendo por campo os `n`
melhores payloads (de qualquer categoria do bucket) via
`FeedbackService.escolher_top_n_payloads` — em vez de um único payload fixo
num único campo.
"""

# Buckets: quais categorias de cache_payloads cada motor do front testa.
BUCKET_SQL: set[str] = {
    "credencial_senha", "credencial_identificador", "sqli", "nosqli",
    "command_injection", "ldap_injection",
}
BUCKET_XSS: set[str] = {
    "campo_generico", "xss", "ssti", "xxe", "ssi_injection", "format_string",
    "java_deserialization", "fuzzing_generico", "upload_extension", "lfi_path_traversal",
}

# categoria -> nome de exibição no relatório
NOME_EXIBICAO: dict[str, str] = {
    "credencial_senha": "SQL Injection",
    "credencial_identificador": "SQL Injection",
    "sqli": "SQL Injection",
    "nosqli": "NoSQL Injection",
    "command_injection": "Command Injection",
    "ldap_injection": "LDAP Injection",
    "campo_generico": "XSS",
    "xss": "XSS",
    "ssti": "Server-Side Template Injection",
    "xxe": "XXE (XML External Entity)",
    "ssi_injection": "SSI Injection",
    "format_string": "Format String",
    "java_deserialization": "Deserialização Insegura",
    "fuzzing_generico": "Fuzzing Genérico",
    "upload_extension": "Upload de Arquivo Malicioso",
    "lfi_path_traversal": "LFI / Path Traversal",
}

# categoria -> texto de fallback do relatório (problema/solução/código).
# As categorias antigas (credencial_*, campo_generico) usam o texto já
# existente em scan_runner._BASE_CONHECIMENTO — não duplicado aqui.
KB_POR_CATEGORIA: dict[str, dict] = {
    "nosqli": {
        "problema": (
            "O parâmetro é usado diretamente numa query NoSQL (ex.: MongoDB), "
            "permitindo que operadores como $ne, $gt ou $where alterem a lógica "
            "da consulta e burlem autenticação ou filtros."
        ),
        "solucao": (
            "Valide e tipe estritamente a entrada antes de usá-la em filtros; "
            "nunca passe objetos/JSON arbitrários do cliente direto para a query."
        ),
        "codigo": (
            "# Vulnerável\ndb.users.find({\"password\": req.body.password})\n\n"
            "# Seguro\ndb.users.find({\"password\": String(req.body.password)})"
        ),
    },
    "command_injection": {
        "problema": (
            "O valor do campo é passado para uma chamada de shell do sistema "
            "operacional sem sanitização, permitindo encadear comandos "
            "(ex.: `; cat /etc/passwd`)."
        ),
        "solucao": (
            "Evite chamar o shell com entrada do usuário; use APIs que executem "
            "o binário diretamente (sem shell=True) e uma allowlist de argumentos."
        ),
        "codigo": (
            "# Vulnerável\nos.system(f\"ping {host}\")\n\n"
            "# Seguro\nsubprocess.run([\"ping\", \"-c\", \"1\", host], shell=False)"
        ),
    },
    "lfi_path_traversal": {
        "problema": (
            "O parâmetro é usado para montar um caminho de arquivo no servidor, "
            "permitindo navegar para fora do diretório esperado com sequências "
            "como `../../etc/passwd`."
        ),
        "solucao": (
            "Nunca monte caminhos de arquivo a partir de entrada do usuário; use "
            "um mapeamento fixo (allowlist) de identificadores para caminhos reais."
        ),
        "codigo": (
            "# Vulnerável\nopen(f\"templates/{nome_arquivo}\")\n\n"
            "# Seguro\nopen(MAPA_DE_ARQUIVOS_PERMITIDOS[nome_arquivo])"
        ),
    },
    "upload_extension": {
        "problema": (
            "O upload aceita extensões/arquivos que podem ser interpretados como "
            "código executável pelo servidor (ex.: .php, .jsp) em vez de apenas "
            "o tipo de arquivo esperado."
        ),
        "solucao": (
            "Valide o tipo real do arquivo pelo conteúdo (magic bytes), não pela "
            "extensão, e armazene uploads fora da raiz executável do servidor."
        ),
        "codigo": (
            "# Vulnerável\nif nome.endswith(('.jpg', '.png')): salvar(arquivo)\n\n"
            "# Seguro\nif detectar_mime_real(arquivo) in MIME_PERMITIDOS: salvar(arquivo)"
        ),
    },
    "xxe": {
        "problema": (
            "O parser XML processa entidades externas definidas no próprio "
            "documento, permitindo leitura de arquivos locais ou SSRF via "
            "`<!ENTITY ... SYSTEM ...>`."
        ),
        "solucao": "Desabilite a resolução de entidades externas e DTDs no parser XML utilizado.",
        "codigo": (
            "# Vulnerável\netree.parse(xml_usuario)\n\n"
            "# Seguro\nparser = etree.XMLParser(resolve_entities=False, no_network=True)\n"
            "etree.parse(xml_usuario, parser)"
        ),
    },
    "ssti": {
        "problema": (
            "A entrada do usuário é renderizada diretamente pela engine de "
            "templates do servidor, permitindo executar expressões da linguagem "
            "do template (ex.: `{{7*7}}`) e potencialmente código arbitrário."
        ),
        "solucao": (
            "Nunca renderize entrada do usuário como template; trate-a sempre "
            "como dado/variável, não como código do template."
        ),
        "codigo": (
            "# Vulnerável\nrender_template_string(f\"Olá {nome}\")\n\n"
            "# Seguro\nrender_template_string(\"Olá {{ nome }}\", nome=nome)"
        ),
    },
    "ldap_injection": {
        "problema": (
            "O valor é concatenado diretamente num filtro LDAP, permitindo "
            "alterar a lógica da busca (ex.: `*)(uid=*))(|(uid=*`) e burlar "
            "autenticação."
        ),
        "solucao": (
            "Escape os metacaracteres do LDAP (`* ( ) \\ NUL`) antes de montar "
            "o filtro, ou use uma biblioteca que faça isso automaticamente."
        ),
        "codigo": (
            "# Vulnerável\nfiltro = f\"(uid={usuario})\"\n\n"
            "# Seguro\nfiltro = f\"(uid={ldap.filter.escape_filter_chars(usuario)})\""
        ),
    },
    "ssi_injection": {
        "problema": (
            "O parâmetro é refletido numa página processada com Server Side "
            "Includes habilitado, permitindo executar diretivas como "
            "`<!--#exec cmd=\"...\"-->`."
        ),
        "solucao": (
            "Desabilite SSI em diretórios que servem conteúdo controlado pelo "
            "usuário, ou escape as sequências `<!--#` na saída."
        ),
        "codigo": "# Apache: remova 'Options +Includes' do diretório que recebe entrada do usuário.",
    },
    "format_string": {
        "problema": (
            "A entrada do usuário é usada como string de formatação (ex.: "
            "`printf(entrada)`), permitindo ler memória/pilha ou travar o "
            "processo com especificadores como `%s%s%s%n`."
        ),
        "solucao": "Nunca use entrada do usuário como string de formato; passe-a sempre como argumento de um formato fixo.",
        "codigo": "# Vulnerável\nprintf(entrada_usuario)\n\n# Seguro\nprintf(\"%s\", entrada_usuario)",
    },
    "java_deserialization": {
        "problema": (
            "Dados serializados fornecidos pelo usuário são desserializados "
            "diretamente, e classes com side-effects perigosos no classpath "
            "podem ser instanciadas (RCE via gadget chains)."
        ),
        "solucao": (
            "Evite desserializar dados não confiáveis; se necessário, use uma "
            "allowlist estrita de classes permitidas."
        ),
        "codigo": "# Seguro (Java 9+)\nois.setObjectInputFilter(filtroAllowlist);",
    },
    "fuzzing_generico": {
        "problema": (
            "Entradas fora do padrão esperado (caracteres especiais, unicode, "
            "strings extremamente longas ou malformadas) causam erro 500, "
            "exceções não tratadas ou comportamento inesperado, indicando "
            "falta de validação de entrada."
        ),
        "solucao": (
            "Valide o formato, tamanho e charset esperado de cada campo no "
            "backend, e trate exceções de parsing sem expor detalhes internos "
            "na resposta."
        ),
        "codigo": "try:\n    validar_schema(entrada)\nexcept ValidationError:\n    return erro_generico_400()",
    },
}


def kb_generico(categoria_ia: str) -> dict:
    """Fallback de última instância para uma categoria sem KB específico
    (ex.: uma categoria nova adicionada em cache_payloads sem entrada aqui ainda)."""
    nome = NOME_EXIBICAO.get(categoria_ia, categoria_ia)
    return {
        "ataque": nome,
        "problema": f"Comportamento anômalo identificado ao injetar payloads de {nome} neste campo.",
        "solucao": "Valide e sanitize a entrada de acordo com o contexto de uso (banco de dados, shell, template, parser, etc).",
        "codigo": f"# Consulte a documentação de segurança específica para {nome}.",
    }
