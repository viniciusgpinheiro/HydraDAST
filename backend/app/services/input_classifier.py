# Arquivo: services/classifier.py

def classificar_campo_hibrido(cur, input_obj, embedding_vetor, tabela_nlp, threshold=0.7) -> str:
    """
    Tenta classificar usando o banco de dados (pgvector).
    Se não encontrar similaridade suficiente, usa uma heurística baseada em regras focada em DAST.
    """
    
    # ==========================================
    # 1. TENTATIVA COM INTELIGÊNCIA (PGVECTOR)
    # ==========================================
    vetor_str = "[" + ",".join(map(str, embedding_vetor)) + "]"
    
    query = f"""
        SELECT classificacao_sugerida, 
               (1 - (embedding_semantico <=> %s::vector)) as similaridade
        FROM {tabela_nlp}
        ORDER BY embedding_semantico <=> %s::vector
        LIMIT 1
    """
    
    cur.execute(query, (vetor_str, vetor_str))
    result = cur.fetchone()
    
    # Se encontrou no banco algo com similaridade maior que o threshold (ex: > 70%)
    if result and result[1] > threshold:
        return result[0]
        
    # ==========================================
    # 2. FALLBACK: HEURÍSTICA DE PENTEST (DAST)
    # ==========================================
    # Extrai todo o contexto possível para a heurística
    texto = " ".join([
        input_obj.html_name or "",
        input_obj.html_id or "",
        input_obj.label_text or "",
        input_obj.placeholder or "",
        input_obj.type or "",
        input_obj.parent_form_action or ""
    ]).lower()

    # Regras de Classificação Expandidas para o TCC:
    
    # 2.1. Credenciais e Autenticação
    if any(chave in texto for chave in ["senha", "password", "pwd", "pass"]):
        return "credencial_senha"
    if any(chave in texto for chave in ["email", "usuario", "username", "login", "user"]):
        return "credencial_identificador"
        
    # 2.2. Campos de Busca (Alvos clássicos de XSS e SQLi)
    if any(chave in texto for chave in ["busca", "search", "pesquisa", "query", "q"]):
        return "busca_pesquisa"
        
    # 2.3. Campos de Texto Longo (Alvos de Stored XSS e HTML Injection)
    if any(chave in texto for chave in ["mensagem", "message", "comentario", "comment", "descricao", "body"]):
        return "contato_mensagem"
        
    # 2.4. Vazamento ou Injeção em APIs
    if any(chave in texto for chave in ["token", "api", "key", "secret"]):
        return "segredo_api"
        
    # 2.5. Identificadores do Sistema (Alvos de IDOR / BOLA)
    if input_obj.type == "hidden" or any(chave in texto for chave in ["id", "uuid", "codigo", "code"]):
        return "identificador_oculto"

    # 2.6. Se nada der match
    return "campo_generico"