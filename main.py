# -*- coding: utf-8 -*-
import os
import time
from datetime import datetime
import logging
from urllib.parse import urlsplit, urlparse, urlunparse
from html import escape
import sys
import io
import re
import difflib
import random
import csv
from collections import defaultdict

from dotenv import load_dotenv

# ✅ Forzar UTF-8 en Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Importaciones del proyecto
from src.rules import score_item
from src.telegram import post_telegram, post_telegram_photo
from src.store_cache import (
    init_title_cache,
    is_product_seen,
    add_product_to_cache
)
from src.affiliate_runtime import get_or_create_affiliate_url
from src.promo_enricher import enrich_item
from src.database import add_published_offer, init_database, print_stats
from src.price_validator import is_discount_real
from src.logger import get_logger

# ============================
# 📊 LOGGING SETUP
# ============================
logger = get_logger("promo_adictos")

# ============================
# 🔥 BLOQUEO DE PRODUCTOS (BLACKLIST)
# ============================

# 🔞 Adultos
BANNED_ADULT = [
    "juguete sexual", "adultos", "sexy", "erotico",
    "dildo", "sexo", "condon", "pene", "vibrador", "lubricante"
]

# 👕 Ropa íntima
BANNED_CLOTHING = [
    "ropa interior", "boxer", "calzon",
    "braga", "panty", "panties", "tanga", "lenceria", "brasier"
]

# 💊 Farmacia y suplementos
BANNED_HEALTH = [
    "vitamina", "suplemento alimenticio", "farmacia",
    "medicina", "pastilla", "tableta recubierta", "medicamento"
]

# 🏠 Línea blanca y muebles grandes
BANNED_HOME = [
    "colchon", "matrimonial", "king", "queen",
    "parrilla de gas", "parrilla electrica", "estufa", 
    "lavadora", "secadora", "refrigerador", "refrigeradora",
    "sala", "comedor", "ropero", "closet"
]

# 💳 Productos digitales
BANNED_DIGITAL = [
    "gift card", "tarjeta regalo",
    "saldo", "codigo digital", "licencia digital"
]

# 📚 Otros / Basura / Accesorios genéricos
BANNED_MISC = [
    "libro usado", "revista", "fanzine",
    "pintura al oleo", "lienzo", "acuarela",
    "manualidades", "hecho a mano",
    "hospital", "hospitalario", "quirurgico", "ortopedico",
    "silla de ruedas", "muletas",
    "protector de pantalla", "mica de vidrio", "glass",
    "funda para celular", "case para iphone", "carcasa para",
    "correa para", "extensible para"
]

# ✅ Unión de todas las listas
BLACKLIST_KEYWORDS = (
    BANNED_ADULT + BANNED_CLOTHING + BANNED_HEALTH +
    BANNED_HOME + BANNED_DIGITAL + BANNED_MISC
)

def normalize_title(title: str) -> str:
    title = title.lower()
    colores = [
        "negro", "blanco", "gris", "rojo", "azul", "rosa", "verde",
        "beige", "café", "marr[oó]n", "amarillo", "naranja", "morado", "lila", "dorado", "plateado"
    ]
    for color in colores:
        title = re.sub(rf"\b{color}\b", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title

def should_block(it: dict) -> str | None:
    """Devuelve el motivo de bloqueo si aplica, o None si pasa."""
    title = (it.get("title") or "").lower()
    category = (it.get("category_label") or "").lower()
    promo = (it.get("promo_tag") or "").lower()
    text = f"{title} {category} {promo}"

    for keyword in BANNED_ADULT:
        if keyword in text: return f"🔞 Adulto: '{keyword}'"
    for keyword in BANNED_CLOTHING:
        if keyword in text: return f"👕 Ropa íntima: '{keyword}'"
    for keyword in BANNED_HEALTH:
        if keyword in text: return f"💊 Farmacia/suplemento: '{keyword}'"
    for keyword in BANNED_HOME:
        if keyword in text: return f"🏠 Línea blanca/muebles: '{keyword}'"
    for keyword in BANNED_DIGITAL:
        if keyword in text: return f"💳 Digital: '{keyword}'"
    for keyword in BANNED_MISC:
        if keyword in text: return f"📚 Misceláneo: '{keyword}'"

    return None

# ============================
# 🎯 FILTRO DE CALIDAD
# ============================

def is_low_quality(it: dict) -> bool:
    """Rechaza productos de baja calidad basado en rating y ventas."""
    try:
        rating = float(it.get("rating") or 0)
    except Exception:
        rating = 0.0

    try:
        reviews = int(it.get("reviews_count") or 0)
    except Exception:
        reviews = 0

    try:
        sold = int(it.get("sold_quantity") or 0)
    except Exception:
        sold = 0

    promo = (it.get("promo_tag") or "").lower()

    # 1. Validación de Rating
    if reviews >= 10:
        if rating < 3.5:
            logger.info(f"[Q] Rating bajo ({rating}) con reviews: {reviews}")
            return True 
        elif reviews >= 40 and rating < 4.0:
            pass 

    # 2. Ventas mínimas si no hay promo fuerte
    has_strong_promo = any(p in promo for p in ("relámpago", "imperdible", "oferta del día", "full", "más vendido"))

    if sold < 50 and not has_strong_promo and rating == 0:
        logger.info(f"[Q] Pocas ventas ({sold}), sin rating y sin promo fuerte")
        return True

    return False

# ============================
# ✅ VALIDACIÓN DE ITEMS
# ============================

def is_valid_item(it: dict) -> bool:
    """Valida que un item tenga los campos mínimos."""
    try:
        original_price = float(it.get("original_price") or 0)
        current_price = float(it.get("price") or 0)
        
        if original_price <= 0 or current_price <= 0:
            return False
        
        if original_price <= current_price:
            return False 
        
        title = (it.get("title") or "").strip()
        if not title:
            return False
        
        return True
    except (ValueError, TypeError):
        return False

# ============================
# 🔧 UTILIDADES Y CONFIG
# ============================

def get_env_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, str(default)) or default)
    except (ValueError, TypeError):
        return default

