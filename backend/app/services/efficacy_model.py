import random

import numpy as np
import xgboost as xgb

from services.attack_categories import NOME_EXIBICAO

# Ordem fixa das categorias pra codificação one-hot — precisa ser estável
# entre treino e inferência (senão a posição de cada coluna muda de
# significado). Vem do catálogo central de categorias (item 1 do pedido).
CATEGORIAS_CONHECIDAS = sorted(NOME_EXIBICAO.keys())


def _parsear_vetor(valor) -> list[float] | None:
    """`embedding_semantico` volta do psycopg2 como string pgvector
    ("[0.1,0.2,...]") quando o adapter da extensão não está registrado, ou
    como sequência já pronta caso esteja. Aceita os dois formatos."""
    if valor is None:
        return None
    if isinstance(valor, str):
        try:
            return [float(x) for x in valor.strip("[]").split(",") if x]
        except ValueError:
            return None
    try:
        return [float(x) for x in valor]
    except TypeError:
        return None


class EfficacyModel:
    def __init__(self, epsilon=0.2):
        self.epsilon = epsilon
        self.model = xgb.XGBClassifier(objective='binary:logistic')
        self.is_trained = False

    def _extrair_features_payload(self, payload: str, categoria_ia: str, embedding_campo: list) -> np.array:
        tamanho = len(payload)
        qtd_aspa_simples = payload.count("'")
        qtd_tags_html = payload.count("<") + payload.count(">")
        tem_sql = 1 if any(word in payload.upper() for word in ["OR", "SELECT", "UNION", "--"]) else 0
        tem_script = 1 if "script" in payload.lower() else 0

        # Categoria como one-hot: o payload sozinho não diz se é um ataque
        # de LFI ou de Format String, por exemplo — a categoria escolhida
        # pelo pgvector/arsenal é o que diferencia esses casos.
        one_hot_categoria = [1.0 if categoria_ia == c else 0.0 for c in CATEGORIAS_CONHECIDAS]

        vetor_multimodal = (
            [tamanho, qtd_aspa_simples, qtd_tags_html, tem_sql, tem_script]
            + one_hot_categoria
            + list(embedding_campo)
        )
        return np.array(vetor_multimodal, dtype=float)

    def escolher_n_melhores(self, candidatos: list[dict], n: int, embedding_campo: list) -> list[dict]:
        """Escolhe até `n` dentre `candidatos` (dicts com ao menos 'payload' e
        'categoria_ia' — normalmente já pré-filtrados pelo pgvector dentre o
        bucket de categorias do motor) via epsilon-greedy sem reposição: cada
        sorteio tem `epsilon` de chance de vir de uma categoria aleatória
        (exploração) e (1-epsilon) de vir da maior eficácia prevista pelo
        XGBoost (exploração guiada pelo histórico real de sucesso/falha).

        Sem modelo treinado ainda (histórico insuficiente em `ataques`), cai
        para a ordem de entrada de `candidatos` (que já vem rankeada por
        similaridade semântica + score de RL) em vez de sorteio puramente
        aleatório — mantém a qualidade atual enquanto o XGBoost não tem dado
        suficiente pra ser confiável."""
        if n <= 0 or not candidatos:
            return []
        if not self.is_trained:
            return candidatos[:n]

        restantes = list(candidatos)
        escolhidos = []
        while restantes and len(escolhidos) < n:
            if random.random() < self.epsilon:
                idx = random.randrange(len(restantes))
            else:
                matriz = np.array([
                    self._extrair_features_payload(c["payload"], c["categoria_ia"], embedding_campo)
                    for c in restantes
                ])
                scores = self.model.predict_proba(matriz)[:, 1]
                idx = int(np.argmax(scores))
            escolhidos.append(restantes.pop(idx))
        return escolhidos

    def treinar_modelo(self, X_treino: np.array, y_treino: np.array):
        if len(X_treino) > 0:
            self.model.fit(X_treino, y_treino)
            self.is_trained = True
            print("[XGBoost] Modelo de eficácia treinado com sucesso!")

    def treinar_de_historico(self, conn, minimo_exemplos: int = 10) -> bool:
        """Treina com o histórico real da tabela `ataques` (Neon), juntando
        com o embedding do campo atacado via `componentes_web.id_componente`.
        Precisa de pelo menos `minimo_exemplos` linhas e das duas classes
        (sucesso e falha) representadas — senão não treina (`is_trained`
        continua False) e quem chama cai no fallback do pgvector/RL."""
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT a.payload_usado, a.tipo_ataque, cw.embedding_semantico, a.sucesso
                    FROM ataques a
                    JOIN componentes_web cw ON cw.id = a.id_componente
                    WHERE cw.embedding_semantico IS NOT NULL AND a.payload_usado IS NOT NULL
                    """
                )
                linhas = cur.fetchall()
        except Exception as e:  # noqa: BLE001 - treino é best-effort, nunca derruba o scan
            print(f"[EfficacyModel] Não foi possível ler o histórico de ataques: {e}")
            return False

        if len(linhas) < minimo_exemplos:
            return False

        X, y = [], []
        for payload_usado, tipo_ataque, embedding_raw, sucesso in linhas:
            embedding = _parsear_vetor(embedding_raw)
            if embedding is None:
                continue
            X.append(self._extrair_features_payload(payload_usado, tipo_ataque or "", embedding))
            y.append(1 if sucesso else 0)

        if len(set(y)) < 2:
            # XGBoost precisa de exemplos das duas classes pra ter o que aprender.
            return False

        self.treinar_modelo(np.array(X), np.array(y))
        return self.is_trained


if __name__ == "__main__":
    # Demo standalone (não roda no pipeline de scan): simula um histórico
    # onde SQLi funcionou bem em login e XSS funcionou bem em busca, e
    # mostra a IA aprendendo a diferenciar os dois contextos.
    modelo = EfficacyModel(epsilon=0.1)

    embedding_login = [-0.2] * 384
    embedding_busca = [0.1] * 384

    candidatos_treino = [
        ("' OR '1'='1", "sqli", embedding_login, 1),
        ("<script>alert(1)</script>", "xss", embedding_login, 0),
        ("<script>alert(1)</script>", "xss", embedding_busca, 1),
        ("' OR '1'='1", "sqli", embedding_busca, 0),
    ] * 5  # repete pra dar volume mínimo de treino

    X = np.array([
        modelo._extrair_features_payload(payload, categoria, emb)
        for payload, categoria, emb, _ in candidatos_treino
    ])
    y = np.array([sucesso for _, _, _, sucesso in candidatos_treino])
    modelo.treinar_modelo(X, y)

    candidatos_teste = [
        {"payload": "' OR '1'='1", "categoria_ia": "sqli"},
        {"payload": "<script>alert(1)</script>", "categoria_ia": "xss"},
        {"payload": "../../etc/passwd", "categoria_ia": "lfi_path_traversal"},
    ]

    print("\n[Resultado] Campo de LOGIN, pedindo os 2 melhores:")
    for c in modelo.escolher_n_melhores(candidatos_teste, 2, embedding_login):
        print(f"  -> {c['categoria_ia']}: {c['payload']}")

    print("\n[Resultado] Campo de BUSCA, pedindo os 2 melhores:")
    for c in modelo.escolher_n_melhores(candidatos_teste, 2, embedding_busca):
        print(f"  -> {c['categoria_ia']}: {c['payload']}")
