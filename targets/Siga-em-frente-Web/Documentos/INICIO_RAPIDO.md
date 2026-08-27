# INÍCIO RÁPIDO - Siga em Frente

## 🚀 Executar em 3 Passos

### Passo 1: Instalar Dependências
```bash
pip install -r requirements.txt
```

### Passo 2: Criar Banco de Dados
```bash
python init_db.py
```

**⚠️ Importante:** Este comando irá exibir as **senhas aleatórias dos administradores**. Guarde essas senhas!

Saída esperada:
```
✓ Banco de dados inicializado com sucesso!
=== SENHAS DOS ADMINISTRADORES ===
Usuário: mario | Senha: abc123XYZ!@#
Usuário: bruno | Senha: def456UVW$%^
===================================
✓ 2 usuários administradores criados
✓ 9 operadores criados (3 por cabine)
✓ 3 cabines de pedágio criadas

Se você baixou a máquina com o banco já populado, as senhas dos coordenadores são:
=== SENHAS DOS ADMINISTRADORES ===
Usuário: mario | Senha: 4WgUYFJkaYpT
Usuário: bruno | Senha: 4yy5A9GYCOxg
===================================
Cabine 1:
    - Igor  : oper1-cab1
    - Tiago : oper2-cab1
    - Yuri  : oper3-cab1
  Cabine 2:
    - Juan  : oper4-cab2
    - Max   : oper5-cab2
    - Val   : oper6-cab2
  Cabine 3:
    - Amanda: oper7-cab3
    - Maria : oper8-cab3
    - Cris  : oper9-cab3
```

### Passo 3: Iniciar a Aplicação
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

⚠️ **IMPORTANTE:** Anote o IP da rede local (ex: 192.168.1.5)!

## 🌐 Acessar a Aplicação

### De ESTA máquina (Windows):
```
http://localhost:5001
ou
http://127.0.0.1:5001
```

### De OUTRA máquina na rede local:
```
http://192.168.1.5:5001
```
(Use o IP que a aplicação exibir)

### De uma VM Linux:
```bash
curl http://192.168.1.5:5001
```
(Use o IP que a aplicação exibir)

## 🔐 Credenciais de Teste Rápido

### Admin (Copie as senhas do init_db.py!)
```
Usuário: mario
Senha: [gerada aleatoriamente]
```

### Operador Padrão
```
Usuário: Igor
Senha: oper1-cab1
```

## 📚 Próximos Passos

1. **Ler documentação:**
   - `README.md` - Visão geral do projeto
   - `GUIA_DE_USO.md` - Guia completo com todos os usuários
   - `REDE_LOCAL.md` - Acessar via rede local e VMs

2. **Estudar vulnerabilidades:**
   - `LISTA_COMPLETA_4_VULNERABILIDADES.md` - Documentação técnica

3. **Realizar teste:**
   - `PLANO_DE_TESTE.md` - Plano de penetração

4. **Ver resultados:**
   - `RELATORIO_VULNERABILIDADES.md` - Relatório profissional

## ✅ Checklist de Funcionamento

- [ ] Banco de dados criado (`siga_em_frente.db` existe)
- [ ] Aplicação iniciada sem erros
- [ ] Página de login acessível em http://localhost:5001
- [ ] IP de rede local exibido (ex: 192.168.1.5)
- [ ] Login com Igor funciona
- [ ] Dashboard de operador carrega
- [ ] Mensagens aparecem (se houver)
- [ ] Botão de transferência funciona
- [ ] Dashboard admin acessível como admin
- [ ] VM/outro computador consegue acessar via IP de rede local

## 🔧 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'flask'"
```bash
pip install -r requirements.txt
```

### Erro: "Address already in use"
A porta 5001 já está em uso. Encontre e finalize o processo:
```bash
# Linux/Mac
lsof -i :5001
kill -9 <PID>

# Windows
netstat -ano | findstr :5001
taskkill /PID <PID> /F
```

### Erro: "siga_em_frente.db not found"
Execute o script de inicialização:
```bash
python init_db.py
```

### Banco de dados corrompido
```bash
rm siga_em_frente.db
python init_db.py
```

### VM Linux não consegue acessar
1. Verifique firewall do Windows:
   ```powershell
   # Abrir PowerShell como Administrador
   New-NetFirewallRule -DisplayName "Siga em Frente" `
     -Direction Inbound -Action Allow -Protocol TCP -LocalPort 5001 -Profile Private
   ```

2. Teste conectividade:
   ```bash
   # Na VM Linux
   ping 192.168.1.5
   curl -I http://192.168.1.5:5001
   ```

3. Veja mais: `REDE_LOCAL.md`

## 📁 Estrutura de Arquivos

```
siga-em-frente/
├── siga.py                               # Aplicação principal
├── models.py                            # Modelos de banco de dados
├── init_db.py                           # Script de inicialização
├── get_network_info.py                 # Script para descobrir IP local
├── requirements.txt                     # Dependências Python
├── README.md                            # Sobre o projeto
├── GUIA_DE_USO.md                      # Como usar
├── REDE_LOCAL.md                       # Acessar via rede local
├── LISTA_COMPLETA_4_VULNERABILIDADES.md # Detalhes das vulnerabilidades
├── PLANO_DE_TESTE.md                   # Plano de pentest
├── RELATORIO_VULNERABILIDADES.md       # Relatório de segurança
├── INICIO_RAPIDO.md                    # Este arquivo
├── templates/                          # Arquivos HTML
│   ├── login.html
│   ├── operator_dashboard.html
│   ├── admin_dashboard.html
│   ├── transfer.html
│   ├── transfer_success.html
│   └── files.html
├── uploads/                            # Arquivos enviados
└── siga_em_frente.db                   # Banco de dados (gerado)
```

## 🎯 Próximas Aulas

1. **IDOR Challenge:** Tente acessar dashboards de outros operadores
2. **CSRF Challenge:** Crie página para transferir fundos automaticamente
3. **XSS Challenge:** Injete JavaScript nas mensagens
4. **File Upload Challenge:** Envie arquivo além das extensões permitidas

## 🌐 Acessar de Outra Máquina

Para realizarataques de uma VM Linux ou outro computador:

1. Anote o IP exibido quando rodar `python siga.py`
2. Na VM/outro computador, acesse: `http://<IP>:5001`
3. Ou use via linha de comando:
   ```bash
   curl http://192.168.1.5:5001
   python exploit.py --target 192.168.1.5:5001
   ```

Veja `REDE_LOCAL.md` para instruções completas!

## 📞 Suporte

Para dúvidas ou problemas:
- Consulte a documentação no `GUIA_DE_USO.md`
- Veja exemplos em `LISTA_COMPLETA_4_VULNERABILIDADES.md`
- Configuração de rede: `REDE_LOCAL.md`
- Assista aos vídeos no canal AulasHack

## ⚠️ Aviso Importante

**Esta máquina contém vulnerabilidades INTENCIONAIS de segurança.**

Não use em produção! É apenas para fins educacionais.

---

**Desenvolvido por AulasHack**
**Versão:** 1.0
**Data:** Janeiro 2026
