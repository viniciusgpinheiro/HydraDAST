# 💰 Banco Digital Grana Fácil - Ambiente de Treinamento

## 📖 Sobre o Projeto

Ambiente web vulnerável **INTENCIONALMENTE** para treinamento de pentesting e segurança ofensiva. Simula um banco digital com 7 vulnerabilidades reais, permitindo prática em ambiente controlado e legal.

## ⚠️ AVISO IMPORTANTE

🔴 **USO EXCLUSIVAMENTE EDUCACIONAL**
- Vulnerabilidades INTENCIONAIS para fins didáticos
- Use APENAS em localhost ou rede local isolada
- NUNCA exponha à internet pública
- NUNCA use estas técnicas sem autorização
- Pentest não autorizado é CRIME

## 🎓 Público-Alvo

- Estudantes de segurança da informação
- Profissionais iniciantes em pentest
- Instrutores de cybersecurity
- Entusiastas de segurança ofensiva

## 🔥 Vulnerabilidades Implementadas

### 1. 🔍 Enumeração de Usuários
- Mensagens sutilmente diferentes revelam existência
- "incorretos!" vs "incorretos"

### 2. 💉 SQL Injection (Error-Based)
- Campo de senha vulnerável a SQLi direto
- Bypass completo de autenticação possível
- Erros SQL expostos ao usuário

### 3. 💻 Command Injection
- Botão de suporte executa comandos do sistema
- RCE (Remote Code Execution) possível
- Comandos: whoami, ping, ls, etc.

### 4. 🔓 Token de Reset Previsível
- Token baseado na senha usando ROT13 + Base64
- Decodificação revela a senha original
- Desafio: usuário deve decodificar o token

### 5. 🕵️ Página Oculta (`/admin1`)
- Painel administrativo sem autenticação
- Descobrível por fuzzing

### 6. 🔐 Armazenamento Inseguro de Credenciais (NOVA!)
- Credenciais críticas em texto claro na página /admin1
- Servidor, DB, API Keys, VPN expostos
- Violação grave de Secrets Management

### 7. 🗄️ Senhas em Texto Claro no Banco
- SQLite armazena senhas sem criptografia
- Banco de dados completamente exposto
- Todas as credenciais acessíveis

### 8. 🌐 Ausência de HTTPS
- Protocolo HTTP sem TLS/SSL
- Dados trafegam em texto claro
- Ataques Man-in-the-Middle possíveis

### 9. 💥 Sem Proteções de Segurança
- Zero CAPTCHA
- Zero Rate Limiting
- Zero MFA
- Zero bloqueio de conta

### 10-14. Outras Vulnerabilidades
- Falta de validação de entrada
- Headers de segurança ausentes
- Logging inadequado

## 📁 Estrutura do Projeto

```
.
├── vulnerable_app.py      # Aplicativo Flask com vulnerabilidades
├── exploit_demo.py        # Script de demonstração automática
├── requirements.txt       # Dependências (Flask, SQLAlchemy)
├── GUIA_DE_USO.md        # Guia detalhado para alunos
├── README.md             # Este arquivo
└── banco_digital.db      # Banco SQLite (criado automaticamente)
```

## 🚀 Início Rápido

### Pré-requisitos
```bash
# Python 3.7+
python3 --version

# pip
pip --version
```

### Instalação em 3 Passos

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Executar o servidor
python granafacil-web.py