def get_env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)) or default)
    except (ValueError, TypeError):
        return default

def is_similar_title(t1: str, t2: str, threshold: float = 0.9) -> bool:
    t1 = (t1 or "").lower().strip()
    t2 = (t2 or "").lower().strip()
    if not t1 or not t2: return False
    similarity = difflib.SequenceMatcher(None, t1, t2).ratio()
    return similarity >= threshold

def canonical_id(it: dict) -> str:
    url = it.get("permalink") or ""
    if not url: return str(it.get("id", ""))
    parts = urlsplit(url)
    return parts.scheme + "://" + parts.netloc + parts.path

def within_active_window() -> bool:
    start_h = get_env_int("ACTIVE_HOUR_START", 8)
    end_h = get_env_int("ACTIVE_HOUR_END", 23)
    now = datetime.now()
    return start_h <= now.hour < end_h

# -------------------------------------------------------------------------
# ⌨️ NUEVA FUNCIÓN: SMART SLEEP (ESPERA CON SKIP)
# -------------------------------------------------------------------------
def smart_sleep(seconds: int):
    """
    Espera 'seconds' segundos, pero permite saltar la espera
    presionando ENTER o ESPACIO en la consola.
    """
    if sys.platform == "win32":
        try:
            import msvcrt
            print("   [⌨️ TIP: Presiona ENTER o ESPACIO para saltar la espera...]")
            
            end_time = time.time() + seconds
            while time.time() < end_time:
                # Si se detecta una tecla presionada
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    # Si es Enter (\r) o Espacio ( )
                    if key in [b'\r', b' ']:
                        print("\n   ⏩ Espera saltada por el usuario.")
                        # Limpiar buffer de teclado por si presionaste varias veces
                        while msvcrt.kbhit():
                            msvcrt.getch()
                        return
                time.sleep(0.1)
        except ImportError:
            # Fallback si falla la librería
            time.sleep(seconds)
    else:
        # Fallback para Linux/Mac (aunque usas Windows)
        time.sleep(seconds)

# ============================
# 💰 FORMATOS, CSV Y REPORTE
# ============================

def fmt_money(v):
    try:
        return "${:,.0f} MXN".format(float(v))
    except Exception:
        return str(v)

def calculate_discount_percentage(original_price: float, final_price: float) -> int:
    if original_price <= 0 or final_price <= 0: return 0
    if final_price >= original_price: return 0
    pct = (original_price - final_price) / original_price * 100
    return int(round(pct))

def save_offer_to_csv(it, discount, final_link):
    filename = "data/ofertas_publicadas.csv"
    file_exists = os.path.isfile(filename)
    if not os.path.exists("data"):
        os.makedirs("data")
        
    with open(filename, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "title", "price", "original_price", "discount_pct", "promo_tag", "link"
        ])
        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "title": it.get("title", ""),
            "price": it.get("price", ""),
            "original_price": it.get("original_price", ""),
            "discount_pct": int(discount * 100),
            "promo_tag": get_promo_tag_safe(it),
            "link": final_link
        })

def save_blocked_log(blocked_list: list):
    if not blocked_list: return
    filename = "data/bloqueos.csv"
    file_exists = os.path.isfile(filename)
    if not os.path.exists("data"):
        os.makedirs("data")
    with open(filename, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "title", "reason"])
        if not file_exists:
            writer.writeheader()
        for item in blocked_list:
            writer.writerow(item)

# ============================
# 🖼️ LÓGICA DE IMAGEN
# ============================

