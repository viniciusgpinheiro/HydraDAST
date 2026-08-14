# Acesso pela Rede Local - Siga em Frente

## 🌐 Visão Geral

A aplicação "Siga em Frente" está configurada para ser acessível tanto localmente quanto pela rede local. Isso permite que máquinas virtuais Linux ou outros computadores na mesma rede possam realizar ataques contra a aplicação.

---

## 📍 Detectar o IP Local Automaticamente

Quando você executa a aplicação, ela **automaticamente detecta e exibe o IP local**:

```bash
python siga.py
```

**Saída esperada:**

```
================================================================================
🎓 MÁQUINA SIGA EM FRENTE - AULASHACK
================================================================================

✅ Aplicação iniciada com sucesso!

📍 URLS DE ACESSO:

  🖥️  Localhost:      http://127.0.0.1:5001
  🌐 Rede Local:      http://192.168.1.5:5001

================================================================================

💡 Dicas:
  • Use a primeira URL (localhost) para testar localmente
  • Use a segunda URL para acessar de outra máquina na rede
  • Para VMs Linux na mesma rede, use: http://<IP_ACIMA>:5001

================================================================================
```

---

## 🔍 Descobrir o IP Local Manualmente

Se por algum motivo precisar verificar o IP local, execute:

```bash
python get_network_info.py
```

**Saída esperada:**

```
================================================================================
🌐 INFORMAÇÕES DE REDE - SIGA EM FRENTE
================================================================================

🖥️  Nome da Máquina:     COMPUTADOR-USER
📍 IP Local (IPv4):     192.168.1.5

================================================================================

📱 COMO ACESSAR A APLICAÇÃO:

  ✅ De ESTA máquina:
     http://127.0.0.1:5001

  ✅ De OUTRA máquina na rede local:
     http://192.168.1.5:5001

================================================================================
```

---

## 🖥️ Acessar do Windows (Mesma Rede)

### Passo 1: Iniciar a Aplicação

```bash
python siga.py
```

Anote o IP que aparecer (ex: 192.168.1.5)

### Passo 2: Abrir em Outro Computador Windows

1. Abra o navegador no outro computador
2. Digite a URL:
   ```
   http://192.168.1.5:5001
   ```

3. Você verá a página de login

---

## 🐧 Acessar de uma VM Linux

### Passo 1: Verificar Conexão de Rede

A VM Linux deve estar na **mesma rede local** do Windows.

**Testando conectividade:**

```bash
# Na VM Linux, teste o ping
ping 192.168.1.5
```

Se o ping responder, a rede está configurada corretamente.

### Passo 2: Acessar a Aplicação

**Opção A: Via Navegador (se tiver interface gráfica)**

```bash
firefox http://192.168.1.5:5001
```

ou

```bash
chromium-browser http://192.168.1.5:5001
```

**Opção B: Via cURL (recomendado para testes)**

```bash
# Teste de conectividade
curl -I http://192.168.1.5:5001

# Acessar a página de login
curl http://192.168.1.5:5001
```

**Opção C: Via Ferramentas de Pentest**

```bash
# Com nmap (descoberta)
nmap -p 5001 192.168.1.5

# Com burp suite proxy
# Configurar proxy em: 192.168.1.5:8080 (se tiver proxy)

# Com ferramentas Python
python3 -c "
import requests
response = requests.get('http://192.168.1.5:5001')
print(response.status_code)
print(response.text)
"
```

---

## 🔧 Configuração de Rede (Detalhes)

### Como a Aplicação Funciona

A aplicação Flask está configurada para:

1. **Escutar em TODAS as interfaces de rede:** `0.0.0.0:5001`
2. **Detectar automaticamente o IP local** ao iniciar
3. **Exibir as URLs de acesso** no console

### Arquitetura de Rede

```
┌─────────────────────────────────────────────┐
│        REDE LOCAL (192.168.1.0/24)          │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │   Windows (Servidor da Aplicação)  │   │
│  │   IP: 192.168.1.5                  │   │
│  │   Porta: 5001                       │   │
│  │   http://192.168.1.5:5001          │   │
│  └─────────────────────────────────────┘   │
│                     │                       │
│                     │ Rede Local            │
│                     │                       │
│  ┌─────────────────────────────────────┐   │
│  │   VM Linux (Atacante)               │   │
│  │   IP: 192.168.1.10                  │   │
│  │   Executa exploits contra 192.168...│   │
│  └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

---

## ⚠️ Firewall do Windows

Se não conseguir acessar de outra máquina, provavelmente é o firewall do Windows bloqueando.

### Abrir Porta 5001 no Firewall Windows

**Método 1: Windows Defender Firewall (GUI)**

1. Abra **Windows Defender Firewall**
2. Clique em **Permitir um aplicativo através do firewall**
3. Clique em **Permitir outro app...**
4. Selecione `python.exe` (ou a aplicação)
5. Marque **Privada** (rede local)
6. Clique em **Adicionar**

**Método 2: PowerShell (Administrador)**

```powershell
# Abrir PowerShell como Administrador

