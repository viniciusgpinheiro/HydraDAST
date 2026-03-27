import asyncio
from playwright.async_api import async_playwright
from pydantic import BaseModel
from typing import List
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
    inner_text: Optional[str] = ""
    
    # Restrições
    maxlength: Optional[str] = ""
    minlength: Optional[str] = ""
    required: bool = False
    disabled: bool = False
    
    # Hierarquia 
    parent_form_id: Optional[str] = ""
    parent_form_action: Optional[str] = ""
    parent_form_method: Optional[str] = "GET"
    
    tag_name: str = ""
    role: Optional[str] = ""
    content_context: Optional[str] = ""  # Texto ao redor (vizinhos)
    css_selector: Optional[str] = ""    # Para a IA saber "onde" agir
    is_visible: bool = True
    # Dados de validação técnica (essencial para IA de segurança)
    pattern: Optional[str] = ""
    inputmode: Optional[str] = ""


class ScanMappedData(BaseModel):
    url: str
    inputs: List[WebInput]


async def run_smart_crawler(target_url: str) -> ScanMappedData:
    async with async_playwright() as p:
        # Acesso Headless: Chromium sem interface gráfica
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(f"[*] Iniciando mapeamento em: {target_url}")
        
        # Navega e espera o JS carregar (essencial para o Juice Shop)
        await page.goto(target_url, wait_until="networkidle")

        # Busca todos os inputs, selects e textareas
        found_elements = await page.query_selector_all("input, select, textarea")
        inputs_list = []

        for el in found_elements:
            # 1. Identificadores Básicos
            name = await el.get_attribute("name") or ""
            id_attr = await el.get_attribute("id") or ""
            class_attr = await el.get_attribute("class") or ""

            # 2. Tipo e Valor
            input_type = await el.get_attribute("type") or ""
            input_value = await el.get_attribute("value") or ""
            placeholder = await el.get_attribute("placeholder") or ""
            label_text = ""
            if id_attr:
                # Busca direta no elemento (mais rápido que page.query_selector se possível)
                label_el = await page.query_selector(f"label[for='{id_attr}']")
                if label_el:
                    label_text = await label_el.inner_text()
            
            # Se não achou label por ID, verifica se o elemento está dentro de um label (Label Encapsulado)
            if not label_text:
                # Avalia se o pai é um label
                label_text = await el.evaluate("""(node) => {
                    const label = node.closest('label');
                    return label ? label.innerText : '';
                }""")
            
            # 3. Metadados de Acessibilidade (Crucial para LLMs)
            title = await el.get_attribute("title") or ""
            aria_label = await el.get_attribute("aria-label") or "" # Corrigido hífen
            role = await el.get_attribute("role") or "" # Define a função do elemento (ex: button, tab)
            inner_text = (await el.inner_text()).strip() or ""

            # 4. Restricoes
            max_length = await el.get_attribute("maxlength") or ""
            min_length = await el.get_attribute("minlength") or ""
            is_required = await el.evaluate("el => el.required") 
            is_disabled = await el.is_disabled()

            # 5. Hierarquia (Buscando o formulário pai)
            parent_form_data = await el.evaluate("""(node) => {
                const form = node.closest('form');
                if (!form) return null;
                
                return {
                    id: form.id || "",
                    action: form.getAttribute('action') || "",
                    method: form.getAttribute('method') || "GET"
                };
            }""")

            if parent_form_data:
                parent_form_id = parent_form_data["id"]
                parent_form_action = parent_form_data["action"]
                parent_form_method = parent_form_data["method"].upper()
            else:
                # Caso o elemento esteja solto na página (comum em SPAs modernas)
                parent_form_id = ""
                parent_form_action = ""
                parent_form_method = "GET"

            # 1. Metadados Técnicos e Acessibilidade (Cruciais para IA de Segurança)
            tag_name = await el.evaluate("node => node.tagName.toLowerCase()")
            pattern = await el.get_attribute("pattern") or ""
            input_mode = await el.get_attribute("inputmode") or ""
            is_visible = await el.is_visible()

            # 2. Gerador de Seletor CSS (Para a IA saber onde clicar/atuar)
            css_selector = await el.evaluate(r"""(node) => {
                if (node.id) return `#${node.id}`;
                if (node.name) return `[name="${node.name}"]`;
                let selector = node.tagName.toLowerCase();
                if (node.className) {
                    selector += "." + node.className.trim().split(/\s+/).join('.');
                }
                return selector;
            }""")

            # 3. Captura de Contexto de Vizinhança (O "combustível" para o seu NLP)
            # Pega o texto dos elementos ao redor para definir o propósito do campo
            content_context = await el.evaluate("""(node) => {
                const parent = node.parentElement;
                const prevText = node.previousElementSibling ? node.previousElementSibling.innerText.trim() : "";
                const nextText = node.nextElementSibling ? node.nextElementSibling.innerText.trim() : "";
                const pText = parent ? parent.innerText.split('\\n')[0].trim() : ""; // Pega a primeira linha do pai
                
                return `${prevText} | ${nextText} | context: ${pText}`.replace(/\\s+/g, ' ').substring(0, 160);
            }""")

            # 4. Captura de Opções (Apenas se for um SELECT)
            options = []
            if tag_name == "select":
                options = await el.evaluate("""(node) => 
                    Array.from(node.options).map(opt => opt.text.trim()).filter(t => t !== "")
                """)

            # Cria o objeto Pydantic (Validação automática)
            input_data = WebInput(
                tag_name=tag_name,
                html_name=name,
                html_id=id_attr,
                html_class=class_attr,
                type=input_type,
                value=input_value,
                placeholder=placeholder,
                label_text=label_text,
                content_context=content_context,
                role=role,
                css_selector=css_selector,
                pattern=pattern,
                inputmode=input_mode,
                is_visible=is_visible,
                maxlength=max_length,
                minlength=min_length,
                required=is_required,
                disabled=is_disabled,
                parent_form_id=parent_form_id,
                parent_form_action=parent_form_action,
                parent_form_method=parent_form_method
            )
            inputs_list.append(input_data)

        await browser.close()
        
        return ScanMappedData(url=target_url, inputs=inputs_list)

# Exemplo de execução (Para testar contra o seu Juice Shop no Docker)
if __name__ == "__main__":
    url_vulneravel = "https://the-internet.herokuapp.com/login"
    url_vulneravel = "https://leanpub.com/juice-shop"
    resultado = asyncio.run(run_smart_crawler(url_vulneravel))
print(resultado.model_dump_json(indent=2))