# 📋 LISTA COMPLETA - 15 VULNERABILIDADES DO BANCO GRANA FÁCIL

**Última Atualização:** 31/01/2026  
**Versão:** 3.0 (incluindo VULN-15)

---

## 🔴 CRÍTICAS (4) - 27%

### VULN-01: SQL Injection (Error-Based)
- **CVSS:** 9.8
- **Vector:** CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
- **CWE:** CWE-89
- **OWASP:** A03:2021 - Injection
- **Local:** Campo de senha (/login)
- **Impacto:** Bypass completo de autenticação
- **Exploração:** `' OR '1'='1' --`

---

### VULN-02: Command Injection (RCE)
- **CVSS:** 10.0 ⚠️ **MÁXIMA**
- **Vector:** CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H
- **CWE:** CWE-78
- **OWASP:** A03:2021 - Injection
- **Local:** Botão de suporte (/support)
- **Impacto:** Execução remota de código (RCE)
- **Exploração:** `whoami`, `cat /etc/passwd`

---

### VULN-03: Senhas em Texto Claro no Banco de Dados
- **CVSS:** 9.1
- **Vector:** CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N
- **CWE:** CWE-257
- **OWASP:** A02:2021 - Cryptographic Failures
- **Local:** Banco SQLite (banco_digital.db)
- **Impacto:** Exposição de todas as credenciais de usuários
- **Exploração:** `sqlite3 banco_digital.db "SELECT * FROM usuarios;"`

---

### VULN-14: Armazenamento Inseguro de Credenciais Críticas
- **CVSS:** 9.0
- **Vector:** CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:H
- **CWE:** CWE-522, CWE-798
- **OWASP:** A02:2021 - Cryptographic Failures
- **Local:** Página /admin1 (HTML)
- **Impacto:** Exposição de credenciais de infraestrutura (servidor, DB, VPN, API)
- **Exploração:** Visualizar código-fonte HTML

---

## 🟠 ALTAS (4) - 27%

### VULN-04: Token de Reset Previsível
- **CVSS:** 8.1
- **Vector:** CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N
- **CWE:** CWE-330
- **OWASP:** A02:2021 - Cryptographic Failures
- **Local:** Funcionalidade de reset (/reset)
- **Impacto:** Recuperação de senhas através de decodificação (Base64 + ROT13)
- **Exploração:** Decodificar token com CyberChef

---

### VULN-05: Página Administrativa sem Autenticação
- **CVSS:** 7.5
- **Vector:** CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N
- **CWE:** CWE-306
- **OWASP:** A01:2021 - Broken Access Control
- **Local:** URL /admin1
- **Impacto:** Acesso não autorizado a área administrativa
- **Exploração:** Fuzzing com Gobuster/Dirsearch

---

### VULN-06: Ausência de HTTPS
- **CVSS:** 7.4
- **Vector:** CVSS:3.1/AV:A/AC:L/PR:N/UI:N/S:C/C:H/I:N/A:N
- **CWE:** CWE-319
- **OWASP:** A02:2021 - Cryptographic Failures
- **Local:** Protocolo HTTP
- **Impacto:** Dados trafegam em texto claro, Man-in-the-Middle
- **Exploração:** Wireshark, tcpdump

---

### VULN-09: Ausência de CAPTCHA ⭐ RECLASSIFICADA!
- **CVSS:** 8.6 ⬆️ (era 5.3 MÉDIA)
- **Vector:** CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:L
- **CWE:** CWE-837
- **OWASP:** A07:2021 - Authentication Failures
- **Local:** Todos os formulários
- **Impacto:** Account Takeover em massa via força bruta automatizada
- **Exploração:** Hydra, scripts Python, Burp Intruder
- **Nota:** DEFESA PRIMÁRIA contra força bruta (bloqueia, não apenas desacelera)

---

## 🟡 MÉDIAS (6) - 40%

### VULN-07: Enumeração de Usuários
- **CVSS:** 5.3
- **Vector:** CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N
- **CWE:** CWE-200
- **OWASP:** A01:2021 - Broken Access Control
- **Local:** Mensagens de erro no login
- **Impacto:** Identificação de usuários válidos ("incorretos!" vs "incorretos")
- **Exploração:** Script Python comparando mensagens

