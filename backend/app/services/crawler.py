import asyncio
from playwright.async_api import async_playwright
from models.web_input import WebInput
from models.scan_mapped_data import ScanMappedData


async def run_smart_crawler(target_url: str) -> ScanMappedData:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print(f"[*] Iniciando mapeamento avançado em: {target_url}")
        
        try:
            await page.goto(target_url, timeout=30000)
        except Exception as e:
            print(f"[!] Aviso durante o carregamento da página: {e}")

        found_elements = await page.query_selector_all("input, select, textarea, button")
        inputs_list = []

        for el in found_elements:
            # 1. Identificadores Básicos
            name = await el.get_attribute("name") or ""
            id_attr = await el.get_attribute("id") or ""
            class_attr = await el.get_attribute("class") or ""
            input_type = await el.get_attribute("type") or ""
            input_value = await el.get_attribute("value") or ""
            placeholder = await el.get_attribute("placeholder") or ""
            
            # 2. Labels e Acessibilidade
            label_text = ""
            if id_attr:
                label_el = await page.query_selector(f"label[for='{id_attr}']")
                if label_el:
                    label_text = await label_el.inner_text()
            
            if not label_text:
                label_text = await el.evaluate("""(node) => {
                    const label = node.closest('label');
                    return label ? label.innerText : '';
                }""")
                
            title = await el.get_attribute("title") or ""
            aria_label = await el.get_attribute("aria-label") or "" 
            role = await el.get_attribute("role") or ""
            inner_text = (await el.inner_text()).strip() or ""
            
            # NOVO: Captura do texto de aria-describedby (dicas de senha, mensagens de erro)
            aria_describedby_id = await el.get_attribute("aria-describedby") or ""
            aria_describedby_text = ""
            if aria_describedby_id:
                aria_describedby_text = await page.evaluate(f"""() => {{
                    const ids = "{aria_describedby_id}".split(' ');
                    let text = '';
                    for (let id of ids) {{
                        if (!id) continue;
                        const descEl = document.getElementById(id);
                        if (descEl) text += descEl.innerText.trim() + ' ';
                    }}
                    return text.trim();
                }}""")

            # 3. Restrições
            max_length = await el.get_attribute("maxlength") or ""
            min_length = await el.get_attribute("minlength") or ""
            is_required = await el.evaluate("el => Boolean(el.required)")
            is_disabled = await el.is_disabled()

            # 4. Hierarquia (Formulário e Fieldset)
            parent_form_data = await el.evaluate("""(node) => {
                const form = node.closest('form');
                const fieldset = node.closest('fieldset');
                let legendText = "";
                
                if (fieldset) {
                    const legend = fieldset.querySelector('legend');
                    if (legend) legendText = legend.innerText.trim();
                }
                
                return {
                    form_id: form ? (form.id || "") : "",
                    form_action: form ? (form.getAttribute('action') || "") : "",
                    form_method: form ? (form.getAttribute('method') || "GET") : "GET",
                    fieldset_legend: legendText
                };
            }""")

            # 5. Metadados Técnicos
            tag_name = await el.evaluate("node => node.tagName.toLowerCase()")
            pattern = await el.get_attribute("pattern") or ""
            input_mode = await el.get_attribute("inputmode") or ""
            is_visible = await el.is_visible()

            # 6. NOVO: Captura Massiva de Atributos (Segurança/Pentest)
            # Otimizado para pegar data-*, on* e frameworks em uma única passagem
            advanced_attrs = await el.evaluate("""(node) => {
                let data_attrs = {};
                let inline_events = [];
                let frameworks = [];
                
                for (let attr of node.attributes) {
                    const name = attr.name.toLowerCase();
                    const value = attr.value;
                    
                    // Captura data-* attributes
                    if (name.startsWith('data-')) {
                        data_attrs[name] = value;
                    }
                    // Captura eventos inline (onclick, onchange, etc)
                    if (name.startsWith('on')) {
                        inline_events.push(`${name}=${value}`);
                    }
                    // Captura diretivas de frameworks (Angular, Vue, Livewire, Alpine)
                    if (name.startsWith('ng-') || name.startsWith('v-') || 
                        name.startsWith('wire:') || name.startsWith('x-') || 
                        name === 'data-bind') {
                        frameworks.push(`${name}=${value}`);
                    }
                }
                return { data_attrs, inline_events, frameworks };
            }""")

            # 7. Gerador de Seletor CSS
            css_selector = await el.evaluate(r"""(node) => {
                if (node.id) return `#${node.id}`;
                if (node.name) return `[name="${node.name}"]`;
                let selector = node.tagName.toLowerCase();
                if (node.className) {
                    selector += "." + node.className.trim().split(/\s+/).join('.');
                }
                return selector;
            }""")

            # 8. Captura de Contexto de Vizinhança
            content_context = await el.evaluate("""(node) => {
                const parent = node.parentElement;
                const prevText = node.previousElementSibling ? node.previousElementSibling.innerText.trim() : "";
                const nextText = node.nextElementSibling ? node.nextElementSibling.innerText.trim() : "";
                const pText = parent ? parent.innerText.split('\\n')[0].trim() : ""; 
                return `${prevText} | ${nextText} | context: ${pText}`.replace(/\\s+/g, ' ').substring(0, 160);
            }""")

            # 9. Captura de Opções (Para SELECT)
            options = []
            if tag_name == "select":
                options = await el.evaluate("""(node) => 
                    Array.from(node.options).map(opt => opt.text.trim()).filter(t => t !== "")
                """)

            # Instanciando o Modelo Completo
            input_data = WebInput(
                tag_name=tag_name,
                html_name=name,
                html_id=id_attr,
                html_class=class_attr,
                type=input_type if input_type else tag_name,
                value=input_value,
                placeholder=placeholder,
                label_text=label_text,
                title=title,
                aria_label=aria_label,
                aria_describedby_text=aria_describedby_text,
                inner_text=inner_text,
                content_context=content_context,
                fieldset_legend=parent_form_data.get("fieldset_legend", ""),
                role=role,
                css_selector=css_selector,
                pattern=pattern,
                inputmode=input_mode,
                is_visible=is_visible,
                maxlength=max_length,
                minlength=min_length,
                required=is_required,
                disabled=is_disabled,
                parent_form_id=parent_form_data.get("form_id", ""),
                parent_form_action=parent_form_data.get("form_action", ""),
                parent_form_method=parent_form_data.get("form_method", "GET"),
                data_attributes=advanced_attrs.get("data_attrs", {}),
                inline_events=advanced_attrs.get("inline_events", []),
                framework_bindings=advanced_attrs.get("frameworks", []),
                options=options
            )
            inputs_list.append(input_data)

        await browser.close()
        return ScanMappedData(url=target_url, inputs=inputs_list)


if __name__ == "__main__":
    # url_vulneravel = "https://quotes.toscrape.com/login"
    # url_vulneravel = "https://the-internet.herokuapp.com/login"
    # url_vulneravel = "https://leanpub.com/juice-shop"
    resultado = asyncio.run(run_smart_crawler(url_vulneravel))
    print(resultado.model_dump_json(indent=2))