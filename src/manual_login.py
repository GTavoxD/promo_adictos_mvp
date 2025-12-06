# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import time
import os

# Ruta donde se guardará la sesión
STATE_PATH = "data/ml_affiliate_state.json"

def run_login():
    print("🚀 Abriendo navegador en modo 'HUMANO'...")
    
    with sync_playwright() as p:
        # Lanzamos Chrome con argumentos para ocultar que es un robot
        browser = p.chromium.launch(
            headless=False, # Visible
            args=[
                "--disable-blink-features=AutomationControlled", # 👈 CLAVE: Oculta la automatización
                "--start-maximized",
                "--no-sandbox"
            ]
        )
        
        # Contexto con User Agent real
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        page = context.new_page()
        
        # Vamos a Mercado Libre
        print("🌐 Navegando a Mercado Libre...")
        page.goto("https://www.mercadolibre.com.mx", timeout=60000)
        
        print("\n" + "="*50)
        print("   ⚡ ACCIÓN REQUERIDA ⚡")
        print("1. El navegador está abierto. Ve y DA CLIC en 'Ingresa' o 'Inicia Sesión'.")
        print("2. Resuelve el CAPTCHA (ahora debería cargar).")
        print("3. Entra a tu cuenta.")
        print("4. Navega a cualquier producto y VERIFICA que veas la barra negra de afiliados arriba.")
        print("="*50 + "\n")
        
        input(">>> CUANDO TERMINES Y VEAS LA BARRA NEGRA, PRESIONA ENTER AQUÍ...")
        
        # Guardar cookies
        context.storage_state(path=STATE_PATH)
        print(f"\n✅ ¡ÉXITO! Sesión guardada en: {STATE_PATH}")
        print("Ya puedes cerrar esta ventana y ejecutar el BOT.")
        
        browser.close()

if __name__ == "__main__":
    # Crear carpeta data si no existe
    if not os.path.exists("data"):
        os.makedirs("data")
    run_login()