# Permitir a porta 5001
New-NetFirewallRule -DisplayName "Siga em Frente - Porta 5001" `
  -Direction Inbound -Action Allow -Protocol TCP -LocalPort 5001 `
  -Profile Private

# Verificar se funcionou
Get-NetFirewallRule -DisplayName "Siga em Frente*"

# Se precisar remover depois
Remove-NetFirewallRule -DisplayName "Siga em Frente*"
```

**Método 3: CMD (Administrador)**

```cmd
# Abrir CMD como Administrador

netsh advfirewall firewall add rule name="Siga em Frente Port 5001" `
  dir=in action=allow protocol=tcp localport=5001 profile=private
```

---

## ✅ Checklist de Configuração de Rede

- [ ] Aplicação executando em Windows com `python siga.py`
- [ ] IP local exibido no console (ex: 192.168.1.5)
- [ ] Firewall do Windows permite porta 5001
- [ ] VM Linux está na mesma rede local
- [ ] VM Linux consegue fazer ping no IP do Windows
- [ ] VM Linux consegue acessar `http://192.168.1.5:5001`

---

## 🔐 Segurança de Rede

### ⚠️ IMPORTANTE

- A porta 5001 está **ABERTA** para toda a rede local
- Qualquer computador na rede pode acessar
- Use **APENAS** em ambiente de laboratório/aula
- **NÃO** exponha para a internet pública

### Limitar Acesso

Se quiser limitar para apenas uma VM específica:

**PowerShell:**

```powershell
New-NetFirewallRule -DisplayName "Siga em Frente - VM Linux" `
  -Direction Inbound -Action Allow -Protocol TCP -LocalPort 5001 `
  -RemoteAddress 192.168.1.10 -Profile Private
```

---

## 🧪 Testando Acesso da VM Linux

### Passo 1: Na VM Linux

```bash
# Instalar curl (se não tiver)
sudo apt-get install curl

# Testar conectividade
ping 192.168.1.5
curl -I http://192.168.1.5:5001
```

### Passo 2: Fazer Login (Exemplo)

```bash
# Fazer login como operador
curl -c cookies.txt \
  -d "username=Igor&password=oper1-cab1" \
  http://192.168.1.5:5001/login

# Acessar dashboard (com cookie)
curl -b cookies.txt \
  http://192.168.1.5:5001/dashboard/operator?id=1
```

### Passo 3: Realizar Exploits

Agora você pode executar exploits de pentest:

```bash
# Teste de IDOR
curl -b cookies.txt http://192.168.1.5:5001/dashboard/operator?id=2
curl -b cookies.txt http://192.168.1.5:5001/dashboard/admin?id=101

# Teste de CSRF (criar página maliciosa e servir)
python3 -m http.server 8000

# Teste de XSS (via curl)
curl -X POST http://192.168.1.5:5001/message \
  -d 'recipient_id=1&content=<img src=x onerror="alert(1)">'

# Teste de File Upload
curl -F "file=@backdoor.py" http://192.168.1.5:5001/files
```

---

## 🎓 Cenário de Aula Completo

### Setup Inicial

**No Windows (Host da Aplicação):**

```bash
# 1. Navegar para pasta do projeto
cd siga-em-frente

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Criar banco de dados
python init_db.py

# 4. Iniciar aplicação
python siga.py
# Anote o IP que aparecer!
```

**No Linux (VM Atacante):**

```bash
# 1. Verificar conectividade
ping 192.168.1.5

# 2. Testar acesso
curl -I http://192.168.1.5:5001

# 3. Executar exploits conforme as instruções da aula
# ...
```

---

## 🆘 Troubleshooting

### Problema: "Connection refused" da VM Linux

**Solução:**

1. Verifique se Windows está rodando a aplicação:
   ```bash
   # Na VM Linux
   netstat -an | grep 5001
   ```

2. Verifique firewall:
   ```powershell
   # No Windows
   Get-NetFirewallRule | Select-Object DisplayName | findstr "5001"
   ```

3. Teste ping:
   ```bash
   ping 192.168.1.5
   ```

### Problema: IP errado ou não detectado

**Solução:**

Execute o script de informações de rede:

```bash
python get_network_info.py
```

### Problema: Firewall bloqueia em silêncio

**Solução:**

Desative temporariamente o firewall:

```powershell
# Desativar (temporário, só para teste)
Set-NetFirewallProfile -Profile Private -Enabled $False

# Reativar
Set-NetFirewallProfile -Profile Private -Enabled $True
```

---

## 📚 Documentação Relacionada

- `README.md` - Visão geral da aplicação
- `INICIO_RAPIDO.md` - Primeiros passos
- `GUIA_DE_USO.md` - Como usar a aplicação
- `LISTA_COMPLETA_4_VULNERABILIDADES.md` - Detalhes técnicos

---

**Desenvolvido por AulasHack**
**Data:** Janeiro 2026

