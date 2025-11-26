# -*- coding: utf-8 -*-
import os
import time
import datetime
import logging
from urllib.parse import urlsplit, urlparse, urlunparse
from html import escape
import sys
import io
import re

from dotenv import load_dotenv

# ✅ Forzar UTF-8 en Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from src.offers_fetcher import fetch_offers
from src.rules import score_item
from src.publisher import post_telegram, post_telegram_photo
from src.store import (
    init_title_cache, 
    is_product_seen,
    add_product_to_cache
)
from src.audit import audit_row
from src.affiliate_runtime import get_or_create_affiliate_url
from src.promo_enricher import enrich_item
from src.database import add_published_offer, init_database, print_stats
from src.price_validator import is_discount_real

# ============================
# 📊 LOGGING SETUP
# ============================

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)-8s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger("promo_bot")

# ============================
# 🔥 BLOQUEO DE PRODUCTOS
# ============================

BANNED_KEYWORDS = [
    "gift card", "tarjeta regalo",
    "recarga", "recargas",
    "refurbished", "reacondicionado", "reacondicionada",
    "ropa interior", "boxer", "calzon",
    "braga", "panty", "panties", "tanga", "lenceria",

    "colchon", "matrimonial", "king", "queen",
    "parrilla de gas", "parrilla electrica", "estufa", 
    "lavadora", "secadora", "refrigerador", "refrigeradora",

    "hospital", "hospitalario", "quirurgico", "ortopedico",
    "Silla De Ruedas",

    "protector de pantalla", "mica de vidrio",
    "funda para celular", "case para iphone", "carcasa para",
    "vitamina", "suplemento alimenticio", "farmacia", "medicina",
    "pastilla", "tableta recubierta",

    "libro usado", "revista", "fanzine",
    "pintura al oleo", "lienzo", "acuarela",
    "manualidades", "hecho a mano",

    "juguete sexual", "adultos", "sexy", "erotico",
    "anal", "dildo", "sexo", "condon", "pene",
]

def should_block(it: dict) -> bool:
    """Verifica si un producto debe ser bloqueado por palabras clave."""
    title = (it.get("title") or "").lower()
    category = (it.get("category_label") or "").lower()
    promo = (it.get("promo_tag") or "").lower()

    text = f"{title} {category} {promo}"

    for bad in BANNED_KEYWORDS:
        if bad in text:
            return True

    return False

# ============================
# 🎯 FILTRO DE CALIDAD
# ============================

def is_low_quality(it: dict) -> bool:
    """Rechaza productos de baja calidad."""
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

    MIN_RATING = 4.2
    MIN_REVIEWS = 40
    MIN_SOLD = 200

    if rating and reviews >= MIN_REVIEWS and rating < MIN_RATING:
        return True

    strong_promo = (
        "relámpago" in promo
        or "relampago" in promo
        or "imperdible" in promo
        or "oferta del día" in promo
        or "oferta del dia" in promo
    )
    if sold and sold < MIN_SOLD and not strong_promo:
        return True

    seller_rating = it.get("seller_rating")
    seller_reputation = it.get("seller_reputation")
    
    if seller_reputation and seller_reputation < 100:
        logger.warning(f"Vendedor con {seller_reputation} operaciones - rechazando")
        return True
        
    return False

# ============================
# ✅ VALIDACIÓN DE ITEMS
# ============================

def is_valid_item(it: dict) -> bool:
    """Valida que un item tenga los campos mínimos y sean del tipo correcto."""
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
# 🔧 FUNCIONES DE CONFIG
# ============================

def get_env_float(key: str, default: float) -> float:
    """Lee una variable de entorno como float."""
    try:
        value = os.getenv(key, str(default))
        return float(value or default)
    except (ValueError, TypeError):
        return default


def get_env_int(key: str, default: int) -> int:
    """Lee una variable de entorno como int."""
    try:
        value = os.getenv(key, str(default))
        return int(value or default)
    except (ValueError, TypeError):
        return default

# ============================
# 💰 FORMATOS MONETARIOS
# ============================

