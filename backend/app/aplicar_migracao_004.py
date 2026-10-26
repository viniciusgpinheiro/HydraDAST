import os, psycopg2
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
with conn.cursor() as cur:
    cur.execute("""
        ALTER TABLE testes
            ADD COLUMN IF NOT EXISTS limite_requisicoes INTEGER;

        ALTER TABLE ataques
            ADD COLUMN IF NOT EXISTS payload_id UUID REFERENCES cache_payloads(id);

        CREATE INDEX IF NOT EXISTS idx_ataques_payload_id ON ataques(payload_id);
        CREATE INDEX IF NOT EXISTS idx_ataques_id_componente ON ataques(id_componente);
        CREATE INDEX IF NOT EXISTS idx_ataques_id_relatorio ON ataques(id_relatorio);
    """)
conn.commit()
print("Migração 004 aplicada na conexão real do backend.")

with conn.cursor() as cur:
    cur.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'ataques' AND column_name = 'payload_id'"
    )
    print("Confirmação:", cur.fetchall())
conn.close()
