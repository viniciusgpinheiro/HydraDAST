import os

def limpar_e_unificar(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Definimos os grupos de unificação (O que deve ser fundido)
    grupos = {
        "SQL_Injection_Master": ["SQLi", "SQL Injection", "Databases"],
        "Command_Injection_Master": ["Command Injection", "command-injection-commix"],
        "LFI_PathTraversal_Master": ["LFI", "Linux", "Windows", "UnixAttacks_fuzzdb", "Windows-Attacks_fuzzdb"],
        "Extensions_Master": ["extensions-Bo0oM", "file-extensions-all-cases", "file-extensions-lower-case", "file-extensions-upper-case", "file-extensions"],
        "XSS_Master": ["XSS_Modern", "URI-XSS_fuzzdb", "HTML5sec-Injections-Jhaddix"],
        "NoSQL_Master": ["NoSQL Injection", "JSON_Fuzzing"],
        "Template_Injection_Master": ["template-engines-expression", "template-engines-special-vars", "SSTI"]
    }

    arquivos_processados = set()

    for nome_final, sementes in grupos.items():
        payloads_unificados = set()
        
        for semente in sementes:
            caminho = os.path.join(input_dir, f"{semente}.txt")
            if os.path.exists(caminho):
                with open(caminho, 'r', encoding='utf-8') as f:
                    payloads_unificados.update(f.read().splitlines())
                arquivos_processados.add(f"{semente}.txt")

        if payloads_unificados:
            # Ordenação por tamanho (payloads curtos primeiro para velocidade)
            lista_final = sorted(list(payloads_unificados), key=len)
            with open(os.path.join(output_dir, f"{nome_final}.txt"), 'w', encoding='utf-8') as f:
                f.write("\n".join(lista_final))
            print(f"[✔] Criado: {nome_final}.txt ({len(lista_final)} payloads únicos)")

    # Move os arquivos que NÃO foram unificados (como Polyglots e Unicode) para a pasta final
    for arquivo in os.listdir(input_dir):
        if arquivo.endswith(".txt") and arquivo not in arquivos_processados:
            import shutil
            shutil.copy(os.path.join(input_dir, arquivo), os.path.join(output_dir, arquivo))
            print(f"[→] Mantido: {arquivo}")

# Execução
if __name__ == '__main__':
    dir_bruto = "../data/arsenal_inteligente"
    dir_limpo = "../data/arsenal_final"
    limpar_e_unificar(dir_bruto, dir_limpo)