def fmt_money(v):
    """Formatea número a dinero: $1,234 MXN"""
    try:
        return "${:,.0f} MXN".format(float(v))
    except Exception:
        return str(v)


def _normalize_coupon_text_generic(text: str) -> str:
    """Extrae y normaliza texto de cupón."""
    if not text:
        return ""
    import re as _re

    t = " ".join(str(text).split())
    low = t.lower()

    idxs = [
        low.rfind("cupón"),
        low.rfind("cupon"),
        low.rfind("código"),
        low.rfind("codigo"),
    ]
    idx = max(idxs)
    snippet = t[idx:] if idx != -1 else t

    m = _re.search(r"\d{1,3}\s*%\s*off", snippet, flags=_re.IGNORECASE)
    if m:
        return m.group(0).strip().upper()

    m = _re.search(r"\$\s?\d[\d.,]*\s*off", snippet, flags=_re.IGNORECASE)
    if m:
        return m.group(0).strip().upper()

    m = _re.search(r"\$\s?\d[\d.,]*", snippet, flags=_re.IGNORECASE)
    if m:
        return m.group(0).strip()

    return (snippet[:60] + "…") if len(snippet) > 60 else snippet

# ============================
# 🎨 GENERADOR DE CAPTION
# ============================

def get_emoji_for_product(title: str) -> str:
    """Retorna un emoji según la categoría del producto."""
    title_lower = (title or "").lower()
    
    if any(w in title_lower for w in ("scooter", "patín eléctrico", "patin electrico", "hoverboard")):
        return "🛴"
    if any(w in title_lower for w in ("bicicleta", "bici", "mountain bike", "ebike")):
        return "🚲"
    if any(w in title_lower for w in ("motocicleta", "moto", "motocross", "atv")):
        return "🏍️"
    if any(w in title_lower for w in ("carro montable", "auto montable", "ride on")):
        return "🚗"
    if any(w in title_lower for w in ("llanta", "neumático", "rin", "faro")):
        return "🚙"
    if any(w in title_lower for w in ("smart tv", "pantalla", "televisor", "monitor")):
        return "📺"
    if any(w in title_lower for w in ("celular", "smartphone", "iphone", "samsung")):
        return "📱"
    if any(w in title_lower for w in ("laptop", "notebook", "macbook", "computadora")):
        return "💻"
    if any(w in title_lower for w in ("playstation", "xbox", "nintendo switch")):
        return "🎮"
    
    return "🛒"


def get_promo_tag(item: dict) -> str:
    """
    Extrae el mejor tag de promoción disponible del item.
    
    Busca en múltiples campos y patrones para encontrar
    tags como "Oferta relámpago", "Black Friday", etc.
    """
    
    # ✅ PRIORIDAD 1: Usar tag oficial si existe
    official_tag = item.get("promo_tag_official", "")
    if official_tag:
        logger.info(f"[TAG] Usando tag oficial: {official_tag}")
        return official_tag
    
    # ✅ PRIORIDAD 2: Usar tag final del enriquecimiento
    final_tag = item.get("promo_tag_final", "")
    if final_tag:
        logger.info(f"[TAG] Usando tag final: {final_tag}")
        return final_tag
    
    # ✅ PASO 3: Buscar en campos originales
    texts = []
    
    tag_fields = [
        "promo_tag",
        "tag",
        "badge",
        "time_limit_label",
        "promotion",
        "offer_type",
        "promotional_tag",
        "deal_tag",
        "label",
        "highlight"
    ]
    
    for key in tag_fields:
        v = item.get(key)
        if v:
            if isinstance(v, list):
                texts.extend([str(x).strip() for x in v if x])
            else:
                text = str(v).strip()
                if text and len(text) > 0:
                    texts.append(text)
    
    combined = " ".join(texts).lower()
    
    logger.debug(f"[TAG] Campos encontrados: {texts}")
    logger.debug(f"[TAG] Texto combinado: {combined[:100]}")
    
    # Patrones a buscar (en orden de prioridad)
    patterns = [
        # Ofertas relámpago
        ("relampago", "⚡ Oferta relámpago"),
        ("relámpago", "⚡ Oferta relámpago"),
        ("oferta relampago", "⚡ Oferta relámpago"),
        ("oferta relámpago", "⚡ Oferta relámpago"),
        
        # Ofertas del día
        ("oferta del dia", "⏰ Oferta del día"),
        ("oferta del día", "⏰ Oferta del día"),
        ("deal of the day", "⏰ Oferta del día"),
        
        # Eventos especiales
        ("black friday", "🖤 Black Friday"),
        ("cyber monday", "💻 Cyber Monday"),
        ("cyber lunes", "💻 Cyber Monday"),
        ("hot sale", "🔥 Hot Sale"),
        
        # Precios especiales
        ("super precio", "💥 Súper precio"),
        ("súper precio", "💥 Súper precio"),
        ("precio especial", "💳 Precio especial"),
        
        # Popularidad
        ("mas vendido", "🏆 Más Vendido"),
        ("más vendido", "🏆 Más Vendido"),
        ("bestseller", "🏆 Bestseller"),
        ("trending", "📈 Trending"),
        
        # Otros
        ("imperdible", "🔥 Imperdible"),
        ("exclusive", "✨ Exclusivo"),
        ("exclusivo", "✨ Exclusivo"),
        ("limited", "⏳ Limitado"),
        ("limitado", "⏳ Limitado"),
    ]
    
    for pattern, emoji_text in patterns:
        if pattern in combined:
            logger.info(f"[TAG] ✅ Tag encontrado: {emoji_text}")
            return emoji_text
    
    logger.debug(f"[TAG] ❌ Sin tag de promoción")
    return ""


