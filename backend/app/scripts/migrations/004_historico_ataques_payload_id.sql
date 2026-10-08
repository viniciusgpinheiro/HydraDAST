-- Migração: completa o schema real confirmado no Neon (todas as PKs são
-- uuid) para suportar a persistência real do histórico de ataques e o
-- treino do EfficacyModel (XGBoost).
--
-- Substitui a parte da migração 002 que nunca chegou a ser aplicada nesse
-- banco (ataques.id_campo/payload_id como INTEGER — tipo errado, a tabela
-- já usa uuid em tudo e já tem id_componente fazendo esse papel). Rode
-- manualmente (psql, DBeaver, Neon SQL editor), como as anteriores.

-- 1) Snapshot do limite de requisições em vigor no momento em que o teste
--    foi criado (a parte da migração 002 que fazia sentido, só que nunca
--    tinha sido aplicada de fato neste banco).
ALTER TABLE testes
    ADD COLUMN IF NOT EXISTS limite_requisicoes INTEGER;

-- 2) Liga cada ataque ao payload exato de cache_payloads que o originou.
--    Hoje `ataques` só guarda tipo_ataque/payload_usado como texto solto;
--    isso é só uma conveniência pra consultas de treino do XGBoost não
--    dependerem de comparar texto (cache_payloads.payload já é UNIQUE, mas
--    um id evita ambiguidade se o texto mudar/for removido depois).
ALTER TABLE ataques
    ADD COLUMN IF NOT EXISTS payload_id UUID REFERENCES cache_payloads(id);

CREATE INDEX IF NOT EXISTS idx_ataques_payload_id ON ataques(payload_id);
CREATE INDEX IF NOT EXISTS idx_ataques_id_componente ON ataques(id_componente);
CREATE INDEX IF NOT EXISTS idx_ataques_id_relatorio ON ataques(id_relatorio);
