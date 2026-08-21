"""
=========================================================================
  DevPortal  —  ALVO DE TESTE PROPOSITALMENTE VULNERÁVEL (HydraDAST)
=========================================================================
  USO EXCLUSIVAMENTE LOCAL / EDUCACIONAL.
  NÃO IMPLANTE em produção nem exponha à internet.

  Vulnerabilidades plantadas (categorias de backend/app/data/arsenal_final):
    * SSTI (Server-Side Template Injection) -> /perfil?nome=  (Template_Injection_Master.txt)
    * SSI Injection                        -> /pagina?titulo= (SSI-Injection-Jhaddix.txt)
    * LDAP Injection                       -> /diretorio?uid= (LDAP_Fuzzing.txt)
=========================================================================
"""
import os
import re
import subprocess
from flask import Flask, request, render_template_string
# possivel erro

app = Flask(__name__)
PORT = 5003

# "diretório" corporativo simulado (para a busca LDAP)
DIRETORIO = [
    {"uid": "admin", "nome": "Administrador", "setor": "TI", "email": "admin@devportal.local"},
    {"uid": "jsilva", "nome": "João Silva", "setor": "Engenharia", "email": "jsilva@devportal.local"},
    {"uid": "msouza", "nome": "Maria Souza", "setor": "Financeiro", "email": "msouza@devportal.local"},
]

BASE = """
<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>DevPortal</title><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
 body{background:#0d1117;color:#e6edf3;font-family:Inter,system-ui,sans-serif;margin:0}
 .top{background:#161b22;border-bottom:1px solid #30363d;padding:16px 32px;display:flex;gap:24px;align-items:center}
 .top a{color:#a371f7;text-decoration:none;font-weight:500}
 .brand{font-weight:800;font-size:1.3rem;color:#fff}.brand span{color:#a371f7}
 .wrap{max-width:760px;margin:40px auto;padding:0 24px}
 .card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:24px;margin-bottom:24px}
 label{display:block;margin:12px 0 6px;color:#8b949e}
 input{width:100%;box-sizing:border-box;background:#010409;border:1px solid #30363d;border-radius:8px;color:#e6edf3;padding:10px 12px}
 button{margin-top:16px;background:#a371f7;color:#0d1117;border:none;border-radius:8px;padding:10px 18px;font-weight:600;cursor:pointer}
 .warn{background:rgba(219,109,40,.12);border:1px solid rgba(219,109,40,.4);color:#db6d28;padding:10px 14px;border-radius:8px;font-size:.85rem;margin-bottom:24px}
 pre.res,.res{background:#010409;border:1px solid #30363d;border-radius:8px;padding:14px;margin-top:16px;white-space:pre-wrap;overflow:auto}
 table{width:100%;border-collapse:collapse;margin-top:16px}
 th,td{border:1px solid #30363d;padding:8px 10px;text-align:left}th{color:#8b949e}
 h1,h2{color:#fff}
</style></head><body>
<div class="top"><span class="brand">Dev<span>Portal</span></span>
 <a href="/">Início</a><a href="/perfil?nome=dev">Perfil</a>
 <a href="/pagina?titulo=Bem-vindo">Página</a><a href="/diretorio">Diretório</a></div>
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
      <h1>DevPortal</h1>
      <div class="card">
        <p>Portal de desenvolvedores de demonstração para testes do <b>HydraDAST</b>.</p>
        <ul>
          <li><a href="/perfil?nome=dev">Saudação de perfil</a></li>
          <li><a href="/pagina?titulo=Bem-vindo">Renderizar página</a></li>
          <li><a href="/diretorio">Buscar no diretório</a></li>
        </ul>
      </div>""")


@app.route("/perfil")
def perfil():
    nome = request.args.get("nome", "dev")
    # VULNERÁVEL: entrada do usuário concatenada no template Jinja2 (SSTI).
    # Ex.: nome={{7*7}}  ->  49    |    nome={{config}}
    template = (
        "<h2>Perfil</h2><div class='card'>"
        "<form method='get' action='/perfil'>"
        "<label for='nome'>Nome de exibição</label>"
        "<input id='nome' name='nome' value='" + nome + "'>"
        "<button type='submit'>Atualizar</button></form>"
        "<div class='res'>Olá, " + nome + "! Bem-vindo(a) de volta.</div>"
        "</div>"
    )
    try:
        corpo = render_template_string(template)
    except Exception as e:
        corpo = f"<div class='res'>[erro de template] {e}</div>"
    return page(corpo)


def processar_ssi(texto):
    """Processador SSI ingênuo e VULNERÁVEL (SSI Injection).
    Suporta <!--#echo var="X"--> e <!--#exec cmd="X"-->."""
    def echo(m):
        return {"DATE_LOCAL": "hoje", "DOCUMENT_NAME": "pagina"}.get(m.group(1), "")

    def execc(m):
        try:
            return subprocess.run(m.group(1), shell=True, capture_output=True,
                                  text=True, timeout=8).stdout
        except Exception as e:
            return f"[erro] {e}"

    texto = re.sub(r'<!--#echo\s+var="([^"]*)"\s*-->', echo, texto)
    texto = re.sub(r'<!--#exec\s+cmd="([^"]*)"\s*-->', execc, texto)
    return texto


@app.route("/pagina")
def pagina():
    titulo = request.args.get("titulo", "Bem-vindo")
    # VULNERÁVEL: conteúdo do usuário passa por diretivas SSI (SSI Injection).
    # Ex.: titulo=<!--#exec cmd="whoami"-->
    corpo_ssi = processar_ssi(f"<h2>{titulo}</h2><p>Página gerada dinamicamente.</p>")
    return page(f"""
      <div class="card">
        <form method="get" action="/pagina">
          <label for="titulo">Título da página</label>
          <input id="titulo" name="titulo" value="{titulo}">
          <button type="submit">Gerar</button>
        </form>
        <div class="res">{corpo_ssi}</div>
      </div>""")


@app.route("/diretorio")
def diretorio():
    uid = request.args.get("uid", "")
    linhas = ""
    if uid:
        # VULNERÁVEL: filtro LDAP montado por concatenação (LDAP Injection).
        # Ex.: uid=*   ->  retorna todos    |    uid=*)(uid=*
        ldap_filter = f"(uid={uid})"
        # avaliação simplificada e permissiva do filtro (imita servidor vulnerável)
        alvo = uid.replace("*", "").replace(")(", "").replace("(", "").replace(")", "")
        curinga = "*" in uid or ")(" in uid
        encontrados = [
            e for e in DIRETORIO
            if curinga or (alvo and alvo.lower() in e["uid"].lower()) or alvo == ""
        ]
        rows = "".join(
            f"<tr><td>{e['uid']}</td><td>{e['nome']}</td><td>{e['setor']}</td><td>{e['email']}</td></tr>"
            for e in encontrados
        )
        linhas = (
            f"<div class='res'>filtro: <code>{ldap_filter}</code></div>"
            f"<table><tr><th>uid</th><th>nome</th><th>setor</th><th>email</th></tr>{rows}</table>"
        )
    return page(f"""
      <h2>Diretório corporativo</h2>
      <div class="card">
        <form method="get" action="/diretorio">
          <label for="uid">Buscar por uid</label>
          <input id="uid" name="uid" value="{uid}" placeholder="jsilva">
          <button type="submit">Buscar</button>
        </form>
        {linhas}
      </div>""")


if __name__ == "__main__":
    print(f" * DevPortal (ALVO VULNERÁVEL) em http://127.0.0.1:{PORT}")
    app.run(host="127.0.0.1", port=PORT, debug=False)
