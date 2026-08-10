# 🎯 Alvos de Teste Vulneráveis — HydraDAST

> ⚠️ **AVISO DE SEGURANÇA**
> Estas três aplicações são **propositalmente vulneráveis** e existem apenas para
> testar o scanner HydraDAST em ambiente **local e controlado** (como DVWA, WebGoat, bWAPP).
> **Nunca** implante em produção, em rede compartilhada ou exposta à internet.
> Todas escutam somente em `127.0.0.1` por padrão.

## Sites

| Site | Porta | Vulnerabilidades plantadas | Arquivo de arsenal correspondente |
|------|-------|----------------------------|-----------------------------------|
| **VulnBank**  | 5001 | SQL Injection · Reflected XSS · NoSQL Injection | `SQL_Injection_Master.txt`, `login_bypass.txt`, `XSS_Master.txt`, `NoSQL_Master.txt` |
| **FileVault** | 5002 | LFI / Path Traversal · Command Injection · XXE  | `LFI_PathTraversal_Master.txt`, `Command_Injection_Master.txt`, `XXE-Fuzzing.txt`, `XML-FUZZ.txt` |
| **DevPortal** | 5003 | SSTI (Template Injection) · SSI Injection · LDAP Injection | `Template_Injection_Master.txt`, `SSI-Injection-Jhaddix.txt`, `LDAP_Fuzzing.txt` |

## Como rodar

```bash
cd targets
python -m venv venv
# Windows:  venv\Scripts\activate     |   Linux/Mac: source venv/bin/activate
pip install -r requirements.txt

# todos de uma vez:
python run_all.py

# ou individualmente:
python vulnbank/app.py     # http://127.0.0.1:5001
python filevault/app.py    # http://127.0.0.1:5002
python devportal/app.py    # http://127.0.0.1:5003
```

> `lxml` é opcional (habilita XXE completo no FileVault). Sem ele, há um fallback com o
> parser da biblioteca padrão.

## Endpoints e provas de conceito (para validar detecção)

### VulnBank — http://127.0.0.1:5001
- **SQL Injection** — `POST /login` (campos `usuario`, `senha`)
  - `usuario = admin'--`  → bypass de login
  - `usuario = ' OR '1'='1`
- **Reflected XSS** — `GET /buscar?q=`
  - `q=<script>alert(1)</script>`
- **NoSQL Injection** — `POST /api/login` (JSON)
  - `{"usuario":"admin","senha":{"$ne":null}}` → bypass

### FileVault — http://127.0.0.1:5002
- **LFI / Path Traversal** — `GET /ver?arquivo=`
  - `arquivo=../../../../etc/passwd` (Linux) / `arquivo=..\..\..\..\windows\win.ini` (Windows)
- **Command Injection** — `POST /rede` (campo `host`)
  - `host=127.0.0.1 && whoami` (Windows) / `host=127.0.0.1; id` (Linux)
- **XXE** — `POST /importar` (campo `xml`)
  - `<!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><x>&e;</x>`

### DevPortal — http://127.0.0.1:5003
- **SSTI** — `GET /perfil?nome=`
  - `nome={{7*7}}` → `49`
- **SSI Injection** — `GET /pagina?titulo=`
  - `titulo=<!--#exec cmd="whoami"-->`
- **LDAP Injection** — `GET /diretorio?uid=`
  - `uid=*` → lista todos os registros

## Apontando o HydraDAST para os alvos

No frontend (**Novo scan**), use uma das URLs acima em **url** e selecione os
motores desejados. Os motores/checkboxes correspondem aos arquivos de
`backend/app/data/arsenal_final` (o tipo de teste é o nome do arquivo).
