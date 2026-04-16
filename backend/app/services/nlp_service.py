from sentence_transformers import SentenceTransformer
from models.web_input import WebInput
from models.scan_mapped_data import ScanMappedData

class NLPService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Modelo de NLP carregado com sucesso.")

    def _prepare_text(self, web_input: WebInput) -> str:
        '''
        Transforma o WebInput em uma string para o modelo
        '''
        dados = [
            f"name:{web_input.html_name}",
            f"id:{web_input.html_id}",
            f"label:{web_input.label_text}",
            f"placeholder:{web_input.placeholder}",
            f"type:{web_input.type}",
            f"action:{web_input.parent_form_action}"
        ]
        return " ".join([d for d in dados if "unknown" not in d and d.split(":")[1]]).lower()

    def process_page(self, scan_data: ScanMappedData):
        '''
        Recebe página inteira e gera embeddings para cada input
        '''
        resultados = []

        for input in scan_data.inputs:
            texto = self._prepare_text(input)
            embedding = self.model.encode(texto).tolist()
            resultados.append({
                "input_original": input,
                "embedding": embedding
            })

        return resultados
