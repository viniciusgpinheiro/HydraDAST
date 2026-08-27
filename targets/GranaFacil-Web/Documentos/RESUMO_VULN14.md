# VULN-14: Armazenamento Inseguro de Credenciais Críticas

## 🔴 VULNERABILIDADE CRÍTICA

**VulnID:** VULN-14  
**Severidade:** CRÍTICA  
**CVSS 3.1:** 9.0  
**Vector:** CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:H  
**CWE:** CWE-522, CWE-798  
**OWASP:** A02:2021 - Cryptographic Failures  
**Ativo:** Página /admin1 - Conteúdo HTML

---

## 📝 RESUMO

Credenciais críticas de infraestrutura estão **hard-coded em texto claro** dentro do HTML da página `/admin1`, incluindo:
- Credenciais de servidor (sysadmin)
- Credenciais de banco de dados (db_admin)  
- API Keys de produção
- Credenciais de VPN corporativa

**INDEPENDENTE da VULN-05:** Mesmo corrigindo a autenticação da página, as credenciais continuariam expostas de forma insegura!

---

## 💥 IMPACTO

- Comprometimento total da infraestrutura
- Acesso ao banco de dados de produção
- Uso indevido de API Keys (cobranças)
- Acesso à VPN (movimentação lateral)
- Violação de compliance (PCI-DSS, SOC 2, ISO 27001)

---

## 🔧 REMEDIAÇÃO

### IMEDIATO (Hoje):
1. ✅ **ROTACIONAR** todas as credenciais expostas
2. ✅ **REMOVER** conteúdo da página /admin1
3. ✅ **AUDITAR** logs de acesso

### PERMANENTE:
✅ Implementar **Secrets Management**:
- HashiCorp Vault
- AWS Secrets Manager
- Azure Key Vault
- CyberArk

✅ **NUNCA** armazenar credenciais em:
- Código-fonte
- Páginas web
- Arquivos de configuração
- Documentação
- Planilhas

---

## 📚 REFERÊNCIAS

1. OWASP Secrets Management Cheat Sheet
2. CWE-522: Insufficiently Protected Credentials
3. CWE-798: Use of Hard-coded Credentials
4. HashiCorp Vault Documentation

---

**Total de vulnerabilidades agora: 14 (4 Críticas, 3 Altas, 6 Médias, 1 Baixa)**