---

### VULN-08: Ausência de Rate Limiting
- **CVSS:** 5.3
- **Vector:** CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:L
- **CWE:** CWE-307
- **OWASP:** A07:2021 - Authentication Failures
- **Local:** Endpoint /login
- **Impacto:** Força bruta ilimitada (mas contornável)
- **Exploração:** 10.000 requisições sem bloqueio
- **Nota:** Defesa SECUNDÁRIA (desacelera, não bloqueia)

---

### VULN-10: Ausência de Multi-Factor Authentication (MFA)
- **CVSS:** 6.5
- **Vector:** CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N
- **CWE:** CWE-308
- **OWASP:** A07:2021 - Authentication Failures
- **Local:** Sistema de autenticação
- **Impacto:** Falta de segunda camada de proteção
- **Exploração:** Login apenas com senha

---

### VULN-11: Falta de Validação e Sanitização de Entrada
- **CVSS:** 6.1
- **Vector:** CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N
- **CWE:** CWE-20
- **OWASP:** A03:2021 - Injection
- **Local:** Todos os campos de entrada
- **Impacto:** Base para múltiplas vulnerabilidades (SQLi, Command Injection)
- **Exploração:** Inputs maliciosos aceitos sem validação

---

### VULN-12: Headers de Segurança Ausentes
- **CVSS:** 4.3
- **Vector:** CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N
- **CWE:** CWE-1021
- **OWASP:** A05:2021 - Security Misconfiguration
- **Local:** HTTP Response Headers
- **Impacto:** Vulnerabilidade a clickjacking, MIME-sniffing, XSS
- **Exploração:** Verificação com securityheaders.com

---

### VULN-15: Ausência de Política de Senhas Fortes ⭐ NOVA!
- **CVSS:** 5.3
- **Vector:** CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:L/A:N
- **CWE:** CWE-521
- **OWASP:** A07:2021 - Authentication Failures
- **Local:** Sistema de criação de contas
- **Impacto:** Facilita força bruta (ataque em MINUTOS vs ANOS)
- **Exploração:** Senhas aceitas: "1", "123", "senha123", username==password
- **Nota:** Reduz espaço de busca em 99.999%!
- **PoC:** `python poc_vuln15_weak_passwords.py`

---

## 🟢 BAIXAS (1) - 7%

### VULN-13: Logging e Monitoramento Inadequados
- **CVSS:** 3.1
- **Vector:** CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:N/I:L/A:N
- **CWE:** CWE-778
- **OWASP:** A09:2021 - Security Logging Failures
- **Local:** Sistema de logging
- **Impacto:** Dificuldade de detectar ataques, investigação forense impossível
- **Exploração:** 10.000+ tentativas de ataque não registradas

---

## 📊 ESTATÍSTICAS FINAIS

| Métrica | Valor |
|---------|-------|
| **Total de Vulnerabilidades** | 15 |
| **CVSS Médio** | 6.9 |
| **CRÍTICAS ou ALTAS** | 8 (53%) |
| **Exploráveis remotamente** | 14 (93%) |
| **Sem autenticação necessária** | 12 (80%) |
| **Com PoC disponível** | 15 (100%) |

---

## 🎯 TOP 5 POR IMPACTO

| # | VulnID | Título | CVSS | Impacto |
|---|--------|--------|------|---------|
| 1 | VULN-02 | Command Injection | **10.0** | RCE completo |
| 2 | VULN-01 | SQL Injection | 9.8 | Bypass auth |
| 3 | VULN-03 | Senhas em texto claro (Banco) | 9.1 | Todas as credenciais |
| 4 | VULN-14 | Credenciais expostas (Infra) | 9.0 | Infraestrutura |
| 5 | VULN-09 | Sem CAPTCHA | 8.6 | Account Takeover |

---

## 🔗 ATAQUES ENCADEADOS