def get_product_image(it: dict) -> str:
    def clean_url(u):
        if not u: return ""
        u = u.strip()
        if u.startswith("//"): u = "https:" + u
        if "mlstatic.com" in u:
            u = u.split("?")[0].split("#")[0]
        return u

    candidates = [
        it.get("image_url"),       
        it.get("thumbnail"),       
        it.get("thumbnail_url"),
        it.get("secure_thumbnail"),
        it.get("image")
    ]

    for raw_url in candidates:
        if not isinstance(raw_url, str): continue
        url = clean_url(raw_url)
        u_lower = url.lower()
        if not u_lower.startswith("http"): continue
        if u_lower.endswith(".svg") or u_lower.endswith(".gif"): continue
        if "pixel" in u_lower: continue
        if "_v1.jpg" in u_lower:
             url = url.replace("_A.jpg", "_Q.jpg").replace("_B.jpg", "_Q.jpg").replace("_I.jpg", "_V.jpg")
        return url
    return ""

# ============================
# 🎨 GENERADOR DE CAPTION Y TAGS (BLINDADO - FINAL)
# ============================

def get_promo_tag_safe(item: dict) -> str:
    """
    Confianza total en el tag generado por promo_enricher.py.
    Devuelve el tag tal como viene (concatenado, con emojis).
    """
    # 🚨 SOLUCIÓN: Devuelve directamente el tag procesado. 
    # Si promo_enricher devolvió 'Relámpago | FULL', esto lo respeta.
    return item.get("promo_tag") or ""
    
    # 🚨 PASO 1: CONFIAR EN EL ENRICHER
    # Si el tag ya tiene algún emoji conocido, el enricher hizo bien su trabajo.
    if any(c in raw_tag for c in ["⚡", "🔥", "⏰", "💎", "⭐"]):
        return raw_tag # Retornamos el tag combinado (ej: "Relámpago | FULL")

    # 🚨 PASO 2: FALLBACK DE SEGURIDAD (Si el Enricher falló o no puso emoji)
    
    # Normalizamos para la búsqueda de texto
    combined_norm = raw_tag.upper().replace("Á","A").replace("É","E").replace("Í","I").replace("Ó","O").replace("Ú", "U")
    
    final_label = ""
    
    # Buscamos la etiqueta principal SIN ACENTO
    patterns = [
        ("RELAMPAGO", "⚡ Oferta Relámpago"),
        ("IMPERDIBLE", "💎 Imperdible"),
        ("OFERTA DEL DIA", "⏰ Oferta del Día"), 
        ("MAS VENDIDO", "🔥 Más Vendido"),    
    ]
    
    for kw, label in patterns:
        if kw in combined_norm:
            final_label = label
            break
            
    # Paso 3: Re-concatenar FULL si estaba presente en el crudo
    is_full = "FULL" in combined_norm
    if is_full:
        full_tag = " | ⚡ FULL"
        if final_label:
            if "FULL" not in final_label.upper():
                final_label = f"{final_label}{full_tag}"
        else:
            final_label = "⚡ FULL"
            
    return final_label or raw_tag
    
def get_rating_text(it: dict) -> str:
    try:
        rating = float(it.get("rating", 0))
        reviews = int(it.get("reviews_count", 0))
        if rating <= 0: return ""
        if reviews > 0:
            return f"<b>⭐</b> <b>({rating:.1f})</b> ({reviews} opiniones)"
        return f"<b>⭐</b> ({rating:.1f})"
    except:
        return ""

def caption(it, disc, link_final: str) -> str:
    """Genera el caption HTML para Telegram."""
    title = escape((it.get("title") or "")[:140])
    promo_tag = get_promo_tag_safe(it)
    rating_txt = get_rating_text(it)
    
    try:
        orig = float(it.get("original_price") or 0)
        curr = float(it.get("price") or 0)
    except:
        orig = 0; curr = 0

    discount_pct = calculate_discount_percentage(orig, curr)
    
    lines = [f"<b>{title}</b>"]
    
    meta = []
    if promo_tag: meta.append(promo_tag)
    if rating_txt: meta.append(rating_txt)
    if meta: lines.append(" | ".join(meta))
    
    lines.append(f"💳 <b>{fmt_money(curr)}</b> (<s>{fmt_money(orig)}</s> -{discount_pct}%)")
    
    coupon = it.get("coupon_text") or it.get("coupon_note")
    if coupon:
        lines.append(f"<b>{coupon}</b>")
        
    return "\n".join(lines)

# ============================
# 🚀 LOOP PRINCIPAL
# ============================

