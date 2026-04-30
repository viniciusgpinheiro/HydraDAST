from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class WebInput(BaseModel):
    # Identificadores Básicos
    html_name: Optional[str] = "unknown"
    html_id: Optional[str] = "unknown"
    html_class: Optional[str] = ""
    
    # Tipo e Conteúdo
    type: str = "text"
    value: Optional[str] = ""
    placeholder: Optional[str] = ""
    label_text: Optional[str] = ""
    
    # Metadados e Acessibilidade (Foco em NLP)
    title: Optional[str] = ""
    aria_label: Optional[str] = ""
    aria_describedby_text: Optional[str] = ""  
    inner_text: Optional[str] = ""
    
    # Restrições
    maxlength: Optional[str] = ""
    minlength: Optional[str] = ""
    required: bool = False
    disabled: bool = False
    
    # Hierarquia e Semântica (Foco em NLP)
    parent_form_id: Optional[str] = ""
    parent_form_action: Optional[str] = ""
    parent_form_method: Optional[str] = "GET"
    fieldset_legend: Optional[str] = ""       
    
    tag_name: str = ""
    role: Optional[str] = ""
    content_context: Optional[str] = ""
    css_selector: Optional[str] = ""
    is_visible: bool = True
    
    # Dados de Validação Técnica e Segurança (Foco em Pentest)
    pattern: Optional[str] = ""
    inputmode: Optional[str] = ""
    data_attributes: Dict[str, str] = Field(default_factory=dict) 
    inline_events: List[str] = Field(default_factory=list)        
    framework_bindings: List[str] = Field(default_factory=list)   
    
    # Opções para tags <select>
    options: List[str] = Field(default_factory=list)
