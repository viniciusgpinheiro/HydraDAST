"""
=========================================================================
  FileVault  —  ALVO DE TESTE PROPOSITALMENTE VULNERÁVEL (HydraDAST)
=========================================================================
  USO EXCLUSIVAMENTE LOCAL / EDUCACIONAL.
  NÃO IMPLANTE em produção nem exponha à internet.

  Vulnerabilidades plantadas (categorias de backend/app/data/arsenal_final):
    * LFI / Path Traversal -> /ver?arquivo=   (LFI_PathTraversal_Master.txt)
    * Command Injection    -> /rede           (Command_Injection_Master.txt, Metacharacters_fuzzdb.txt)
    * XXE                  -> /importar        (XXE-Fuzzing.txt, XML-FUZZ.txt)
=========================================================================
"""
import os
import subprocess
from flask import Flask, request, render_template_string
from xml.dom import minidom  # noqa

app = Flask(__name__)
PORT = 5002

BASE_DIR = os.path.join(os.path.dirname(__file__), "arquivos")
os.makedirs(BASE_DIR, exist_ok=True)
# arquivos "legítimos" da aplicação
for nome, conteudo in {
    "relatorio.txt": "Relatório trimestral — receita: R$ 480.000\n",
    "notas.txt": "Lembrete: renovar certificados TLS.\n",
    "config.txt": "app=filevault\nversao=1.4.2\n",
}.items():
    p = os.path.join(BASE_DIR, nome)
    if not os.path.exists(p):
        with open(p, "w", encoding="utf-8") as f:
            f.write(conteudo)


BASE = """
<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>FileVault</title><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
 body{background:#0d1117;color:#e6edf3;font-family:Inter,system-ui,sans-serif;margin:0}
 .top{background:#161b22;border-bottom:1px solid #30363d;padding:16px 32px;display:flex;gap:24px;align-items:center}
 .top a{color:#58a6ff;text-decoration:none;font-weight:500}
 .brand{font-weight:800;font-size:1.3rem;color:#fff}.brand span{color:#3fb950}
 .wrap{max-width:760px;margin:40px auto;padding:0 24px}
 .card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:24px;margin-bottom:24px}
 label{display:block;margin:12px 0 6px;color:#8b949e}
 input,textarea{width:100%;box-sizing:border-box;background:#010409;border:1px solid #30363d;border-radius:8px;color:#e6edf3;padding:10px 12px;font-family:ui-monospace,monospace}
 button{margin-top:16px;background:#3fb950;color:#06131f;border:none;border-radius:8px;padding:10px 18px;font-weight:600;cursor:pointer}
 .warn{background:rgba(219,109,40,.12);border:1px solid rgba(219,109,40,.4);color:#db6d28;padding:10px 14px;border-radius:8px;font-size:.85rem;margin-bottom:24px}
 pre.res{background:#010409;border:1px solid #30363d;border-radius:8px;padding:14px;margin-top:16px;white-space:pre-wrap;overflow:auto}
 h1,h2{color:#fff}
</style></head><body>
<div class="top"><span class="brand">File<span>Vault</span></span>
 <a href="/">Início</a><a href="/ver?arquivo=relatorio.txt">Ver arquivo</a>
 <a href="/rede">Diagnóstico de rede</a><a href="/importar">Importar XML</a></div>
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
      <h1>FileVault</h1>
      <div class="card">
        <p>Cofre de arquivos de demonstração para testes do <b>HydraDAST</b>.</p>
        <ul>
          <li><a href="/ver?arquivo=relatorio.txt">Visualizar arquivos</a></li>
          <li><a href="/rede">Diagnóstico de rede</a></li>
          <li><a href="/importar">Importar XML</a></li>
        </ul>
      </div>""")


@app.route("/ver")
def ver():
    arquivo = request.args.get("arquivo", "")
    conteudo = ""
    if arquivo:
        # VULNERÁVEL: caminho controlado pelo usuário, sem sanitização (LFI / Path Traversal).
        # Ex.: arquivo=../../../../etc/passwd   ou   ..\\..\\windows\\win.ini
        caminho = os.path.join(BASE_DIR, arquivo)
        try:
            with open(caminho, "r", encoding="utf-8", errors="replace") as f:
                conteudo = f.read()
        except Exception as e:
            conteudo = f"[erro] {e}"
    return page(f"""
      <h2>Visualizar arquivo</h2>
      <div class="card">
        <form method="get" action="/ver">
          <label for="arquivo">Nome do arquivo</label>
          <input id="arquivo" name="arquivo" value="{arquivo}">
          <button type="submit">Abrir</button>
        </form>
        <pre class="res">{conteudo}</pre>
      </div>""")


@app.route("/rede", methods=["GET", "POST"])
def rede():
    saida = ""
    host = request.form.get("host", "") if request.method == "POST" else ""
    if host:
        # VULNERÁVEL: entrada concatenada em comando de shell (Command Injection).
        # Ex.: host=127.0.0.1 && whoami   ou   127.0.0.1 | dir
        comando = ("ping -n 1 " if os.name == "nt" else "ping -c 1 ") + host
        try:
            saida = subprocess.run(
                comando, shell=True, capture_output=True, text=True, timeout=8
            ).stdout
        except Exception as e:
            saida = f"[erro] {e}"
    return page(f"""
      <h2>Diagnóstico de rede (ping)</h2>
      <div class="card">
        <form method="post" action="/rede">
          <label for="host">Host / IP</label>
          <input id="host" name="host" value="{host}" placeholder="127.0.0.1">
          <button type="submit">Executar ping</button>
        </form>
        <pre class="res">{saida}</pre>
      </div>""")


@app.route("/importar", methods=["GET", "POST"])
def importar():
    resultado = ""
    xml = request.form.get("xml", "") if request.method == "POST" else ""
    if xml:
        # VULNERÁVEL: parser XML com entidades externas habilitadas (XXE).
        # Ex.: <!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><x>&e;</x>
        try:
            from lxml import etree
            parser = etree.XMLParser(resolve_entities=True, no_network=False, load_dtd=True)
            doc = etree.fromstring(xml.encode(), parser=parser)
            resultado = etree.tostring(doc, pretty_print=True).decode()
        except ImportError:
            # fallback sem lxml — ainda expande entidades internas
            try:
                doc = minidom.parseString(xml)
                resultado = doc.toprettyxml()
            except Exception as e:
                resultado = f"[erro] {e}"
        except Exception as e:
            resultado = f"[erro] {e}"
    exemplo = ('<?xml version="1.0"?>\n<nota><para>Olá</para></nota>')
    return page(f"""
      <h2>Importar XML</h2>
      <div class="card">
        <form method="post" action="/importar">
          <label for="xml">Documento XML</label>
          <textarea id="xml" name="xml" rows="6">{xml or exemplo}</textarea>
          <button type="submit">Importar</button>
        </form>
        <pre class="res">{resultado}</pre>
      </div>""")


if __name__ == "__main__":
    print(f" * FileVault (ALVO VULNERÁVEL) em http://127.0.0.1:{PORT}")
    app.run(host="127.0.0.1", port=PORT, debug=False)
