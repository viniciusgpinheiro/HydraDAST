#!/usr/bin/env python3
"""
seed.py - Gerador de banco de dados para o Banco Digital Grana Fácil
Compatível com a aplicação web (granafacil_web.py) e o app mobile Android.

AulasHack - Treinamento de Pentest Mobile
AVISO: Dados fictícios gerados apenas para fins educacionais.
"""

import sqlite3
import random
import os
from datetime import datetime, timedelta

try:
    from faker import Faker
    fake = Faker('pt_BR')
except ImportError:
    print("[!] Faker não instalado. Execute: pip install faker")
    exit(1)

# Caminho do banco — relativo ao diretório do script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'banco_digital.db')

# ──────────────────────────────────────────────
# Usuários fixos
# Mantém username/password da aplicação web intactos.
# Adiciona CPF e PIN de 6 dígitos para o app mobile.
# ──────────────────────────────────────────────
USUARIOS_FIXOS = [
    {
        'username':     'admin',
        'password':     'senhaForte123!',
        'cpf':          '111.111.111-11',
        'pin':          '100101',
        'nome_completo':'Administrador do Sistema',
        'email':        'admin@granafacil.com.br',
        'saldo':        99999.99,
        'cartao_ativo': 1,
        'chave_pix':    '111.111.111-11',
        'limite_diario':500.0,
        'conta_ativa':  1
    },
    {
        'username':     'root',
        'password':     'P@ssw0rd2024!',
        'cpf':          '222.222.222-22',
        'pin':          '200202',
        'nome_completo':'Root Supervisor',
        'email':        'root@granafacil.com.br',
        'saldo':        50000.00,
        'cartao_ativo': 1,
        'chave_pix':    '222.222.222-22',
        'limite_diario':500.0,
        'conta_ativa':  1
    },
    {
        'username':     'usuario1',
        'password':     'senha123',
        'cpf':          '333.333.333-33',
        'pin':          '300303',
        'nome_completo':'João da Silva',
        'email':        'joao.silva@granafacil.com.br',
        'saldo':        1500.00,
        'cartao_ativo': 1,
        'chave_pix':    '333.333.333-33',
        'limite_diario':300.0,
        'conta_ativa':  1
    },
    {
        'username':     'maria',
        'password':     'maria2020',
        'cpf':          '444.444.444-44',
        'pin':          '400404',
        'nome_completo':'Maria Oliveira',
        'email':        'maria.oliveira@granafacil.com.br',
        'saldo':        3200.50,
        'cartao_ativo': 1,
        'chave_pix':    '444.444.444-44',
        'limite_diario':500.0,
        'conta_ativa':  1
    },
    {
        'username':     'john',
        'password':     'john456',
        'cpf':          '555.555.555-55',
        'pin':          '500505',
        'nome_completo':'John Ferreira',
        'email':        'john.ferreira@granafacil.com.br',
        'saldo':        750.00,
        'cartao_ativo': 0,
        'chave_pix':    None,
        'limite_diario':100.0,
        'conta_ativa':  1
    },
]


def gerar_cpf_formatado(usados: set) -> str:
    """Gera um CPF formatado único (sem validação matemática — massa de dados)."""
    while True:
        nums = [random.randint(0, 9) for _ in range(11)]
        cpf = '{}{}{}.{}{}{}.{}{}{}-{}{}'.format(*nums)
        if cpf not in usados:
            usados.add(cpf)
            return cpf


def criar_schema(cursor: sqlite3.Cursor) -> None:
    """Recria as tabelas do zero."""
    cursor.executescript('''
        DROP TABLE IF EXISTS transacoes;
        DROP TABLE IF EXISTS usuarios;

        CREATE TABLE usuarios (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            username       VARCHAR(80)  NOT NULL UNIQUE,
            password       VARCHAR(120) NOT NULL,
            cpf            VARCHAR(14)  NOT NULL UNIQUE,
            pin            VARCHAR(6)   NOT NULL,
            nome_completo  VARCHAR(120) NOT NULL,
            email          VARCHAR(120) NOT NULL UNIQUE,
            saldo          REAL         NOT NULL DEFAULT 0.0,
            cartao_ativo   INTEGER      NOT NULL DEFAULT 1,
            chave_pix      VARCHAR(14),
            limite_diario  REAL         NOT NULL DEFAULT 500.0,
            conta_ativa    INTEGER      NOT NULL DEFAULT 1
        );

        CREATE TABLE transacoes (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            conta_origem_id  INTEGER NOT NULL,
            conta_destino_id INTEGER NOT NULL,
            valor            REAL    NOT NULL,
            tipo             VARCHAR(20) NOT NULL,
            descricao        VARCHAR(200),
            data             DATETIME NOT NULL,
            FOREIGN KEY (conta_origem_id)  REFERENCES usuarios(id),
            FOREIGN KEY (conta_destino_id) REFERENCES usuarios(id)
        );
    ''')
    print("[+] Schema criado com sucesso")


