# Guia de Uso - Siga em Frente

## Introdução

Este documento fornece um guia completo sobre como utilizar a máquina de pentest "Siga em Frente". Inclui instruções de instalação, credenciais de acesso e exemplos de navegação pela aplicação.

## Instalação Rápida

### Passo 1: Preparação do Ambiente

```bash
# Criar diretório do projeto
mkdir siga-em-frente
cd siga-em-frente

# Clonar ou extrair os arquivos da máquina
# ... coloque os arquivos aqui ...

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# No Linux/Mac:
source venv/bin/activate

# No Windows:
venv\Scripts\activate
```

### Passo 2: Instalar Dependências

```bash
pip install -r requirements.txt
```

### Passo 3: Inicializar o Banco de Dados

```bash
python init_db.py
```

Este script criará automaticamente:
- 2 usuários administradores
- 9 operadores (3 por cabine)
- 3 cabines de pedágio
- Dados pré-configurados

### Passo 4: Executar a Aplicação

```bash
python siga.py
```

A aplicação estará disponível em: `http://localhost:5001`

## Credenciais de Acesso

### Usuários Administrativos

As senhas dos administradores são **geradas aleatoriamente** durante a inicialização do banco de dados. Quando você executar `python init_db.py`, as senhas serão exibidas no terminal.

**Importante:** Guarde estas senhas pois não há recuperação padrão implementada.

Exemplo de saída:
```
===================================
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

| ID | Usuário | Função | Dashboard |
|----|---------|--------|-----------|
| 101 | mario | Administrador | `/dashboard/admin?id=101` |
| 101 | bruno | Administrador | `/dashboard/admin?id=101` |

### Operadores - Cabine 1

| ID | Usuário | Senha | Cabine | Contato |
|----|---------|-------|--------|---------|
| 1 | Igor | oper1-cab1 | 1 | 11-91234-5678 |
| 2 | Tiago | oper2-cab1 | 1 | 11-92345-6789 |
| 3 | Yuri | oper3-cab1 | 1 | 11-93456-7890 |

### Operadores - Cabine 2

| ID | Usuário | Senha | Cabine | Contato |
|----|---------|-------|--------|---------|
| 4 | Juan | oper4-cab2 | 2 | 11-94567-8901 |
| 5 | Max | oper5-cab2 | 2 | 11-95678-9012 |
| 6 | Val | oper6-cab2 | 2 | 11-96789-0123 |

### Operadores - Cabine 3

| ID | Usuário | Senha | Cabine | Contato |
|----|---------|-------|--------|---------|
| 7 | Amanda | oper7-cab3 | 3 | 11-97890-1234 |
| 8 | Maria | oper8-cab3 | 3 | 11-98901-2345 |
| 9 | Cris | oper9-cab3 | 3 | 11-99012-3456 |

## Navegação da Aplicação

### Tela de Login

Ao acessar `http://localhost:5001`, você será redirecionado para a tela de login.

**Campos:**
- Usuário: nome de login do usuário
- Senha: senha do usuário

**Exemplo:** Login como Igor (operador da Cabine 1)
```
Usuário: Igor
Senha: oper1-cab1
```

### Dashboard do Operador

Após fazer login, o operador é redirecionado para seu dashboard (`/dashboard/operator?id=<numero-do-operador>`).

**Elementos do Dashboard:**
- **Boas-vindas:** Mensagem personalizada com o nome do operador
- **Estatísticas:** Quantidade de veículos e valor em caixa da cabine
- **Mensagens da Coordenação:** Mensagens enviadas pelos administradores
- **Botão de Transferência:** Link para a página de transferência de fundos

### Dashboard do Administrador

Após fazer login como administrador, você é redirecionado para (`/dashboard/admin?id=101`).