def run():
    # Importación local para evitar ciclo
    from src.offers_fetcher import fetch_offers

    load_dotenv()
    init_database()
    init_title_cache()
    logger.info("✅ Caché de productos inicializado")

    start_time = time.time()

    if not within_active_window():
        now = datetime.now()
        logger.info(f"Fuera de horario activo ({now.strftime('%H:%M')}). No publico.")
        return

    # Configuración
    min_disc = get_env_float("MIN_DISCOUNT", 0.30)
    top_n = get_env_int("TOP_N", 10)
    post_interval = get_env_int("POST_INTERVAL_SECONDS", 60)
    pages = get_env_int("PAGES", 3)

    if post_interval < 30: post_interval = 60
    
    logger.info(f"MIN_DISCOUNT={int(min_disc*100)}%, TOP_N={top_n}, PAGES={pages}")

    # 1. Fetch de productos
    items = fetch_offers(pages=pages)
    logger.info(f"[DEBUG] Total items crudos: {len(items)}")

    # 2. Deduplicar
    unique_map = {}
    for it in items:
        key = canonical_id(it)
        if key not in unique_map:
            unique_map[key] = it
        else:
            if it.get("price", 999999) < unique_map[key].get("price", 999999):
                unique_map[key] = it
    
    items = list(unique_map.values())
    logger.info(f"[DEBUG] Items únicos: {len(items)}")

    # 3. Filtrado y Enriquecimiento
    blocked_reasons = [] 
    blocked_items_data = [] 
    valid_candidates = []

    for it in items:
        if not is_valid_item(it): continue

        reason = should_block(it)
        if reason:
            blocked_reasons.append(f"{it.get('title')} -> {reason}")
            blocked_items_data.append({
                "timestamp": datetime.now().isoformat(),
                "title": it.get("title", ""),
                "reason": reason
            })
            continue

        it = enrich_item(it)

        if is_product_seen(it["title"], canonical_id(it)): continue
        if not is_discount_real(it, min_disc): continue
        if is_low_quality(it): continue

        score, discount = score_item(it)
        if score > 0:
            it["_score"] = score
            it["discount_pct"] = discount * 100
            valid_candidates.append(it)

    if blocked_reasons:
        logger.warning(f"⚠️ {len(blocked_reasons)} productos bloqueados.")
    if blocked_items_data:
        save_blocked_log(blocked_items_data)
        
    # 4. Ordenar y Seleccionar
    valid_candidates.sort(key=lambda x: x["_score"], reverse=True)
    to_publish = valid_candidates[:top_n]

    logger.info(f"[DEBUG] Ofertas válidas: {len(valid_candidates)}. Publicando TOP {len(to_publish)}.")

    # 5. Publicación
    pushed = 0
    for it in to_publish:
        try:
            # Link Afiliado
            final_link = get_or_create_affiliate_url(it.get("permalink", ""))
            if not final_link: final_link = it.get("permalink", "")
            
            if not final_link:
                continue

            # Preparar medios
            img_url = get_product_image(it)
            disc_val = it.get("discount_pct", 0) / 100
            caption_text = caption(it, disc_val, final_link)

            # Enviar
            ok = False
            if img_url:
                logger.info(f"📸 Enviando FOTO: {img_url[:60]}...")
                ok = post_telegram_photo(img_url, caption_text, url_button=final_link)
            else:
                logger.info(f"📝 Enviando TEXTO (Fallback)...")
                ok = post_telegram(caption_text, url_button=final_link)

            if ok:
                save_offer_to_csv(it, disc_val, final_link)
                add_product_to_cache(it, final_link)
                add_published_offer(it, disc_val, final_link)
                pushed += 1
                
                logger.info(f"✅ Publicado: {it.get('title')[:40]}")
                
                # --------------------------------------------------------
                # ⏳ ESPERA INTELIGENTE (SKIP)
                # --------------------------------------------------------
                wait = post_interval + random.randint(5, 15)
                logger.info(f"⏳ Esperando {wait}s...")
                
                # Usamos la nueva función en lugar de time.sleep()
                smart_sleep(wait) 
                # --------------------------------------------------------
            
            if pushed >= top_n:
                break

        except Exception as e:
            logger.exception(f"❌ Error en publicación: {e}")

    # Reporte final
    print_stats()
    logger.info(f"Total publicadas: {pushed}")

    if pushed == 0:
        from src.alerts import send_warning
        send_warning("Sin ofertas", "No se publicó nada en este ciclo")

    duration = (time.time() - start_time) / 60
    from src.alerts import send_success
    send_success(
        "Bot ejecutado exitosamente",
        f"Duración: {duration:.1f} minutos\nPublicadas: {pushed} ofertas"
    )

if __name__ == "__main__":
    logger.info("🚀 Iniciando PromoAdictos...")
    try:
        run()
    except Exception as e:
        from src.alerts import send_error
        logger.error(f"Error crítico: {e}")
        send_error("Error crítico en el bot", str(e)[:500])
        raise
    
    logger.info("♻️ Reiniciando bot...")
    os.execv(sys.executable, ['python'] + sys.argv)