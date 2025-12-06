import hashlib
import os
import json
from datetime import datetime

TITLE_CACHE_FILE = "data/title_cache.json"
SEEN_PRODUCTS_FILE = "data/seen_products.json"

title_cache = set()
seen_products = {}

def init_title_cache():
    global title_cache, seen_products

    if os.path.exists(TITLE_CACHE_FILE):
        with open(TITLE_CACHE_FILE, "r", encoding="utf-8") as f:
            title_cache = set(json.load(f))

    if os.path.exists(SEEN_PRODUCTS_FILE):
        with open(SEEN_PRODUCTS_FILE, "r", encoding="utf-8") as f:
            seen_products = json.load(f)

def save_title_cache():
    # 🚨 CORRECCIÓN: Manejar el PermissionError al guardar
    try:
        with open(TITLE_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(list(title_cache), f, ensure_ascii=False, indent=2)

        with open(SEEN_PRODUCTS_FILE, "w", encoding="utf-8") as f:
            json.dump(seen_products, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        # Esto evita que el bot muera; solo se salta el guardado en este ciclo.
        print(f"[CACHE] ❌ Advertencia: No se pudo guardar el caché. Error: {e}")

def is_product_seen(title: str, canonical_id: str) -> bool:
    title_hash = hashlib.md5(title.lower().strip().encode()).hexdigest()
    return title_hash in title_cache or canonical_id in seen_products

def add_product_to_cache(it: dict, final_link: str):
    title = it.get("title", "").lower().strip()
    
    # 🚨 FIX CRÍTICO: Asegurarse de que final_link no sea None
    if not final_link:
        print("[CACHE] ⚠️ Advertencia: Link nulo o vacío, no se agregó a la caché.")
        return False
        
    canonical = final_link.strip()
    title_hash = hashlib.md5(title.encode()).hexdigest()
    title_cache.add(title_hash)
    seen_products[canonical] = datetime.now().isoformat()
    save_title_cache()
    return True