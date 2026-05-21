import random
import numpy as np
import xgboost as xgb

class EfficacyModel:
    def __init__(self, epsilon=0.2):
        self.epsilon = epsilon
        self.model = xgb.XGBClassifier(objective='binary:logistic')
        self.is_trained = False

    def _preparar_input_xgboost(self, features_payload: list, embedding_campo: list) -> np.array:
        #Exemplos:
        #features_payload: [12, 1, 0, 1, 0] (len: 5)
        #embedding_campo: [0.123, -0.456, ..., 0.012] (len: 384)

        # Aí junta ambos num único array linear de 389 posições
        vetor_multimodal = features_payload + embedding_campo
        return np.array(vetor_multimodal)

    def _extrair_features_payload(self, payload: str, embedding_campo: list) -> list:
        tamanho = len(payload)
        qtd_aspa_simples = payload.count("'")
        qtd_tags_html = payload.count("<") + payload.count(">")
        tem_sql = 1 if any(word in payload.upper() for word in ["OR", "SELECT", "UNION", "--"]) else 0
        tem_script = 1 if "script" in payload.lower() else 0

        return self._preparar_input_xgboost(
            features_payload=[tamanho, 
             qtd_aspa_simples, 
             qtd_tags_html, 
             tem_sql, 
             tem_script], 
             embedding_campo=embedding_campo
             )
    
    def escolher_melhor_payload(self, payloads: list, embedding_campo: list) -> str:
        # aplica epsilon-greedy
        if not self.is_trained or random.random() < self.epsilon:
            print("[Epsilon-Greedy] Escolhendo payload aleatório")
            return random.choice(payloads)
        
        print("[Epsilon-Greedy] Escolhendo payload com maior eficácia prevista")

        # escolhe o payload com maior eficácia prevista
        matriz_features = []
        for payload in payloads:
            features = self._extrair_features_payload(payload, embedding_campo)
            matriz_features.append(features)

        X_pred = np.array(matriz_features)

        previsoes = self.model.predict_proba(X_pred)
        
        scores = previsoes[:, 1]  # Probabilidade de ser eficaz (classe positiva)

        melhor = np.argmax(scores)

        return payloads[melhor]
    
    def treinar_modelo(self, X_treino: np.array, y_treino: np.array):
        if len(X_treino) > 0:
            self.model.fit(X_treino, y_treino)
            self.is_trained = True
            print("[XGBoost] Modelo de eficácia treinado com sucesso!")

