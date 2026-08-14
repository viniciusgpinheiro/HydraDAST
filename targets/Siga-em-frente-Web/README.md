# Siga em Frente - Máquina de Pentest Web

## Sobre

Siga em Frente é uma aplicação web desenvolvida pela **AulasHack** para fins educacionais em testes de penetração (pentest) de aplicações web. Esta máquina foi criada especificamente para o curso de **Pentest Web** ministrado pela escola AulasHack.

A aplicação simula um sistema de gestão de pedágios de uma empresa fictícia, implementando deliberadamente **5 vulnerabilidades (incluindo Privilege Escalation) críticas de segurança web** que são comumente encontradas em aplicações reais. O objetivo é proporcionar um ambiente seguro e controlado para que os alunos aprendam a identificar, explorar e mitigar estas vulnerabilidades.

## Vulnerabilidades Implementadas

1. **IDOR (Insecure Direct Object References)** - Permite acesso não autorizado a recursos de outros usuários
2. **CSRF (Cross-Site Request Forgery)** - Permite que ações sejam executadas sem consentimento do usuário
3. **XSS (Cross-Site Scripting)** - Armazenado nas mensagens da coordenação
4. **File Upload Vulnerável** - Permite upload de arquivos maliciosos

Para detalhes completos sobre cada vulnerabilidade, consulte o arquivo `LISTA_COMPLETA_4_VULNERABILIDADES.md`.

## Requisitos do Sistema

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Navegador web moderno (Chrome, Firefox, Safari, Edge)

## Instalação

1. Clone ou baixe este repositório:
```bash
cd siga-em-frente
```

2. Crie um ambiente virtual (opcional, mas recomendado):
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Inicialize o banco de dados com os usuários e dados pré-configurados:
```bash
python init_db.py
```

## Executando a Aplicação

```bash
python app.py
```

A aplicação estará acessível em: `http://localhost:5000`

## Credenciais Padrão

Veja o arquivo `GUIA_DE_USO.md` para a lista completa de usuários e senhas.

## Estrutura do Projeto

```
siga-em-frente/
├── app.py                    # Aplicação Flask principal
├── models.py                 # Modelos do banco de dados
├── init_db.py               # Script de inicialização do banco
├── requirements.txt         # Dependências Python
├── templates/               # Templates HTML
│   ├── login.html
│   ├── operator_dashboard.html
│   ├── admin_dashboard.html
│   ├── transfer.html
│   ├── transfer_success.html
│   └── files.html
├── uploads/                 # Diretório para arquivos enviados
├── README.md                # Este arquivo
├── GUIA_DE_USO.md          # Guia completo de uso
└── LISTA_COMPLETA_4_VULNERABILIDADES.md  # Documentação das vulnerabilidades
```

## Funcionalidades da Aplicação

### Para Operadores
- autenticação de login
- visualização do dashboard da cabine
- visualização de mensagens da coordenação
- transferência de fundos entre cabines (até 60% do saldo)

### Para Administradores
- visualização do painel administrativo com estatísticas globais
- envio de mensagens para operadores
- upload de documentos

## Avisos de Segurança

**ESTA APLICAÇÃO CONTÉM VULNERABILIDADES INTENCIONAIS E NÃO DEVE SER USADA EM PRODUÇÃO!**

Esta máquina foi criada exclusivamente para fins educacionais. As vulnerabilidades implementadas são propositais e servem como alvo para aprendizado em segurança ofensiva.

## Suporte Educacional

Para dúvidas sobre as vulnerabilidades, mitigações ou para feedbacks sobre o ambiente, consulte:
- Canal AulasHack no YouTube: https://youtube.com/@aulashack
- Documentação completa: consulte `LISTA_COMPLETA_4_VULNERABILIDADES.md`

## Créditos

Máquina desenvolvida e mantida pela **AulasHack** como parte do programa educacional de segurança da informação.

## Licença

Esta máquina é fornecida gratuitamente para fins educacionais exclusivamente.