def get_rating_text(item: dict) -> str:
    """Formatea el texto de calificación."""
    try:
        rating = float(item.get("rating") or 0)
    except (ValueError, TypeError):
        rating = 0.0

    try:
        reviews = int(item.get("reviews_count") or 0)
    except (ValueError, TypeError):
        reviews = 0

    if rating <= 0:
        return ""

    rating_txt = f"⭐ <b>{rating:.1f}</b>"
    if reviews > 0:
        rating_txt += f" ({reviews:,} opiniones)"

    return rating_txt


def calculate_discount_percentage(original_price: float, final_price: float) -> int:
    """Calcula el porcentaje de descuento."""
    if original_price <= 0 or final_price <= 0:
        return 0
    if final_price >= original_price:
        return 0
    
    pct = (original_price - final_price) / original_price * 100
    return int(round(pct))


def format_price_line(original_price: float, final_price: float) -> str:
    """Formatea la línea de precios."""
    before = fmt_money(original_price)
    after = fmt_money(final_price)
    return f"🛒 Antes: <s>{before}</s> - 💳 Ahora: <b>{after}</b>"


def caption(it, disc, link_final: str):
    """Genera el caption para publicar en Telegram."""
    
    # ✅ PASO 1: Extraer datos básicos
    raw_title = (it.get("title") or "")[:140]
    title = escape(raw_title)
    
    # ✅ PASO 2: Obtener emoji
    emoji = get_emoji_for_product(raw_title)
    
    # ✅ PASO 3: Obtener tag de promoción (mejorado)
    promo_tag = get_promo_tag(it)
    
    # ✅ PASO 4: Obtener rating
    rating_txt = get_rating_text(it)
    
    # ✅ PASO 5: Calcular descuento
    try:
        original_price = float(it.get("original_price") or 0)
        final_price = float(it.get("price_final") or it.get("price") or 0)
    except (ValueError, TypeError):
        original_price = 0
        final_price = 0
    
    discount_pct = calculate_discount_percentage(original_price, final_price)
    
    # ✅ PASO 6: Procesar cupón
    raw_coupon = it.get("coupon_text") or ""
    coupon_clean = _normalize_coupon_text_generic(raw_coupon)
    coupon = escape(coupon_clean) if coupon_clean else ""
    
    # ✅ PASO 7: Construir líneas
    lines = []
    
    # Línea 1: Emoji + Título
    lines.append(f"{emoji} <b>{title}</b>")
    
    # Línea 2: Tag + Rating
    line2_parts = []
    if promo_tag:
        line2_parts.append(promo_tag)
    if rating_txt:
        line2_parts.append(rating_txt)
    if line2_parts:
        lines.append("  ".join(line2_parts))
    
    # Línea 3: Descuento + Cupón
    if discount_pct > 0 and coupon:
        lines.append(f"🔥 Descuento: {discount_pct}% + 🎟️ Cupón: <b>{coupon}</b>")
    elif discount_pct > 0:
        lines.append(f"🔥 Descuento: {discount_pct}%")
    
    # Línea 4: Precios
    if original_price > 0 and final_price > 0:
        lines.append(format_price_line(original_price, final_price))
    
    # Línea 5: Link
    if link_final:
        safe_link = escape(link_final, quote=True)
        lines.append(f'👉 <a href="{safe_link}">Ver oferta</a>')
    
    # ✅ PASO 8: Retornar
    result = "\n".join(lines)
    logger.debug(f"[CAPTION] Generado:\n{result[:100]}...")
    return result

