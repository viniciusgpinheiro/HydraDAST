-- Migração: suporte a orçamento de requisições por teste (item 3) e
-- rastreabilidade de qual campo/payload originou cada ataque (item 4).
--
-- Rode manualmente contra o banco (psql, DBeaver, etc). Não há ORM/migração
-- automática neste projeto ainda, então este script é a fonte da verdade
-- do que precisa mudar fisicamente no schema.

-- 1) Snapshot do limite de requisições em vigor (usuarios.limite_requisicoes)
--    no momento em que o teste foi criado. Guardado por teste para que uma
--    mudança posterior na Configuração do usuário não altere retroativamente
--    o orçamento de um teste já rodado.
ALTER TABLE testes
    ADD COLUMN IF NOT EXISTS limite_requisicoes INTEGER;

-- 2) Cada linha de `ataques` passa a apontar explicitamente para o campo
--    (componentes_web) e para o payload de `cache_payloads` que a originou,
--    em vez de depender só do texto livre em `ataques.parametro`.
ALTER TABLE ataques
    ADD COLUMN IF NOT EXISTS id_campo INTEGER REFERENCES componentes_web(id),
    ADD COLUMN IF NOT EXISTS payload_id INTEGER REFERENCES cache_payloads(id);

CREATE INDEX IF NOT EXISTS idx_ataques_id_campo ON ataques(id_campo);
CREATE INDEX IF NOT EXISTS idx_ataques_payload_id ON ataques(payload_id);
