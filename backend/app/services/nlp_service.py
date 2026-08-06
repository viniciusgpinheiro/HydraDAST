from sentence_transformers import SentenceTransformer
from models.web_input import WebInput
from models.scan_mapped_data import ScanMappedData

class NLPService:
    # Tipos de input que não representam campos de dado testáveis
    _TIPOS_IGNORADOS = {"submit", "button", "hidden", "reset", "image", "file"}

    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Modelo de NLP carregado com sucesso.")

    def _prepare_text(self, web_input: WebInput) -> str:
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
        resultados = []

        for input in scan_data.inputs:
            tipo = (input.type or "").lower()
            if tipo in self._TIPOS_IGNORADOS:
                continue

            texto = self._prepare_text(input)
            embedding = self.model.encode(texto).tolist()
            resultados.append({
                "input_original": input,
                "embedding": embedding
            })

        return resultados