# ============================
# 🔍 UTILIDADES
# ============================

def canonical_id(it: dict) -> str:
    """Extrae ID canónico del producto."""
    url = it.get("permalink") or ""
    if not url:
        return it.get("id", "")
    parts = urlsplit(url)
    base = parts.scheme + "://" + parts.netloc + parts.path
    return base or it.get("id", "")


def within_active_window() -> bool:
    """Verifica si está en horario activo."""
    start_h = get_env_int("ACTIVE_HOUR_START", 8)
    end_h = get_env_int("ACTIVE_HOUR_END", 23)

    now = datetime.datetime.now()
    return start_h <= now.hour < end_h


def interactive_sleep(seconds: int):
    """Espera interactiva (presionar 's' para saltar)."""
    if seconds <= 0:
        return

    try:
        import msvcrt
    except ImportError:
        time.sleep(seconds)
        return

    logger.info(f"Esperando {seconds} segundos. Presiona 's' para saltar.")
    remaining = seconds
    while remaining > 0:
        print(f"\r[WAIT] {remaining:3d}s restantes... ", end="", flush=True)
        start = time.time()
        while time.time() - start < 1:
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                if ch in (b"s", b"S"):
                    logger.info("Espera saltada por usuario")
                    return
            time.sleep(0.1)
        remaining -= 1
    logger.info("Espera completada")


def get_product_image(it: dict) -> str:
    """Obtiene la URL de imagen del producto."""
    def norm(u: str) -> str:
        if not u:
            return ""
        u = u.strip()
        if u.startswith("data:"):
            return ""
        if u.startswith("//"):
            u = "https:" + u
        return u

    for key in ("image_url", "thumbnail", "thumbnail_url", "secure_thumbnail", "image"):
        val = it.get(key)
        if isinstance(val, str):
            url = norm(val)
            if url:
                return url

    return ""

# ============================
# 🚀 LOOP PRINCIPAL
# ============================

