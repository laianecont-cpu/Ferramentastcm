python -m pip install --upgrade pip
pip install -r requirements.txt

import os
import pandas as pd
from playwright.sync_api import sync_playwright

PLANILHA_PATH = "Processos_doe_2.xlsx"

if not os.path.exists(PLANILHA_PATH):
    print(f"Ficheiro {PLANILHA_PATH} não encontrado.")
    exit()

df = pd.read_excel(PLANILHA_PATH, dtype={'processo': str})
processos_busca = [str(p).strip().lower() for p in df['processo'].dropna().tolist()]
print(f"Processos a monitorizar: {processos_busca}")

def executar_automacao():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("Acedendo ao site do TCM-BA...")
        page.goto("https://egbanet.egba.ba.gov.br/tcm")
        page.wait_for_load_state("networkidle")

        btn_pdf = page.locator("a:has-text('PDF'), span:has-text('PDF')").first
        if btn_pdf.is_visible():
            btn_pdf.click()
            page.wait_for_load_state("networkidle")
        else:
            print("Não foi possível encontrar o botão PDF.")
            browser.close()
            return

        seletor_pagina = page.locator("select.select-pagina")
        
        if seletor_pagina.is_visible():
            opcoes_paginas = page.eval_on_selector_all(
                "select.select-pagina option", 
                "elements => elements.map(el => el.value)"
            )
            print(f"Total de páginas na edição: {len(opcoes_paginas)}")

            processo_encontrado = False

            for num_pagina in opcoes_paginas:
                seletor_pagina.select_option(value=num_pagina)
                page.wait_for_timeout(1000)

                texto_pagina = page.content().lower()

                for proc in processos_busca:
                    if proc in texto_pagina:
                        print(f"PROCESSO ENCONTRADO! O processo '{proc}' foi detetado na página {num_pagina}.")
                        processo_encontrado = True
                        break

                if processo_encontrado:
                    break

            if processo_encontrado:
                print("A iniciar o download da edição completa...")
                btn_download = page.locator("#baixar-diario-completo, a.full-download")
                
                if btn_download.is_visible():
                    with page.expect_download() as download_info:
                        btn_download.click()
                    
                    download = download_info.value
                    caminho_destino = "Edicao_Completa_Diario.pdf"
                    download.save_as(caminho_destino)
                    print(f"Download concluído com sucesso! Ficheiro salvo em: {caminho_destino}")
            else:
                print("Nenhum dos processos da planilha foi localizado na edição de hoje.")
        else:
            print("Lista suspensa de páginas não foi localizada.")

        browser.close()

if __name__ == "__main__":
    executar_automacao()