def inserir_usuarios_fixos(cursor: sqlite3.Cursor) -> None:
    for u in USUARIOS_FIXOS:
        cursor.execute('''
            INSERT INTO usuarios
                (username, password, cpf, pin, nome_completo, email,
                 saldo, cartao_ativo, chave_pix, limite_diario, conta_ativa)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            u['username'], u['password'], u['cpf'], u['pin'],
            u['nome_completo'], u['email'], u['saldo'],
            u['cartao_ativo'], u['chave_pix'], u['limite_diario'], u['conta_ativa']
        ))
    print(f"[+] {len(USUARIOS_FIXOS)} usuários fixos inseridos")


def inserir_usuarios_faker(cursor: sqlite3.Cursor, quantidade: int = 20) -> None:
    cpfs_usados      = {u['cpf']      for u in USUARIOS_FIXOS}
    emails_usados    = {u['email']    for u in USUARIOS_FIXOS}
    usernames_usados = {u['username'] for u in USUARIOS_FIXOS}
    inseridos = 0

    while inseridos < quantidade:
        nome    = fake.name()
        partes  = nome.split()
        prim    = partes[0].lower()
        ult     = partes[-1].lower()
        sufixo  = random.randint(1, 9999)
        username = f"{prim}.{ult}{sufixo}"
        email    = f"{prim}.{ult}{sufixo}@{fake.free_email_domain()}"
        cpf      = gerar_cpf_formatado(cpfs_usados)
        pin      = str(random.randint(100000, 999999))
        saldo    = round(random.uniform(100.0, 15000.0), 2)
        cartao   = random.randint(0, 1)
        pix      = cpf if random.random() > 0.3 else None
        limite   = random.choice([50.0, 100.0, 200.0, 300.0, 500.0])
        senha_web = fake.password(length=10, special_chars=True)

        if username in usernames_usados or email in emails_usados:
            continue

        usernames_usados.add(username)
        emails_usados.add(email)

        cursor.execute('''
            INSERT INTO usuarios
                (username, password, cpf, pin, nome_completo, email,
                 saldo, cartao_ativo, chave_pix, limite_diario, conta_ativa)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            username, senha_web, cpf, pin, nome, email,
            saldo, cartao, pix, limite, 1
        ))
        inseridos += 1

    print(f"[+] {quantidade} usuários aleatórios inseridos via Faker")


def inserir_transacoes(cursor: sqlite3.Cursor, quantidade: int = 60) -> None:
    cursor.execute("SELECT id FROM usuarios")
    ids = [row[0] for row in cursor.fetchall()]

    descricoes = [
        'Pagamento de aluguel', 'Divisão de conta', 'Transferência pessoal',
        'Reembolso de despesa', 'Pagamento de serviço', 'Presente', 'Vaquinha',
        'Mensalidade', 'Pagamento de freelance', 'Empréstimo entre amigos'
    ]

    for _ in range(quantidade):
        origem  = random.choice(ids)
        destino = random.choice([i for i in ids if i != origem])
        valor   = round(random.uniform(10.0, 490.0), 2)
        tipo    = random.choice(['pix', 'transferencia'])
        desc    = random.choice(descricoes)
        data    = datetime.now() - timedelta(
            days=random.randint(0, 90),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        cursor.execute('''
            INSERT INTO transacoes
                (conta_origem_id, conta_destino_id, valor, tipo, descricao, data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (origem, destino, valor, tipo, desc,
              data.strftime('%Y-%m-%d %H:%M:%S')))

    print(f"[+] {quantidade} transações inseridas")


def run_seed() -> None:
    """Ponto de entrada principal — pode ser chamado externamente."""
    print(f"\n[*] Gerando banco em: {DB_PATH}")
    conn   = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    criar_schema(cursor)
    inserir_usuarios_fixos(cursor)
    inserir_usuarios_faker(cursor, quantidade=20)
    inserir_transacoes(cursor, quantidade=60)

    conn.commit()
    conn.close()

    print(f"\n[+] Banco '{os.path.basename(DB_PATH)}' criado com sucesso!")
    print("[+] Credenciais dos usuários fixos:")
    print(f"    {'Username':<12} {'CPF':<16} {'PIN':<8} {'Saldo':>10}")
    print(f"    {'-'*50}")
    for u in USUARIOS_FIXOS:
        print(f"    {u['username']:<12} {u['cpf']:<16} {u['pin']:<8} R${u['saldo']:>9.2f}")
    print()


if __name__ == '__main__':
    run_seed()