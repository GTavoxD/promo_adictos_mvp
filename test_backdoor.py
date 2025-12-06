import requests
import os
from dotenv import load_dotenv

load_dotenv()
access_token = os.getenv("MELI_REFRESH_TOKEN", "").strip() # Usamos esto solo para renovar si hiciera falta
# Nota: Asumimos que el token access está fresco o que probaremos sin token también.

def probar_puerta_trasera():
    # ID de Categoría Videojuegos en México: MLM1144
    category_id = "MLM1144" 
    
    headers = {
        # A veces, NO enviar Authorization ayuda en endpoints públicos de navegación
        "User-Agent": "PromoAdictosBot/1.0"
    }

    print("🕵️ Probando rutas alternativas de datos...\n")

    # --- RUTA 1: HIGHLIGHTS (Lo más destacado de una categoría) ---
    # Este endpoint suele ser más permisivo.
    url_highlights = f"https://api.mercadolibre.com/highlights/MLM/category/{category_id}"
    
    print(f"1️⃣ Intentando descargar 'Destacados de Videojuegos'...")
    try:
        r = requests.get(url_highlights, headers=headers)
        if r.status_code == 200:
            data = r.json()
            items = data.get('content', [])
            print(f"   ✅ ¡ABIERTO! Se encontraron {len(items)} items destacados.")
            if items:
                first = items[0]
                print(f"   Ejemplo: {first.get('title')} - ${first.get('price')}")
        else:
            print(f"   ❌ BLOQUEADO ({r.status_code})")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # --- RUTA 2: CLASIFICADO POR PRECIO EN LISTADO ---
    # En lugar de /search, usamos el listado de categoría directo
    print(f"\n2️⃣ Intentando listar items de categoría directamente...")
    url_cat_search = f"https://api.mercadolibre.com/sites/MLM/search?category={category_id}&sort=price_asc&limit=3"
    
    try:
        r2 = requests.get(url_cat_search, headers=headers)
        if r2.status_code == 200:
            print(f"   ✅ ¡ABIERTO! (Búsqueda por categoría funciona)")
            item = r2.json()['results'][0]
            print(f"   Item más barato: {item.get('title')} - ${item.get('price')}")
        else:
            print(f"   ❌ BLOQUEADO ({r2.status_code}) - El firewall odia /search incluso con categorías.")
    except:
        pass

if __name__ == "__main__":
    probar_puerta_trasera()