### **Ataque 1: Enumeração + Senhas Fracas + Força Bruta**
```
VULN-07 (Enumeração) 
   ↓ Identifica 10 usuários válidos
VULN-15 (Senhas fracas) ⭐ NOVA
   ↓ 40% usam senhas triviais
VULN-09 (Sem CAPTCHA)
   ↓ Força bruta automatizada ilimitada
RESULTADO: Account Takeover de 4 contas em 2 HORAS
```

**Impacto:** Reduz tempo de ataque de **200 ANOS para 2 HORAS**!

---

### **Ataque 2: SQLi + Exfiltração de Credenciais**
```
VULN-01 (SQL Injection)
   ↓ Acessa banco de dados
VULN-03 (Senhas em texto claro)
   ↓ Exfiltra TODAS as credenciais
RESULTADO: Comprometimento de 100% das contas
```

---

### **Ataque 3: Fuzzing + Credenciais de Infraestrutura**
```
VULN-05 (Página sem auth)
   ↓ Descobre /admin1
VULN-14 (Credenciais expostas)
   ↓ Acessa servidor, DB, VPN, API
RESULTADO: Comprometimento da infraestrutura completa
```

---

## 🔒 PRIORIDADES DE REMEDIAÇÃO

### **🔴 URGENTE (Esta Semana):**

| # | VulnID | Ação | Complexidade |
|---|--------|------|--------------|
| 1 | VULN-02 | Remover botão de suporte | Baixa |
| 2 | VULN-01 | Prepared statements | Média |
| 3 | VULN-03 | Hash de senhas (bcrypt) | Média |
| 4 | VULN-14 | Remover credenciais + rotacionar | Alta |

**Tempo estimado:** 2-3 dias de desenvolvimento

---

### **🟠 ALTA (Este Mês):**

| # | VulnID | Ação | Complexidade |
|---|--------|------|--------------|
| 5 | VULN-09 | Implementar reCAPTCHA ⚠️ | Média |
| 6 | VULN-15 | Política de senhas fortes ⭐ | Média |
| 7 | VULN-06 | Implementar HTTPS | Alta |
| 8 | VULN-05 | Autenticação em /admin1 | Baixa |
| 9 | VULN-04 | Tokens criptográficos seguros | Média |

**Tempo estimado:** 2-3 semanas de desenvolvimento

---

### **🟡 MÉDIA (3 Meses):**

| # | VulnID | Ação | Complexidade |
|---|--------|------|--------------|
| 10 | VULN-10 | Implementar MFA | Alta |
| 11 | VULN-08 | Rate limiting | Média |
| 12 | VULN-07 | Mensagens genéricas | Baixa |
| 13 | VULN-11 | Validação de entrada | Média |
| 14 | VULN-12 | Headers de segurança | Baixa |

**Tempo estimado:** 1-2 meses de desenvolvimento

---

### **🟢 BAIXA (6 Meses):**

| # | VulnID | Ação | Complexidade |
|---|--------|------|--------------|
| 15 | VULN-13 | Logging e SIEM | Alta |

**Tempo estimado:** 1-2 meses de desenvolvimento + integração

---

## 📚 FERRAMENTAS POR VULNERABILIDADE

| VulnID | Ferramentas Usadas |
|--------|--------------------|
| VULN-01 | SQLMap, Burp Suite |
| VULN-02 | Terminal, curl, netcat |
| VULN-03 | SQLite Browser, sqlite3 |
| VULN-04 | CyberChef, scripts Python |
| VULN-05 | Gobuster, Dirsearch, ffuf |
| VULN-06 | Wireshark, tcpdump |
| VULN-07 | Scripts Python, Burp Intruder |
| VULN-08 | Hydra, scripts Python |
| VULN-09 | Hydra, scripts Python, Burp |
| VULN-10 | Análise manual |
| VULN-11 | Testes manuais |
| VULN-12 | securityheaders.com, curl |
| VULN-13 | Análise de logs |
| VULN-14 | View Source, Inspecionar elemento |
| VULN-15 | poc_vuln15_weak_passwords.py ⭐ |

---

## 🎓 MÓDULOS DO CURSO

