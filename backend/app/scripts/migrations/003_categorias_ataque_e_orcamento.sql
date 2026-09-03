-- Migração: suporte às novas categorias de ataque (item 1 do pedido) e ao
-- orçamento "n melhores ataques por campo" derivado do limite de
-- requisições do usuário (itens 2 e 3).
--
-- Rode manualmente contra o banco (psql, DBeaver, etc), como a 002. Não há
-- ORM/migração automática neste projeto ainda.

-- 1) Cada payload de cache_payloads passa a declarar em qual ponto da
--    requisição ele deve ser injetado. A categoria sozinha não diz isso: um
--    payload de LFI/Format String costuma ir em query string, um de Command
--    Injection/SSTI/XXE costuma ir no body do formulário, etc.
--    Valores esperados pela aplicação: 'body', 'query', 'header', 'cookie', 'method'.
ALTER TABLE cache_payloads
    ADD COLUMN IF NOT EXISTS ponto_injecao TEXT NOT NULL DEFAULT 'body';

-- 2) Snapshot do orçamento calculado para o teste: quantas rotas distintas
--    foram encontradas na página e quantos ataques por rota (n =
--    limite_requisicoes / numero_rotas_detectadas) isso liberou. Fica ao
--    lado de testes.limite_requisicoes (migração 002) para auditoria — uma
--    mudança posterior no limite não altera retroativamente o orçamento de
--    um teste já rodado.
ALTER TABLE testes
    ADD COLUMN IF NOT EXISTS numero_rotas_detectadas INTEGER,
    ADD COLUMN IF NOT EXISTS orcamento_por_rota INTEGER;

-- 3) cache_payloads.tipo_ataque continua texto livre (sem CHECK/enum, para
--    não travar linhas já existentes nem exigir migração de dados). Os
--    novos valores usados pela aplicação a partir de agora são:
--    'sqli', 'nosqli', 'command_injection', 'lfi_path_traversal',
--    'upload_extension', 'xxe', 'ssti', 'ldap_injection', 'ssi_injection',
--    'format_string', 'java_deserialization', 'fuzzing_generico', 'xss'
--    (além das 3 categorias antigas: 'credencial_senha',
--    'credencial_identificador', 'campo_generico').
--
-- Depois de rodar esta migração, rode nesta ordem:
--   1. backend/app/scripts/seed_arsenal_payloads.py       (popula as novas categorias)
--   2. backend/app/scripts/populate_cache_payloads_embeddings.py  (gera embeddings de tudo)
