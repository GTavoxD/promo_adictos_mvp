import requests
import os
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("MELI_REFRESH_TOKEN", "").strip() 
# Nota: Usamos el refresh token para sacar uno fresco rápido, 
# en un script real usarías la lógica de renovación completa.
# Para este test rápido, asumimos que tu main_search.py ya actualizó el token recientemente.
# Si falla la auth, corre main_search.py una vez antes.

# Recuperamos el Access Token fresco (truco rápido usando tu función existente si quieres, 
# pero aquí lo haremos directo para aislar el test)
client_id = os.getenv("MELI_CLIENT_ID", "").strip()
client_secret = os.getenv("MELI_CLIENT_SECRET", "").strip()

def obtener_token_rapido():
    url = "https://api.mercadolibre.com/oauth/token"
    payload = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": token
    }
    r = requests.post(url, data=payload)
    if r.status_code == 200:
        return r.json()['access_token']
    return None

def ejecutar_diagnostico():
    access_token = obtener_token_rapido()
    if not access_token:
        print("❌ No se pudo generar token para el test. Corre main_search.py primero.")
        return

    headers = {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "PromoAdictosBot/1.0"
    }

    print("🩺 INICIANDO DIAGNÓSTICO DE PUERTAS...\n")

    # --- PRUEBA 1: Lectura Directa de un Item (ID específico) ---
    # Usaremos el ID de un Nintendo Switch OLED genérico o un item activo
    item_id = "MLM1909062337" 
    print(f"1️⃣ Probando Lectura de Item ({item_id})...")
    r1 = requests.get(f"https://api.mercadolibre.com/items/{item_id}", headers=headers)
    
    if r1.status_code == 200:
        print(f"   ✅ ABIERTO: {r1.json().get('title')} | ${r1.json().get('price')}")
    else:
        print(f"   ❌ CERRADO: Error {r1.status_code}")

    # --- PRUEBA 2: Navegación por Categorías (Sin buscar texto) ---
    # Categoría MLM1055 = Consolas y Videojuegos
    print(f"\n2️⃣ Probando Categorías (Videojuegos)...")
    r2 = requests.get(f"https://api.mercadolibre.com/categories/MLM1055", headers=headers)
    
    if r2.status_code == 200:
        print(f"   ✅ ABIERTO: Acceso a categoría '{r2.json().get('name')}'")
    else:
        print(f"   ❌ CERRADO: Error {r2.status_code}")

    # --- PRUEBA 3: Búsqueda RESTRINGIDA (Por Vendedor) ---
    # A veces buscar "todo" falla, pero buscar en una tienda oficial funciona.
    print(f"\n3️⃣ Probando Búsqueda Específica (Tienda Oficial Nintendo)...")
    # Intentamos buscar filtrando, a veces esto salta el firewall
    params = {"category": "MLM1055", "limit": 1}
    r3 = requests.get("https://api.mercadolibre.com/sites/MLM/search", headers=headers, params=params)
    
    if r3.status_code == 200:
        print(f"   ✅ ABIERTO: La búsqueda por categoría funcionó.")
    else:
        print(f"   ❌ CERRADO: La búsqueda sigue bloqueada ({r3.status_code}).")

if __name__ == "__main__":
    ejecutar_diagnostico()