import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()
EMAIL = os.getenv("TESTE_EMAIL")
PASSWORD = os.getenv("TESTE_PSWD")

def login():
    print(f"Email: {EMAIL}")
    
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.new_page()
        
        page.goto(
            "https://www.natura.com.br/login?redirect=%2F&origin=menu",
            wait_until="domcontentloaded"
        )
        
        page.wait_for_selector("#login-field", timeout=10000, state="visible")
        
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
        
        # Espera os cookies de sessão chegarem (não depende de redirect)
        page.wait_for_timeout(8000)
        
        # Salva independente da URL atual
        context.storage_state(path="state.json")
        print(f"URL atual: {page.url}")
        print("✅ Sessão salva em state.json!")
        
        # Confirma que há cookies de sessão
        cookies = context.cookies()
        cookies_natura = [c for c in cookies if "natura" in c["domain"]]
        print(f"Cookies da Natura salvos: {len(cookies_natura)}")
        for c in cookies_natura:
            print(f"  {c['name']}: {c['value'][:30]}...")

if __name__ == "__file__":
    login()

if __name__ == "__main__":
    login()
