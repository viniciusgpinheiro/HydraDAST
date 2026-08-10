"""
=========================================================================
  VulnBank  —  ALVO DE TESTE PROPOSITALMENTE VULNERÁVEL (HydraDAST)
=========================================================================
  USO EXCLUSIVAMENTE LOCAL / EDUCACIONAL.
  NÃO IMPLANTE em produção nem exponha à internet.

  Vulnerabilidades plantadas (categorias de backend/app/data/arsenal_final):
    * SQL Injection  -> /login          (SQL_Injection_Master.txt, login_bypass.txt)
    * Reflected XSS  -> /buscar?q=       (XSS_Master.txt)
    * NoSQL Injection-> /api/login       (NoSQL_Master.txt)
=========================================================================
"""
import sqlite3
from flask import Flask, request, render_template_string, jsonify

app = Flask(__name__)
PORT = 5001


def get_db():
    """Banco em memória, recriado a cada request (simples e determinístico)."""
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("CREATE TABLE users (id INTEGER, username TEXT, password TEXT, saldo TEXT)")
    cur.executemany(
        "INSERT INTO users VALUES (?,?,?,?)",
        [
            (1, "admin", "S3nh@Admin!", "R$ 1.250.000,00"),
            (2, "joao", "joao123", "R$ 3.240,00"),
            (3, "maria", "maria2024", "R$ 12.800,00"),
        ],
    )
    conn.commit()
    return conn


BASE = """
<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>VulnBank</title><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
 body{background:#0d1117;color:#e6edf3;font-family:Inter,system-ui,sans-serif;margin:0}
 .top{background:#161b22;border-bottom:1px solid #30363d;padding:16px 32px;display:flex;gap:24px;align-items:center}
 .top a{color:#58a6ff;text-decoration:none;font-weight:500}
 .brand{font-weight:800;font-size:1.3rem;color:#fff}.brand span{color:#58a6ff}
 .wrap{max-width:720px;margin:40px auto;padding:0 24px}
 .card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:24px;margin-bottom:24px}
 label{display:block;margin:12px 0 6px;color:#8b949e}
 input,textarea{width:100%;box-sizing:border-box;background:#010409;border:1px solid #30363d;border-radius:8px;color:#e6edf3;padding:10px 12px}
 button{margin-top:16px;background:#58a6ff;color:#06131f;border:none;border-radius:8px;padding:10px 18px;font-weight:600;cursor:pointer}
 .warn{background:rgba(219,109,40,.12);border:1px solid rgba(219,109,40,.4);color:#db6d28;padding:10px 14px;border-radius:8px;font-size:.85rem;margin-bottom:24px}
 .res{background:#010409;border:1px solid #30363d;border-radius:8px;padding:14px;margin-top:16px}
 h1,h2{color:#fff}
</style></head><body>
<div class="top"><span class="brand">Vuln<span>Bank</span></span>
 <a href="/">Início</a><a href="/buscar">Buscar</a><a href="/login">Entrar</a></div>
<div class="wrap">
 <div class="warn">⚠️ Alvo de teste propositalmente vulnerável — apenas uso local.</div>
 {{ body|safe }}
</div></body></html>
"""


def page(body):
    return render_template_string(BASE, body=body)


@app.route("/")
def home():
    return page("""
      <h1>VulnBank</h1>
      <div class="card">
        <p>Banco de demonstração para testes de segurança do <b>HydraDAST</b>.</p>
        <ul>
          <li><a href="/login">Área do cliente</a> (login)</li>
          <li><a href="/buscar">Buscar transações</a></li>
          <li><code>POST /api/login</code> (autenticação via JSON)</li>
        </ul>
      </div>""")


@app.route("/login", methods=["GET", "POST"])
def login():
    resultado = ""
    if request.method == "POST":
        usuario = request.form.get("usuario", "")
        senha = request.form.get("senha", "")
        # VULNERÁVEL: concatenação direta na query (SQL Injection).
        # Ex.: usuario = admin'--   ou   ' OR '1'='1
        query = f"SELECT username, saldo FROM users WHERE username = '{usuario}' AND password = '{senha}'"
        conn = get_db()
        try:
            row = conn.execute(query).fetchone()
            if row:
                resultado = f'<div class="res">Bem-vindo, <b>{row[0]}</b>! Saldo: {row[1]}</div>'
            else:
                resultado = '<div class="res">Credenciais inválidas.</div>'
        except Exception as e:  # erros SQL vazam para o cliente (útil ao scanner)
            resultado = f'<div class="res">Erro SQL: {e}<br><code>{query}</code></div>'
        finally:
            conn.close()

    return page(f"""
      <h2>Área do cliente</h2>
      <div class="card">
        <form method="post" action="/login">
          <label for="usuario">Usuário</label>
          <input id="usuario" name="usuario" placeholder="admin">
          <label for="senha">Senha</label>
          <input id="senha" name="senha" type="password">
          <button type="submit">Entrar</button>
        </form>
        {resultado}
      </div>""")


@app.route("/buscar")
def buscar():
    termo = request.args.get("q", "")
    # VULNERÁVEL: reflexão sem escape (Reflected XSS).
    # Ex.: q=<script>alert(1)</script>
    reflexo = f'<div class="res">Nenhum resultado para: {termo}</div>' if termo else ""
    return page(f"""
      <h2>Buscar transações</h2>
      <div class="card">
        <form method="get" action="/buscar">
          <label for="q">Termo</label>
          <input id="q" name="q" value="{termo}" placeholder="pix, boleto, ...">
          <button type="submit">Buscar</button>
        </form>
        {reflexo}
      </div>""")


@app.route("/api/login", methods=["POST"])
def api_login():
    # VULNERÁVEL: injeção estilo NoSQL. Aceita operadores no JSON,
    # ex.: {"usuario":"admin","senha":{"$ne":null}} -> bypass de autenticação.
    data = request.get_json(silent=True) or {}
    usuario = data.get("usuario")
    senha = data.get("senha")
    conn = get_db()
    users = {r[1]: r[2] for r in conn.execute("SELECT * FROM users")}
    conn.close()

    def match(regra, valor):
        if isinstance(regra, dict):  # operadores "NoSQL"
            if "$ne" in regra:
                return valor != regra["$ne"]
            if "$gt" in regra:
                return valor > str(regra["$gt"])
            if "$regex" in regra:
                import re
                return re.search(regra["$regex"], valor) is not None
            return False
        return valor == regra

    for nome, pwd in users.items():
        if match(usuario, nome) and match(senha, pwd):
            return jsonify({"ok": True, "usuario": nome})
    return jsonify({"ok": False}), 401


if __name__ == "__main__":
    print(f" * VulnBank (ALVO VULNERÁVEL) em http://127.0.0.1:{PORT}")
    app.run(host="127.0.0.1", port=PORT, debug=False)