if __name__ == "__main__":
    # =========================================================================
    # CONFIGURAÇÃO DO TESTE: Escolha o cenário mudando o número (1, 2 ou 3)
    # =========================================================================
    CENARIO_ATIVO = 1
    
    # Instancia a IA com Epsilon baixo (0.1) para que ela use mais o XGBoost (90%) 
    # e faça menos escolhas aleatórias, facilitando a visualização do aprendizado.
    modelo = EfficacyModel(epsilon=0.1)
    
    # Nosso arsenal de teste reduzido
    payloads_teste = [
        "' OR '1'='1",                      # SQL Injection genérico
        "<script>alert(1)</script>",         # XSS clássico
        "../../etc/passwd",                  # Path Traversal / LFI
        "normal_input_sem_ataque"            # Input limpo
    ]
    
    # Criando 2 tipos de páginas/campos falsos (Embeddings simulados)
    embedding_campo_busca = [0.1] * 384
    embedding_campo_login = [-0.2] * 384

    print(f"=== INICIANDO SIMULAÇÃO: CENÁRIO {CENARIO_ATIVO} ===")

    # -------------------------------------------------------------------------
    # CENÁRIO 1: O Especialista em SQLi (Foco em bypass de login)
    # Objetivo: Ensinar à IA que em campos de LOGIN, payloads SQL funcionam muito.
    # -------------------------------------------------------------------------
    if CENARIO_ATIVO == 1:
        print("[Config] Simulando histórico onde SQL Injection dominou o campo de Login.\n")
        
        # Extrai features combinando o payload com o contexto de login
        f_sqli = modelo._extrair_features_payload("' OR '1'='1", embedding_campo_login)
        f_xss  = modelo._extrair_features_payload("<script>alert(1)</script>", embedding_campo_login)
        f_limpo = modelo._extrair_features_payload("normal_input_sem_ataque", embedding_campo_login)
        
        X_treino = np.array([f_sqli, f_xss, f_limpo])
        y_treino = np.array([1, 0, 0])  # Apenas o SQLi teve sucesso (1)
        
        modelo.treinar_modelo(X_treino, y_treino)
        
        print("\n[Resultado] Testando 5 vezes a decisão da IA para o campo de LOGIN:")
        for i in range(5):
            escolhido = modelo.escolher_melhor_payload(payloads_teste, embedding_campo_login)
            print(f"  Tentativa {i+1}: {escolhido}")

    # -------------------------------------------------------------------------
    # CENÁRIO 2: O Caçador de XSS (Foco em campos de busca/pesquisa)
    # Objetivo: Ensinar à IA que em campos de BUSCA, payloads de script dão mais certo.
    # -------------------------------------------------------------------------
    elif CENARIO_ATIVO == 2:
        print("[Config] Simulando histórico onde Cross-Site Scripting (XSS) dominou na Busca.\n")
        
        f_sqli = modelo._extrair_features_payload("' OR '1'='1", embedding_campo_busca)
        f_xss  = modelo._extrair_features_payload("<script>alert(1)</script>", embedding_campo_busca)
        f_lfi  = modelo._extrair_features_payload("../../etc/passwd", embedding_campo_busca)
        
        X_treino = np.array([f_sqli, f_xss, f_lfi])
        y_treino = np.array([0, 1, 0])  # Apenas o XSS teve sucesso (1)
        
        modelo.treinar_modelo(X_treino, y_treino)
        
        print("\n[Resultado] Testando 5 vezes a decisão da IA para o campo de BUSCA:")
        for i in range(5):
            escolhido = modelo.escolher_melhor_payload(payloads_teste, embedding_campo_busca)
            print(f"  Tentativa {i+1}: {escolhido}")

    # -------------------------------------------------------------------------
    # CENÁRIO 3: Aprendizado em Larga Escala (O Modelo Maduro)
    # Objetivo: Simular um banco com MUITOS dados mistos (20 ataques passados).
    # A IA deve ser capaz de diferenciar o alvo: SQLi no Login e XSS na Busca.
    # -------------------------------------------------------------------------
    elif CENARIO_ATIVO == 3:
        print("[Config] Simulando Big Data: 20 registros coletados em auditorias passadas.\n")
        
        X_lista = []
        y_lista = []
        
        # Gerando dados em massa para o modelo consolidar o padrão
        for _ in range(10):
            # No login, SQLi funciona
            X_lista.append(modelo._extrair_features_payload("' OR '1'='1", embedding_campo_login))
            y_lista.append(1)
            # No login, XSS falha
            X_lista.append(modelo._extrair_features_payload("<script>alert(1)</script>", embedding_campo_login))
            y_lista.append(0)
            
            # Na busca, XSS funciona
            X_lista.append(modelo._extrair_features_payload("<script>alert(1)</script>", embedding_campo_busca))
            y_lista.append(1)
            # Na busca, SQLi falha
            X_lista.append(modelo._extrair_features_payload("' OR '1'='1", embedding_campo_busca))
            y_lista.append(0)
            
        X_treino = np.array(X_lista)
        y_treino = np.array(y_lista)
        
        modelo.treinar_modelo(X_treino, y_treino)
        
        print("\n[Resultado] Testando a flexibilidade da IA em tempo real:")
        escolha_login = modelo.escolher_melhor_payload(payloads_teste, embedding_campo_login)
        print(f"  -> Para o campo de LOGIN, a IA escolheu: {escolha_login}")
        
        escolha_busca = modelo.escolher_melhor_payload(payloads_teste, embedding_campo_busca)
        print(f"  -> Para o campo de BUSCA, a IA escolheu: {escolha_busca}")