def run():
    """Ejecuta el ciclo principal del bot."""
    load_dotenv()
    init_database()
    
    # ✅ Inicializar caché de productos
    init_title_cache()
    logger.info("✅ Caché de productos inicializado")
    
    # ✅ Contar errores
    error_count = 0

    if not within_active_window():
        now = datetime.datetime.now()
        logger.info(f"Fuera de horario activo ({now.strftime('%H:%M')}). No publico.")
        return

    # Configuración
    min_disc = get_env_float("MIN_DISCOUNT", 0.40)
    top_n = get_env_int("TOP_N", 10)
    post_interval = get_env_int("POST_INTERVAL_SECONDS", 300)
    pages = get_env_int("PAGES", 20)
    low_thr = get_env_float("LOW_PRICE_THRESHOLD", 1000.0)
    high_thr = get_env_float("HIGH_PRICE_THRESHOLD", 7000.0)

    if post_interval < 30:
        logger.warning(f"POST_INTERVAL={post_interval}s es muy rápido. Ajustando a 60s")
        post_interval = 60

    logger.info(
        f"MIN_DISCOUNT={int(min_disc*100)}%, TOP_N={top_n}, PAGES={pages}, "
        f"POST_INTERVAL={post_interval}s, LOW_THR=${low_thr}, HIGH_THR=${high_thr}"
    )

    # 1) Scraping
    items = fetch_offers(pages=pages)
    logger.info(f"Fetched: {len(items)} items")

    # 1.1) Bloqueo temprano
    items = [it for it in items if not should_block(it)]
    logger.info(f"After block filter: {len(items)} items")

    # 2) Validación y scoring
    scored = []
    all_scored = []

    for it in items:
        if not is_valid_item(it):
            continue

        s, d = score_item(it)
        if s < 0:
            continue

        all_scored.append((s, d, it))

        if d >= min_disc:
            scored.append((s, d, it))
    
    # ✅ Validar descuentos reales
    scored_filtered = []
    for s, d, it in scored:
        price_history = it.get("price_history")
        if is_discount_real(it, price_history):
            scored_filtered.append((s, d, it))
        else:
            logger.info(f"Descuento sospechoso detectado: {it.get('title')}")
    
    scored = scored_filtered
    
    if not scored:
        logger.warning("No hay descuentos validados como REALES")
        scored = [(s, d, it) for s, d, it in all_scored if d >= max(min_disc - 0.10, 0.20)]

    if not scored:
        if not all_scored:
            logger.error("Eligible: 0 items")
            return

        fallback_min = max(min_disc - 0.10, 0.20)
        logger.warning(f"Usando umbral de fallback: >= {int(fallback_min * 100)}%")

        scored_fallback = []
        for s, d, it in all_scored:
            if d >= fallback_min:
                price_history = it.get("price_history")
                if is_discount_real(it, price_history):
                    scored_fallback.append((s, d, it))
        
        scored = scored_fallback if scored_fallback else all_scored[:top_n]

    scored.sort(reverse=True, key=lambda x: x[0])

    # 2.1) Mezcla por precio
    bucket_low = [it for it in scored if float(it[2].get("price") or 0) <= low_thr]
    bucket_mid = [it for it in scored if low_thr < float(it[2].get("price") or 0) < high_thr]
    bucket_high = [it for it in scored if float(it[2].get("price") or 0) >= high_thr]

    logger.debug(f"Buckets: low={len(bucket_low)}, mid={len(bucket_mid)}, high={len(bucket_high)}")

    from itertools import cycle, islice
    buckets = [bucket_high, bucket_low, bucket_mid]
    try:
        mixed = list(islice(
            cycle((item for bucket in buckets if bucket for item in bucket)),
            len(scored)
        ))
    except:
        mixed = scored

    scored = mixed
    logger.info(f"Eligible: {len(scored)} items")

    if len(scored) < 5:
        from src.alerts import send_warning
        send_warning("Pocas ofertas elegibles", f"Solo {len(scored)} productos")

    # 3) Publicación
    pushed = 0
    already_pushed_links = set()
    already_pushed_titles = set()  # ✅ SEGUNDA CAPA DE PROTECCIÓN

    for s, d, it in scored:
        if pushed >= top_n:
            break

        if should_block(it):
            logger.debug(f"Bloqueado: {it.get('title')}")
            continue

        # ✅ Cache mejorado por TÍTULO + LINK BASE (sin query params)
        title = (it.get("title") or "").strip()
        link = (it.get("permalink") or "").strip()

        if not title or not link:
            logger.warning("Producto sin título o link, saltando")
            continue

        # ✅ Normalizar link (quitar parámetros de búsqueda)
        parsed = urlparse(link)
        link_base = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

        # ✅ Crear clave única más robusta (título + ID del producto)
        product_id_match = re.search(r'MLM-?\d+', link)
        product_id = product_id_match.group(0) if product_id_match else ""
        cache_key = f"{title.lower()}_{product_id}"

        # ✅ Evitar duplicados en ESTE ciclo (usar clave compuesta)
        if cache_key in already_pushed_links:
            logger.debug(f"Producto ya publicado en este ciclo (por clave): {title[:50]}")
            continue

        # ✅ Evitar duplicados por título exacto en este ciclo
        title_lower = title.lower()
        if title_lower in already_pushed_titles:
            logger.debug(f"Título ya publicado en este ciclo: {title[:50]}")
            continue

        # Verificar si el PRODUCTO ya fue visto en ciclos anteriores
        if is_product_seen(title, link_base):
            logger.debug(f"Producto exacto ya visto en ciclos anteriores: {title[:50]}")
            continue

        # Es nuevo, agregarlo al caché
        add_product_to_cache(title, link_base)

        try:
            it = enrich_item(it)
        except Exception as e:
            error_count += 1
            logger.error(f"Error enriqueciendo item: {e}")
            
            if error_count > 5:
                from src.alerts import send_warning
                send_warning("Muchos errores", f"Error: {str(e)[:200]}")
            continue

        if should_block(it):
            logger.debug(f"Bloqueado post-enrich: {it.get('title')}")
            continue

        if is_low_quality(it):
            logger.debug(f"Baja calidad: {it.get('title')}")
            continue

        permalink = it.get("permalink", "")

        # ✅ BLINDADO: Link de afiliado SEC o rechazar
        final_link = None
        try:
            logger.debug(f"[AFILIADO] Intentando generar para: {permalink[:60]}")
            aff = get_or_create_affiliate_url(permalink)
            
            # ✅ VALIDACIÓN: Solo acepta links SEC
            if aff and aff.startswith("https://mercadolibre.com/sec/"):
                final_link = aff
                logger.info(f"✅ Link SEC válido: {aff[:60]}")
            elif aff and aff == permalink:
                logger.warning(f"⚠️ Retornó URL original, rechazando")
                final_link = None
            elif aff:
                logger.error(f"❌ Link no es SEC válido: {aff}")
                final_link = None
            else:
                logger.error(f"❌ get_or_create_affiliate_url retornó None")
                final_link = None
                
        except Exception as e:
            logger.error(f"❌ Error generando afiliado: {e}")
            final_link = None

        # ✅ VALIDACIÓN FINAL: Rechazar si no tiene link SEC
        if not final_link or not final_link.startswith("https://mercadolibre.com/sec/"):
            logger.error(f"🚫 RECHAZANDO: Sin link SEC válido para {title[:50]}")
            continue

        cap = caption(it, d, final_link)
        photo = get_product_image(it)

        ok = False
        if photo:
            ok = post_telegram_photo(photo, cap)
            if not ok:
                logger.warning("post_telegram_photo falló, intentando solo texto")
        if not ok:
            ok = post_telegram(cap)

        if ok:
            pushed += 1
            # ✅ CORREGIDO: Agregar tanto cache_key como title_lower
            already_pushed_links.add(cache_key)
            already_pushed_titles.add(title_lower)
            add_published_offer(it, d, final_link)
            logger.info(f"✅ Publicada oferta #{pushed}: {title[:50]}")

            if pushed < top_n and post_interval > 0:
                interactive_sleep(post_interval)
        else:
            logger.error("No se pudo publicar la oferta")

    print_stats()
    logger.info(f"Total publicadas: {pushed} items")

    if pushed == 0:
        from src.alerts import send_warning
        send_warning("Sin ofertas", "No se publicó nada en este ciclo")

try:
    from dashboard_generator import generate_dashboard
    generate_dashboard()
    logger.info("📊 Dashboard actualizado")
except Exception as e:
    logger.error(f"Error actualizando dashboard: {e}")


if __name__ == "__main__":
    logger.info("🚀 Iniciando PromoAdictos...")
    
    import time
    from src.alerts import send_error, send_success
    
    start_time = time.time()
    
    try:
        run()
        duration = (time.time() - start_time) / 60
        send_success(
            "Bot ejecutado exitosamente",
            f"Duración: {duration:.1f} minutos"
        )
    except Exception as e:
        error_msg = str(e)[:500]
        logger.error(f"Error crítico: {error_msg}")
        send_error("Error crítico en el bot", f"<code>{error_msg}</code>")
        raise