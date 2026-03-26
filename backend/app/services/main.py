from models.WebInput import WebInput
from models.ScanMappedData import ScanMappedData
from services.nlp_service import NLPService

'''
APENAS TESTE
'''

dados_mapeados = ScanMappedData(
    url="https://exemplo.com/login",
    inputs=[
        WebInput(html_name="user", label_text="Usuário", type="text"),
        WebInput(html_name="pass", label_text="Senha", type="password")
    ]
)

# Seu serviço processando
nlp = NLPService()
lista_com_vetores = nlp.processar_pagina_completa(dados_mapeados)

for res in lista_com_vetores:
    print(f"Campo: {res['input_original'].html_name} -> Vetor de {len(res['embedding'])} posições.")