import random

import numpy as np
import xgboost as xgb

from services.attack_categories import NOME_EXIBICAO

# Ordem fixa das categorias pra codificação one-hot — precisa ser estável
# entre treino e inferência (senão a posição de cada coluna muda de
# significado). Vem do catálogo central de categorias (item 1 do pedido).
CATEGORIAS_CONHECIDAS = sorted(NOME_EXIBICAO.keys())


class EfficacyModel:
    def __init__(self, epsilon=0.2):
        self.epsilon = epsilon
        self.model = xgb.XGBClassifier(objective='binary:logistic')
        self.is_trained = False

    def _extrair_features_payload(
        self, payload: str, categoria_ia: str, distancia: float, score_confianca: float
    ) -> np.array:
        """7 features do payload/contexto + one-hot de categoria (16) = 23
        no total. Antes isso incluía os 384 valores do embedding bruto do
        campo — com o volume de histórico real que `ataques` ainda tem
        (dezenas a poucas centenas de linhas), 384 dimensões quase contínuas
        afogam o sinal e o XGBoost não aprende padrão nenhum (checado na
        prática: ele não diferenciava campo de login de campo de busca com
        dado perfeitamente separável). `distancia` (pgvector) e
        `score_confianca` (RL) já resumem o que o embedding diria, em 2
        números em vez de 384 — e são os mesmos sinais que o pgvector usa
        pra ordenar, então o XGBoost aprende a refinar por cima deles."""
        tamanho = len(payload)
        qtd_aspa_simples = payload.count("'")
        qtd_tags_html = payload.count("<") + payload.count(">")
        tem_sql = 1 if any(word in payload.upper() for word in ["OR", "SELECT", "UNION", "--"]) else 0
        tem_script = 1 if "script" in payload.lower() else 0

        # Categoria como one-hot: o payload sozinho não diz se é um ataque
        # de LFI ou de Format String, por exemplo — a categoria escolhida
        # pelo pgvector/arsenal é o que diferencia esses casos.
        one_hot_categoria = [1.0 if categoria_ia == c else 0.0 for c in CATEGORIAS_CONHECIDAS]

        vetor = (
            [tamanho, qtd_aspa_simples, qtd_tags_html, tem_sql, tem_script, distancia, score_confianca]
            + one_hot_categoria
        )
        return np.array(vetor, dtype=float)

    def escolher_n_melhores(self, candidatos: list[dict], n: int) -> list[dict]:
        """Escolhe até `n` dentre `candidatos` (dicts com 'payload',
        'categoria_ia', 'distancia' e 'score_confianca' — o formato que
        `FeedbackService.escolher_top_n_payloads` já devolve) via
        epsilon-greedy sem reposição: cada sorteio tem `epsilon` de chance de
        vir de uma categoria aleatória (exploração) e (1-epsilon) de vir da
        maior eficácia prevista pelo XGBoost (exploração guiada pelo
        histórico real de sucesso/falha).

        Sem modelo treinado ainda (histórico insuficiente em `ataques`), cai
        para a ordem de entrada de `candidatos` em vez de sorteio puramente
        aleatório — mantém a qualidade do ranking pgvector+RL enquanto o
        XGBoost não tem dado suficiente pra ser confiável."""
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
                    self._extrair_features_payload(
                        c["payload"], c["categoria_ia"], c["distancia"], c["score_confianca"]
                    )
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
        """Treina com o histórico real da tabela `ataques` (Neon). Recalcula
        `distancia` na hora via pgvector (`componentes_web.embedding_semantico
        <=> cache_payloads.embedding_semantico`, ligados por `ataques.
        id_componente`/`payload_id` — este último da migração 004) e pega o
        `score_confianca` atual do payload. Precisa de pelo menos
        `minimo_exemplos` linhas com as duas classes (sucesso e falha)
        representadas — senão não treina (`is_trained` continua False) e quem
        chama cai no fallback do pgvector/RL."""
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT a.payload_usado, a.tipo_ataque,
                           (cw.embedding_semantico <=> cp.embedding_semantico) AS distancia,
                           cp.score_confianca, a.sucesso
                    FROM ataques a
                    JOIN componentes_web cw ON cw.id = a.id_componente
                    JOIN cache_payloads cp ON cp.id = a.payload_id
                    WHERE cw.embedding_semantico IS NOT NULL AND cp.embedding_semantico IS NOT NULL
                    """
                )
                linhas = cur.fetchall()
        except Exception as e:  # noqa: BLE001 - treino é best-effort, nunca derruba o scan
            print(f"[EfficacyModel] Não foi possível ler o histórico de ataques: {e}")
            return False

        if len(linhas) < minimo_exemplos:
            return False

        X, y = [], []
        for payload_usado, tipo_ataque, distancia, score_confianca, sucesso in linhas:
            if distancia is None or score_confianca is None:
                continue
            X.append(self._extrair_features_payload(
                payload_usado, tipo_ataque or "", float(distancia), float(score_confianca)
            ))
            y.append(1 if sucesso else 0)

        if len(set(y)) < 2:
            # XGBoost precisa de exemplos das duas classes pra ter o que aprender.
            return False

        self.treinar_modelo(np.array(X), np.array(y))
        return self.is_trained


if __name__ == "__main__":
    # Demo standalone (não roda no pipeline de scan): simula um histórico
    # onde SQLi tem distância semântica baixa (campo de login) e score de RL
    # alto, enquanto XSS tem o oposto — e mostra a IA aprendendo a preferir
    # o payload com melhor combinação de sinais.
    modelo = EfficacyModel(epsilon=0.1)

    # (payload, categoria, distancia, score_confianca, sucesso)
    candidatos_treino = [
        ("' OR '1'='1", "sqli", 0.1, 0.8, 1),
        ("<script>alert(1)</script>", "xss", 0.6, 0.3, 0),
        ("<script>alert(1)</script>", "xss", 0.1, 0.8, 1),
        ("' OR '1'='1", "sqli", 0.6, 0.3, 0),
    ] * 5  # repete pra dar volume mínimo de treino

    X = np.array([
        modelo._extrair_features_payload(payload, categoria, distancia, score)
        for payload, categoria, distancia, score, _ in candidatos_treino
    ])
    y = np.array([sucesso for _, _, _, _, sucesso in candidatos_treino])
    modelo.treinar_modelo(X, y)

    candidatos_teste = [
        {"payload": "' OR '1'='1", "categoria_ia": "sqli", "distancia": 0.1, "score_confianca": 0.8},
        {"payload": "<script>alert(1)</script>", "categoria_ia": "xss", "distancia": 0.1, "score_confianca": 0.8},
    ]

    print("\n[Resultado] Pedindo o melhor candidato (ambos com sinais fortes):")
    for c in modelo.escolher_n_melhores(candidatos_teste, 1):
        print(f"  -> {c['categoria_ia']}: {c['payload']}")