# 3. Abrir no navegador
# Local:  http://127.0.0.1:5000
# Rede:   http://[SEU_IP]:5000
```

## 🧪 Demonstração Automática

```bash
# Execute o script de demonstração
python exploit_demo.py
```

Este script demonstra automaticamente:
- ✓ Enumeração de usuários
- ✓ SQL Injection
- ✓ Command Injection
- ✓ Decodificação de token
- ✓ Descoberta de página oculta
- ✓ Extração do banco de dados
- ✓ Força bruta

## 👥 Credenciais para Teste

| Usuário | Senha | Nota |
|---------|-------|------|
| admin | senhaForte123! | Usuário administrativo |
| root | P@ssw0rd2024! | Usuário root |
| usuario1 | senha123 | Senha fraca |
| maria | maria2020 | Senha na rockyou.txt |
| john | john456 | Senha comum |

## 🛠️ Ferramentas Recomendadas

### Essenciais
- **Burp Suite Community** - Proxy e interceptação
- **OWASP ZAP** - Scanner automático
- **CyberChef** - Decodificação de dados

### Reconhecimento
- **Nmap** - Port scanning
- **Gobuster** - Fuzzing de diretórios
- **Dirsearch** - Descoberta de arquivos
- **Nikto** - Scanner de vulnerabilidades web

### Exploração
- **SQLMap** - Exploração automatizada de SQLi
- **Hydra** - Força bruta
- **Wireshark** - Análise de tráfego
- **Python/Requests** - Scripts customizados

## 📚 Material Didático

### Para Instrutores

**Duração Sugerida:** 8 horas (1 dia)

**Agenda:**
1. Introdução à Segurança Web (30min)
2. Enumeração e Reconhecimento (1h)
3. SQL Injection (1.5h)
4. Command Injection (1h)
5. Análise de Tokens (1h)
6. Fuzzing e Descoberta (1h)
7. Análise de Banco de Dados (1h)
8. Mitigações e Boas Práticas (1h)

**Recursos Incluídos:**
- ✅ Código-fonte comentado
- ✅ Guia detalhado (GUIA_DE_USO.md)
- ✅ Scripts de exploração prontos
- ✅ Exercícios progressivos
- ✅ Checklist de mitigações

### Para Alunos

Consulte o **GUIA_DE_USO.md** para:
- Instruções passo a passo
- Comandos e scripts prontos
- Exemplos práticos
- Exercícios graduais
- Dicas e soluções

## 🎯 Exercícios Práticos

### Nível Básico (2h)
- [ ] Enumerar todos os 5 usuários
- [ ] Encontrar a página `/admin1`
- [ ] Fazer login com credenciais fornecidas

### Nível Intermediário (3h)
- [ ] Bypass de login via SQL Injection
- [ ] Executar comandos via Command Injection
- [ ] Decodificar token de reset
- [ ] Força bruta em usuário conhecido

### Nível Avançado (3h)
- [ ] Criar script de enumeração automatizado
- [ ] Extrair todas as senhas do banco
- [ ] Cadeia completa: enum → SQLi → RCE
- [ ] Gerar relatório de pentest profissional

## 🔒 Mitigações (Para Discussão)

### SQL Injection
```python
# ❌ ERRADO (Vulnerável)
query = f"SELECT * FROM users WHERE user='{username}'"

# ✅ CORRETO (Seguro)
query = "SELECT * FROM users WHERE user=?"
cursor.execute(query, (username,))
```

### Command Injection
```python
# ❌ ERRADO
subprocess.run(user_input, shell=True)

# ✅ CORRETO
allowed_commands = ['ping', 'whoami']
if command in allowed_commands:
    subprocess.run([command], shell=False)
```

### Token de Reset
```python
# ❌ ERRADO
token = base64(rot13(password))

# ✅ CORRETO
import secrets
token = secrets.token_urlsafe(32)
# Salvar com expiração em banco
```

### Senhas no Banco
```python
# ❌ ERRADO
password = "senha123"

# ✅ CORRETO
from werkzeug.security import generate_password_hash
password = generate_password_hash("senha123")
```

### Rate Limiting
```python
# ✅ CORRETO
from flask_limiter import Limiter
limiter = Limiter(app)

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    pass
```

## 🐛 Resolução de Problemas

### Porta 5000 já em uso
```bash
# Linux/Mac
lsof -i :5000
kill -9 <PID>

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Dependências não instaladas
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Banco de dados corrompido
```bash
rm banco_digital.db
python vulnerable_app.py
```

### Servidor não responde na rede
```bash
# Verificar firewall
sudo ufw allow 5000

# Verificar IP
ip addr show  # Linux
ipconfig      # Windows
```

## 📊 Mapeamento OWASP Top 10 2021

| Vulnerabilidade | OWASP 2021 | Severidade |
|----------------|------------|------------|
| Enumeração | A01:2021 - Broken Access Control | Média |
| SQL Injection | A03:2021 - Injection | **CRÍTICA** |
| Command Injection | A03:2021 - Injection | **CRÍTICA** |
| Token Previsível | A02:2021 - Cryptographic Failures | Alta |
| Página sem Auth | A01:2021 - Broken Access Control | Alta |
| Senhas em Texto Claro | A02:2021 - Cryptographic Failures | **CRÍTICA** |
| Sem Rate Limiting | A07:2021 - Auth Failures | Média |

## 🌟 Recursos Adicionais