**Elementos do Dashboard:**
- **Estatísticas Globais:** Total de veículos e valor em caixa de todas as cabines
- **Envio de Mensagens:** Formulário para enviar mensagens a operadores específicos
- **Upload de Documentos:** Formulário para fazer upload de arquivos (com validação fraca)
- **Tabela de Operadores:** Lista completa com nomes, usuários, cabines e contatos

### Página de Transferência

Acessada pelo operador a partir do botão "Transferência de Fundos" no dashboard.

**Campos:**
- **Valor de transferência:** Montante a transferir (limitado a 60% do saldo)
- **Número da cabine de destino:** Cabine receptora
- **Botão Transferir:** Executa a transferência
- **Botão Voltar ao Dashboard:** Retorna ao dashboard

**Exemplo:** Igor (Cabine 1) com saldo de R$ 2850,50 pode transferir até R$ 1710,30.

## Funcionalidades Detalhadas

### Visualizar Mensagens

As mensagens são carregadas dinamicamente via JavaScript e exibem:
- Nome do remetente (administrador)
- Conteúdo da mensagem
- Data e hora de envio

### Enviar Mensagem (Admin)

1. Acesse o dashboard administrativo
2. No painel "Enviar Mensagem para Operador"
3. Selecione o operador na lista suspensa
4. Digite a mensagem no campo de texto
5. Clique em "Enviar Mensagem"

### Fazer Upload de Arquivo (Admin)

1. Acesse o dashboard administrativo
2. No painel "Upload de Documentos"
3. Selecione um arquivo com extensão permitida (.docx, .pdf, .eml, .msg)
4. Clique em "Enviar"

Os arquivos são salvos na pasta `uploads/` da aplicação.

### Realizar Transferência (Operador)

1. Acesse o dashboard do operador
2. Clique em "Transferência de Fundos"
3. Digite o valor a transferir
4. Selecione a cabine de destino
5. Clique em "Transferir"

Uma confirmação será exibida com detalhes da transferência.

## Dados Pré-configurados

Ao inicializar o banco de dados, os seguintes dados são criados:

### Cabines

| ID | Número | Veículos | Saldo | Chave PIX |
|----|--------|----------|-------|-----------|
| 1 | 1 | 145 | R$ 2.850,50 | cabine1@sigaemfrente.com.br |
| 2 | 2 | 132 | R$ 2.640,75 | cabine2@sigaemfrente.com.br |
| 3 | 3 | 156 | R$ 3.120,25 | cabine3@sigaemfrente.com.br |

## Resetar a Aplicação

Para resetar completamente a aplicação (apagar banco de dados e criar novo):

```bash
# Deletar banco antigo
rm siga_em_frente.db

# Recriar banco
python init_db.py

# Reiniciar aplicação
python siga.py
```

## Troubleshooting

### A aplicação não inicia

**Erro:** `ModuleNotFoundError: No module named 'flask'`

**Solução:** Instale as dependências novamente
```bash
pip install -r requirements.txt
```

### Porta 5001 já está em uso

**Erro:** `Address already in use`

**Solução:** Altere a porta no arquivo `siga.py` ou finalize o processo que usa a porta 5001.

### Banco de dados corrompido

**Solução:** Delete o arquivo `siga_em_frente.db` e execute `python init_db.py` novamente.

### Erro de autenticação

Verifique se o usuário existe na tabela de credenciais acima. Senhas são **case-sensitive** (diferenciam maiúsculas de minúsculas).

## Documentação Adicional

Para informações sobre as vulnerabilidades implementadas e como explorá-las:
- Consulte: `LISTA_COMPLETA_4_VULNERABILIDADES.md`

Para informações técnicas sobre a aplicação:
- Consulte: `README.md`

## Suporte e Dúvidas

Esta máquina foi desenvolvida pela **AulasHack** para fins educacionais.

Para feedbacks, sugestões ou reportar problemas, entre em contato através do canal AulasHack no YouTube.

---

**Última atualização:** Janeiro 2026
**Detentora intelectual:** AulasHack - Escola de Segurança da Informação
