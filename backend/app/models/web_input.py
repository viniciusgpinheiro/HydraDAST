from pydantic import BaseModel
from typing import Optional

class WebInput(BaseModel):
    # Identificadores
    html_name: Optional[str] = "unknown"
    html_id: Optional[str] = "unknown"
    html_class: Optional[str] = ""
    
    # Tipo e Conteúdo
    type: str = "text"
    value: Optional[str] = ""
    placeholder: Optional[str] = ""
    label_text: Optional[str] = ""
    
    # Metadados e Dicas
    title: Optional[str] = ""
    aria_label: Optional[str] = ""
    
    # Restrições
    maxlength: Optional[str] = ""
    minlength: Optional[str] = ""
    required: bool = False
    disabled: bool = False
    
    # Hierarquia 
    parent_form_id: Optional[str] = ""
    parent_form_action: Optional[str] = ""
    parent_form_method: Optional[str] = "GET"
