"""
Sobe os três alvos de teste vulneráveis do HydraDAST em processos separados:

    VulnBank   -> http://127.0.0.1:5001   (SQLi, XSS, NoSQL)
    FileVault  -> http://127.0.0.1:5002   (LFI/Path Traversal, Command Injection, XXE)
    DevPortal  -> http://127.0.0.1:5003   (SSTI, SSI, LDAP)

Uso:
    python run_all.py

Ctrl+C encerra todos. USO EXCLUSIVAMENTE LOCAL — não exponha à internet.
"""
import os
import sys
import signal
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
APPS = [
    ("VulnBank", os.path.join(BASE, "vulnbank", "app.py"), 5001),
    ("FileVault", os.path.join(BASE, "filevault", "app.py"), 5002),
    ("DevPortal", os.path.join(BASE, "devportal", "app.py"), 5003),
]


def main():
    procs = []
    print("Iniciando alvos de teste (uso local)...\n")
    for nome, caminho, porta in APPS:
        p = subprocess.Popen([sys.executable, caminho], cwd=os.path.dirname(caminho))
        procs.append(p)
        print(f"  {nome:10s} -> http://127.0.0.1:{porta}")
    print("\nCtrl+C para encerrar todos.\n")

    try:
        for p in procs:
            p.wait()
    except KeyboardInterrupt:
        print("\nEncerrando...")
        for p in procs:
            try:
                p.send_signal(signal.SIGTERM)
            except Exception:
                p.kill()


if __name__ == "__main__":
    main()
