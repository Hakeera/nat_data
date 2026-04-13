import sys
import re
from pathlib import Path
import pandas as pd
from playwright.sync_api import sync_playwright


def montar_url(ciclo):
    ciclo = str(ciclo).zfill(2)
    return f"https://br.natura.digital-catalogue.com/br/2026/{ciclo}/revista/{ciclo}-sul-e-sao-paulo/view/index.html?page=1"


def capturar_produtos(ciclo):
    url = montar_url(ciclo)
    print(f"URL: {url}")

    # Diretório base do projeto
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / "data"
    data_dir.mkdir(exist_ok=True)

    arquivo_xlsx = data_dir / f"produtos_revista_{str(ciclo).zfill(2)}.xlsx"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        produtos = []
        capturado = False  # evita múltiplas capturas duplicadas

        def on_response(response):
            nonlocal produtos, capturado

            if "/indexes" in response.url and response.status == 200:
                if capturado:
                    return  # evita duplicar se a API chamar mais de uma vez

                try:
                    data = response.json()

                    if isinstance(data, list) and len(data) > 0:
                        produtos.extend(data)
                        capturado = True
                        print(f"CAPTURADO: {len(data)} PRODUTOS")

                except Exception as e:
                    print(f"ERRO_JSON: {e}")

        page.on("response", on_response)

        print("CARREGANDO_CATALOGO")
        page.goto(url, wait_until="networkidle")

        # fallback caso a API demore
        page.wait_for_timeout(5000)

        browser.close()

    if not produtos:
        print("ERRO: NENHUM_PRODUTO")
        sys.exit(1)

    # normalização básica
    df = pd.DataFrame(produtos)

    # remove duplicados de forma mais robusta
    df = df.drop_duplicates()

    # exporta
    try:
        df.to_excel(arquivo_xlsx, index=False, engine="openpyxl")
    except Exception as e:
        print(f"ERRO_SALVAR: {e}")
        sys.exit(1)

    print(f"SUCESSO: {arquivo_xlsx}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("USO: python3 revista_api.py <CICLO>")
        print("EXEMPLO: python3 revista_api.py 06")
        sys.exit(1)

    ciclo = sys.argv[1]

    # validação simples (evita input lixo do Excel)
    if not re.match(r"^\d{1,2}$", ciclo):
        print("ERRO: CICLO_INVALIDO")
        sys.exit(1)

    capturar_produtos(ciclo)