### Links Úteis
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [PortSwigger Academy](https://portswigger.net/web-security)
- [HackTheBox](https://www.hackthebox.com)
- [TryHackMe](https://tryhackme.com)
- [PentesterLab](https://pentesterlab.com)

### Ambientes Similares
- **DVWA** (Damn Vulnerable Web Application)
- **WebGoat** (OWASP)
- **Juice Shop** (OWASP)
- **bWAPP** (Buggy Web Application)
- **Mutillidae**

## 📝 Changelog

### v2.0 (2025-01-30)
- ✨ Novo design: Banco Digital Grana Fácil
- ✨ Banco de dados SQLite + SQLAlchemy
- ✨ SQL Injection Error-Based
- ✨ Command Injection no suporte
- ✨ Token baseado em senha (não username)
- ✨ Página oculta mudada para `/admin1`
- ✨ Senhas em texto claro no banco
- ✨ Servidor em loopback + rede local
- ✨ Usuário `root` adicionado
- ✨ Senha `maria` alterada para rockyou.txt

### v1.0 (2025-01-30)
- ✨ Implementação inicial
- ✨ 5 vulnerabilidades básicas

## 👨‍💻 Autor

Criado para cursos de pentest e segurança ofensiva.

## 📄 Licença

**APENAS PARA FINS EDUCACIONAIS**

Ao usar este software, você concorda que:
- Usará apenas em ambiente local/controlado
- Não exporá à internet ou redes públicas
- Não aplicará técnicas sem autorização
- Entende que pentest não autorizado é ilegal
- Assume responsabilidade pelo uso ético

## 🤝 Contribuindo

Sugestões de melhorias são bem-vindas!

**Ideias para futuras versões:**
- [ ] XSS (Cross-Site Scripting)
- [ ] CSRF (Cross-Site Request Forgery)
- [ ] XXE (XML External Entity)
- [ ] SSRF (Server-Side Request Forgery)
- [ ] Insecure Deserialization
- [ ] File Upload vulnerável
- [ ] Path Traversal
- [ ] IDOR (Insecure Direct Object References)

## 💬 Suporte

Para dúvidas:
1. Consulte o `GUIA_DE_USO.md`
2. Revise os comentários no código
3. Execute `python exploit_demo.py` para ver exemplos

---

## 🎓 Dicas Finais

**Para Alunos:**
- Comece pelo básico (enumeração e fuzzing)
- Documente cada descoberta
- Pratique criar seus próprios scripts
- Entenda o **porquê** de cada vulnerabilidade
- Aprenda as mitigações corretas

**Para Instrutores:**
- Use como ambiente prático após teoria
- Incentive a criação de relatórios profissionais
- Discuta impactos reais de cada falha
- Compare com casos reais do OWASP
- Ensine defesa, não apenas ataque

---

**⚠️ LEMBRETE FINAL:** 

Use este conhecimento de forma **ÉTICA** e **RESPONSÁVEL**. 

O objetivo é aprender a **DEFENDER** sistemas, não atacá-los ilegalmente.

**🎓 Bom treinamento e aprendizado responsável!**

---

## 📊 Estatísticas das Vulnerabilidades

| Severidade | Quantidade | Percentual |
|------------|-----------|-----------|
| **CRÍTICA** | 4 | 29% |
| **ALTA** | 4 | 29% |
| **MÉDIA** | 5 | 36% |
| **BAIXA** | 1 | 7% |
| **TOTAL** | **14** | **100%** |

### 🎯 Vulnerabilidades por Categoria:

**🔴 CRÍTICAS (4):**
1. SQL Injection - CVSS 9.8
2. Command Injection - CVSS 10.0
3. Senhas em Texto Claro (Banco) - CVSS 9.1
4. Armazenamento Inseguro de Credenciais - CVSS 9.0

**🟠 ALTAS (4):**
1. Token de Reset Previsível - CVSS 8.1
2. Página Admin sem Autenticação - CVSS 7.5
3. Ausência de HTTPS - CVSS 7.4
4. **Ausência de CAPTCHA - CVSS 8.6** ⭐ **(RECLASSIFICADA!)**

**🟡 MÉDIAS (5):**
1. Enumeração de Usuários - CVSS 5.3
2. Ausência de Rate Limiting - CVSS 5.3
3. Ausência de MFA - CVSS 6.5
4. Falta de Validação de Entrada - CVSS 6.1
5. Headers de Segurança Ausentes - CVSS 4.3

**🟢 BAIXAS (1):**
1. Logging Inadequado - CVSS 3.1

---

## ⚠️ NOTA IMPORTANTE: VULN-09 Reclassificada

A **VULN-09 (Ausência de CAPTCHA)** foi **reclassificada de MÉDIA para ALTA**.

**Razão:** CAPTCHA é a defesa PRIMÁRIA contra força bruta automatizada. Sua ausência permite Account Takeover em massa, com taxa de sucesso de 30-40% em um contexto bancário, resultando em prejuízos milionários.

- **CVSS Anterior:** 5.3 (MÉDIA)
- **CVSS Atual:** 8.6 (ALTA) ⬆️
- **Impacto:** Comprometimento de contas via força bruta + enumeração

