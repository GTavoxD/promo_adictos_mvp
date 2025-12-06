from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(storage_state="meli_login.json")
    page = context.new_page()
    page.goto("https://articulo.mercadolibre.com.mx/MLM-1360873480", timeout=30000)
    page.wait_for_selector('[data-testid="review-ratings"]', timeout=10000)
    html = page.content()
    print("Tiene bloque de reseñas:", '[data-testid="review-ratings"]' in html)
    browser.close()
