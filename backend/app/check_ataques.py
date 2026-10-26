import os, psycopg2
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
with conn.cursor() as cur:
    cur.execute("SELECT current_database(), inet_server_addr();")
    print("Banco/host real da conexão:", cur.fetchone())
    cur.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'ataques' ORDER BY ordinal_position"
    )
    print("Colunas de 'ataques' vistas por ESTA conexão:")
    for (col,) in cur.fetchall():
        print(" -", col)
conn.close()
