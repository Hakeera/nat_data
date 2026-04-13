import httpx
import time
import json
from datetime import datetime
import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()
EMAIL = os.getenv("TESTE_EMAIL")
PASSWORD = os.getenv("TESTE_PSWD")

BASE_URL = "https://www.natura.com.br/bff-app-natura-brazil/search"

HEADERS = {
    "accept": "application/json",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Tenant_id": "brazil-natura-web",
    "referer": "https://www.natura.com.br/",
    "origin": "https://www.natura.com.br",
}

PARAMS_BASE = {
    "count": 24,
    "q": "",
    "expand": "prices,availability,images,variations",
    "sort": "top-sellers",
    "refine_1": "cgid=promocoes",
    "apiMode": "product"
}


# ── LOGIN ────────────────────────────────────────────────────────────────────

def fazer_login() -> dict:
    """Abre o Brave via CDP, loga e retorna cookies prontos pro httpx."""
    print("Conectando ao Brave...")
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.new_page()

        print("Navegando para página de login...")
        page.goto(
            "https://www.natura.com.br/login?redirect=%2F&origin=menu",
            wait_until="domcontentloaded"
        )
        page.wait_for_selector("#login-field", timeout=20000, state="visible")

        page.click("#login-field")
        page.wait_for_timeout(500)
        for char in EMAIL:
            page.keyboard.type(char, delay=80)

        page.wait_for_timeout(800)
        page.click("#login-password")
        page.wait_for_timeout(500)
        for char in PASSWORD:
            page.keyboard.type(char, delay=80)

        page.wait_for_timeout(1000)
        page.click('button[type="submit"]')
        print("Aguardando sessão ser estabelecida...")
        page.wait_for_timeout(8000)

        # Salva state.json para reuso futuro
        context.storage_state(path="state.json")

        # Converte cookies do Playwright → formato httpx
        cookies_raw = context.cookies()
        cookies = {
            c["name"]: c["value"]
            for c in cookies_raw
            if "natura" in c["domain"]
        }

        print(f"✅ Login ok! {len(cookies)} cookies capturados.")
        return cookies


def carregar_cookies_salvos() -> dict | None:
    """Reutiliza state.json se existir e for recente (menos de 12h)."""
    if not os.path.exists("state.json"):
        return None

    idade = time.time() - os.path.getmtime("state.json")
    if idade > 12 * 3600:
        print("state.json expirado, fazendo novo login...")
        return None

    with open("state.json") as f:
        state = json.load(f)

    cookies = {
        c["name"]: c["value"]
        for c in state.get("cookies", [])
        if "natura" in c.get("domain", "")
    }
    print(f"✅ Sessão reutilizada! {len(cookies)} cookies carregados.")
    return cookies


def obter_cookies() -> dict:
    """Tenta reutilizar sessão salva, senão faz login."""
    cookies = carregar_cookies_salvos()
    if not cookies:
        cookies = fazer_login()
    return cookies


# ── COLETA ───────────────────────────────────────────────────────────────────

def save_json(produtos):
    print("Salvando JSON...")
    os.makedirs("data", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d")
    filename = f"data/produtos_{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(produtos, f, ensure_ascii=False, indent=2)
    print(f"Arquivo salvo em: {filename}")

def fetch_page(client, start, tentativas=3):
    params = PARAMS_BASE.copy()
    params["start"] = start

    for tentativa in range(1, tentativas + 1):
        try:
            response = client.get(BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (504, 503, 502) and tentativa < tentativas:
                espera = 5 * tentativa  # 5s, 10s, 15s
                print(f"  ⚠️ {e.response.status_code} na tentativa {tentativa}, aguardando {espera}s...")
                time.sleep(espera)
            else:
                raise
        except httpx.RequestError as e:
            if tentativa < tentativas:
                print(f"  ⚠️ Erro de conexão tentativa {tentativa}: {e}, aguardando 10s...")
                time.sleep(10)
            else:
                raise

def normalize(p):
    now = datetime.now().isoformat()
    price = p.get("price", {})
    sales = price.get("sales") or {}
    list_price = price.get("list") or {}
    preco = float(sales.get("decimalPrice", 0))
    preco_original = (
        float(list_price["decimalPrice"])
        if list_price and list_price.get("decimalPrice")
        else preco
    )
    return {
        "id": p.get("productId"),
        "nome": p.get("name"),
        "preco": preco,
        "preco_original": preco_original,
        "desconto": price.get("discountPercent", 0),
        "disponivel": p.get("orderable", False) and p.get("inStock", False),
        "categoria": p.get("classificationName"),
        "marca": p.get("brand"),
        "coletado_em": now,
    }


def fetch_all(cookies: dict):
    start = 0
    count = PARAMS_BASE["count"]
    all_products = []
    total = None

    with httpx.Client(headers=HEADERS, cookies=cookies, timeout=30.0) as client:
        while True:
            print(f"Buscando página start={start}...")
            data = fetch_page(client, start)
            products = data.get("products", [])

            if total is None:
                total = data.get("total")
                print(f"Total esperado: {total}")

            if not products:
                print("Sem mais produtos, encerrando.")
                break

            for p in products:
                all_products.append(normalize(p))

            start += count
            if total and start >= total:
                break

            time.sleep(1)

    return all_products


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    cookies = obter_cookies()
    produtos = fetch_all(cookies)
    print(f"\nTotal coletado: {len(produtos)} produtos")
    save_json(produtos)


if __name__ == "__main__":
    main()
