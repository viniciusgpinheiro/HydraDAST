import asyncio
from playwright.async_api import async_playwright
from models.WebInput import WebInput
from models.ScanMappedData import ScanMappedData


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
            # Extração de atributos para o NLP
            name = await el.get_attribute("name")
            id_attr = await el.get_attribute("id")
            input_type = await el.get_attribute("type") or "text"
            placeholder = await el.get_attribute("placeholder") or ""
            
            # Tenta buscar o label associado (para contexto semântico)
            label_text = ""
            if id_attr:
                label_el = await page.query_selector(f"label[for='{id_attr}']")
                if label_el:
                    label_text = await label_el.inner_text()

            # Cria o objeto Pydantic (Validação automática)
            input_data = WebInput(
                html_name=name,
                html_id=id_attr,
                type=input_type,
                placeholder=placeholder,
                label_text=label_text
            )
            inputs_list.append(input_data)

        await browser.close()
        
        return ScanMappedData(url=target_url, inputs=inputs_list)

# Exemplo de execução (Para testar contra o seu Juice Shop no Docker)
if __name__ == "__main__":
    url_vulneravel = "https://the-internet.herokuapp.com/login"
    resultado = asyncio.run(run_smart_crawler(url_vulneravel))
    print(resultado.json(indent=2))