### **Módulo 1: Vulnerabilidades Básicas (Iniciante)**
- Aula 1: VULN-07 - Enumeração de Usuários
- Aula 2: VULN-05 - Página Oculta (Fuzzing)
- Aula 3: VULN-13 - Logging Inadequado
- Aula 4: VULN-12 - Headers de Segurança

### **Módulo 2: Autenticação e Senhas (Intermediário)**
- Aula 5: VULN-15 - Política de Senhas ⭐ NOVA
- Aula 6: VULN-08 - Rate Limiting (Defesa Secundária)
- Aula 7: VULN-09 - CAPTCHA (Defesa Primária) ⚠️
- Aula 8: VULN-10 - MFA (Defesa Final)
- Aula 9: VULN-04 - Token de Reset
- **Lab:** Ataque Encadeado (VULN-07 + VULN-15 + VULN-09)

### **Módulo 3: Injeções (Avançado)**
- Aula 10: VULN-01 - SQL Injection ⭐
- Aula 11: VULN-02 - Command Injection ⭐
- Aula 12: VULN-11 - Validação de Entrada
- **Lab:** Exploração completa (SQLi + RCE)

### **Módulo 4: Criptografia e Segredos (Avançado)**
- Aula 13: VULN-03 - Senhas em Texto Claro (Banco) ⭐
- Aula 14: VULN-14 - Credenciais em Texto Claro (Infra) ⭐
- Aula 15: VULN-06 - Ausência de HTTPS
- **Lab:** Secrets Management (Vault, AWS Secrets Manager)

---

## 💰 IMPACTO FINANCEIRO ESTIMADO

### **Cenário: 10.000 Clientes**

**Sem correções:**
- Contas comprometidas: 8.000-9.000 (80-90%)
- Prejuízo médio por conta: R$ 5.000
- **Prejuízo total: R$ 40.000.000 - R$ 45.000.000**
- Multas LGPD: R$ 50.000.000
- Dano à reputação: R$ 100.000.000+
- **TOTAL: R$ 190.000.000+**

**Com correções:**
- Contas comprometidas: < 10 (< 0.1%)
- Prejuízo total: R$ 50.000
- **Economia: R$ 189.950.000**

**ROI da Segurança:** 1.899x (189.900%)

---

## 🔐 DEFESA EM PROFUNDIDADE

### **Camada 1: Prevenção de Entrada**
- ✅ VULN-11: Validação de entrada
- ✅ VULN-15: Política de senhas fortes ⭐
- ✅ VULN-09: CAPTCHA

### **Camada 2: Autenticação Forte**
- ✅ VULN-10: MFA
- ✅ VULN-08: Rate limiting
- ✅ VULN-07: Mensagens genéricas

### **Camada 3: Proteção de Dados**
- ✅ VULN-03: Hash de senhas
- ✅ VULN-14: Secrets management
- ✅ VULN-06: HTTPS

### **Camada 4: Controle de Acesso**
- ✅ VULN-05: Autenticação admin
- ✅ VULN-01: Prepared statements

### **Camada 5: Detecção e Resposta**
- ✅ VULN-13: Logging e monitoramento
- ✅ VULN-12: Security headers

---

## 📎 REFERÊNCIAS E RECURSOS

### **Frameworks e Metodologias:**
- OWASP Top 10 2021
- OWASP Testing Guide v4.2
- PTES (Penetration Testing Execution Standard)
- NIST SP 800-115

### **CWE Top 25:**
- CWE-89, CWE-78, CWE-257, CWE-522, CWE-798, CWE-330, CWE-306, CWE-319, CWE-837, CWE-200, CWE-307, CWE-308, CWE-20, CWE-1021, CWE-521 ⭐, CWE-778

### **CVSS Calculator:**
- https://www.first.org/cvss/calculator/3.1

### **Ferramentas Recomendadas:**
- Burp Suite Professional
- OWASP ZAP
- SQLMap
- Gobuster/ffuf
- Hydra
- Wireshark

---

**Total de Vulnerabilidades:** 15  
**Última Atualização:** 31/01/2026 15:55  
**Status:** Completo e Aprovado ✅

---

**Powered by AulasHack Security** 🎓🔒
