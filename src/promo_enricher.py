# -*- coding: utf-8 -*-
"""
promo_enricher.py

Enriquece cada producto de Mercado Libre con info extra:
- Imagen de alta calidad
- Tag de oferta real (Relámpago / Imperdible / Oferta del Día / Más Vendido / FULL)
- Tags de calidad: Top Valoración / Descuento Alto / Muy Vendido (sintéticos)
- Cupón y precio final estimado
- Breadcrumb / categoría y comisión estimada
- Calidad: rating, número de opiniones, vendidos
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List, Tuple
import re
import time
import random
import json

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36 PromoAdictosBot"
    ),
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
}

# ----------------------------------------------------------------------
# Requests seguros
# ----------------------------------------------------------------------


def _safe_get(url: str, max_retries: int = 3, timeout: int = 15) -> Optional[str]:
    if not url:
        return None

    for attempt in range(1, max_retries + 1):
        try:
            time.sleep(random.uniform(0.5, 1.0))
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
            if resp.status_code == 200:
                return resp.text
            else:
                print(f"[ENRICH] HTTP {resp.status_code} para {url}")
        except Exception as e:
            print(f"[ENRICH] Error request {url} (intento {attempt}/{max_retries}): {e}")

    return None


def _html_to_text(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    return " ".join(soup.get_text(" ", strip=True).split())


# ----------------------------------------------------------------------
# Tag de oferta (oficial)
# ----------------------------------------------------------------------


def _extract_tags_from_json(soup: BeautifulSoup) -> List[str]:
    """Escanea scripts JSON internos buscando textos de tag conocidos."""
    patterns = [
        "oferta relámpago",
        "oferta relampago",
        "oferta del día",
        "oferta del dia",
        "oferta imperdible",
        "más vendido",
        "mas vendido",
    ]
    found: List[str] = []
    try:
        for script in soup.find_all("script"):
            if not script.string:
                continue
            txt = script.string.lower()
            for p in patterns:
                if p in txt:
                    found.append(p)
    except Exception:
        pass
    return found


def _normalize_official_tag(text: str) -> Optional[str]:
    if not text:
        return None
    t = text.strip().lower()
    if "relampago" in t or "relámpago" in t:
        return "Oferta Relámpago"
    if "imperdible" in t:
        return "Oferta Imperdible"
    if "oferta del día" in t or "oferta del dia" in t:
        return "Oferta del Día"
    if "más vendido" in t or "mas vendido" in t:
        return "Más Vendido"
    if "full" in t:
        return "FULL"
    return None


def _choose_best_official_tag(
    html_text: str,
    existing: Optional[str],
    soup: Optional[BeautifulSoup] = None,
) -> Optional[str]:
    """
    Devuelve el mejor tag OFICIAL con prioridad mejorada
    """
    candidates: set[str] = set()

    # 1) Tag que ya trae el item desde el scraping
    base = _normalize_official_tag(existing or "")
    if base:
        candidates.add(base)

    # 2) Buscar en el HTML completo
    combined = html_text or ""
    if soup is not None:
        try:
            combined += " " + soup.get_text(" ", strip=True)
        except Exception:
            pass
    
    low = combined.lower()

    # 3) Buscar patrones de tags con PRIORIDAD
    # IMPORTANTE: Buscar primero los más específicos
    priority_patterns = [
        # Ofertas relámpago (máxima prioridad)
        ("oferta relámpago", "Oferta Relámpago"),
        ("oferta relampago", "Oferta Relámpago"),
        ("oferta relàmpago", "Oferta Relámpago"),
        ("deal relámpago", "Oferta Relámpago"),
        ("flash deal", "Oferta Relámpago"),
        ("⚡", "Oferta Relámpago"),  # Si hay emoji de rayo
        
        # Ofertas imperdibles
        ("oferta imperdible", "Oferta Imperdible"),
        ("imperdible", "Oferta Imperdible"),
        
        # Ofertas del día
        ("oferta del día", "Oferta del Día"),
        ("oferta del dia", "Oferta del Día"),
        ("deal of the day", "Oferta del Día"),
        
        # Más vendido
        ("más vendido", "Más Vendido"),
        ("mas vendido", "Más Vendido"),
        ("best seller", "Más Vendido"),
        ("bestseller", "Más Vendido"),
        
        # FULL
        ("full", "FULL"),
    ]
    
    for pattern, tag in priority_patterns:
        if pattern in low:
            candidates.add(tag)

    # 4) Buscar en elementos específicos del DOM
    if soup is not None:
        # Buscar en badges y etiquetas
        badge_selectors = [
            '.ui-pdp-badge__text',
            '.ui-pdp-promotions-pill',
            '.ui-pdp-promotions-pill-label__text',
            '.andes-badge__text',
            '.ui-pdp-highlights',
            '.ui-pdp-highlight__label',
            '[class*="badge"]',
            '[class*="promotion"]',
            '[class*="deal"]',
            '[class*="offer"]'
        ]
        
        for selector in badge_selectors:
            try:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    if text:
                        norm = _normalize_official_tag(text)
                        if norm:
                            candidates.add(norm)
                        # También buscar directamente
                        text_lower = text.lower()
                        for pattern, tag in priority_patterns:
                            if pattern in text_lower:
                                candidates.add(tag)
            except Exception:
                pass

        # Buscar en meta tags
        try:
            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                content = meta.get('content', '')
                if content:
                    for pattern, tag in priority_patterns:
                        if pattern in content.lower():
                            candidates.add(tag)
        except Exception:
            pass

    # 5) Si no hay candidatos, retornar None
    if not candidates:
        return None

    # 6) Priorizar según importancia
    priority_order = [
        "Oferta Relámpago",  # MÁXIMA PRIORIDAD
        "Oferta Imperdible",
        "Oferta del Día",
        "Más Vendido",
        "FULL",
    ]
    
    for tag in priority_order:
        if tag in candidates:
            print(f"[TAG] ✅ Detectado tag oficial: {tag}")
            return tag

    # Si hay algún candidato no priorizado, devolverlo
    return next(iter(candidates)) if candidates else None


# ----------------------------------------------------------------------
# Cupón / precio final
# ----------------------------------------------------------------------


def _extract_coupon_snippet(html: str) -> Optional[str]:
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    text = " ".join(soup.get_text(" ", strip=True).split())
    low = text.lower()
    if "cupón" not in low and "cupon" not in low:
        return None

    idx = low.find("cupón")
    if idx == -1:
        idx = low.find("cupon")
    if idx == -1:
        return None

    start = max(0, idx - 50)
    end = min(len(text), idx + 120)
    return text[start:end].strip()


MONEY_RE = re.compile(r"\$?\s*([\d,.]+)")


def _guess_final_price(
    price_from_card: Optional[float],
    coupon_snippet: Optional[str],
    html_text: str,
) -> Tuple[Optional[float], Optional[str]]:
    if price_from_card is None or not coupon_snippet:
        return None, None

    low_coupon = coupon_snippet.lower()
    base = float(price_from_card)

    # 1) Descuento %
    m = re.search(r"(\d{1,3})\s*%?\s*off", low_coupon)
    if m:
        pct = int(m.group(1))
        if 0 < pct < 100:
            final = base * (1.0 - pct / 100.0)
            return final, f"{pct}% OFF"

    # 2) Descuento fijo "$XXX OFF"
    m = re.search(r"\$\s?([\d,.]+)\s*off", low_coupon)
    if m:
        val = float(m.group(1).replace(".", "").replace(",", ""))
        if 0 < val < base:
            final = base - val
            return final, f"${int(val):,} OFF".replace(",", ",")

    # 3) "$XXX de descuento"
    m = re.search(r"\$\s?([\d,.]+)", low_coupon)
    if m:
        val = float(m.group(1).replace(".", "").replace(",", ""))
        if 0 < val < base:
            final = base - val
            return final, f"${int(val):,} OFF".replace(",", ",")

    return None, None


# ----------------------------------------------------------------------
# Ventas / rating / opiniones
# ----------------------------------------------------------------------

SOLD_RE = re.compile(r"([\d.]+)\+?\s+vendid[oa]s?", re.IGNORECASE)


def _extract_sold_count(text: str) -> int:
    if not text:
        return 0
    m = SOLD_RE.search(text)
    if not m:
        return 0
    raw = m.group(1).replace("+", "").replace(".", "")
    try:
        return int(raw)
    except Exception:
        return 0


def _extract_rating(soup: BeautifulSoup) -> Optional[float]:
    tag = soup.find(attrs={"itemprop": "ratingValue"})
    if tag and tag.get("content"):
        try:
            return float(tag["content"])
        except Exception:
            pass

    span = soup.find("span", class_="ui-pdp-review__rating")
    if span and span.get_text(strip=True):
        try:
            return float(span.get_text(strip=True).replace(",", "."))
        except Exception:
            pass

    return None


def _extract_reviews_count(soup: BeautifulSoup) -> Optional[int]:
    tag = soup.find(attrs={"itemprop": "reviewCount"})
    if tag and tag.get("content"):
        try:
            return int(tag["content"])
        except Exception:
            pass

    txt = soup.get_text(" ", strip=True)
    m = re.search(r"(\d[\d.,]*)\s+opiniones", txt, flags=re.IGNORECASE)
    if m:
        raw = m.group(1).replace(".", "").replace(",", "")
        try:
            return int(raw)
        except Exception:
            pass

    return None


# ----------------------------------------------------------------------
# Imagen / breadcrumb / comisión
# ----------------------------------------------------------------------


def _normalize_url(u: str) -> str:
    if not u:
        return ""
    u = u.strip()
    if u.startswith("//"):
        u = "https:" + u
    return u


def _extract_main_image(soup: BeautifulSoup) -> Optional[str]:
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        return _normalize_url(og["content"])

    img = soup.select_one("img.ui-pdp-gallery__figure__image, img.ui-pdp-image")
    if img and img.get("src"):
        return _normalize_url(img.get("src"))

    for im in soup.find_all("img"):
        src = im.get("src") or im.get("data-src")
        if not src:
            continue
        src = _normalize_url(src)
        if "svg" in src.lower():
            continue
        return src

    return None


def _extract_breadcrumb(soup: BeautifulSoup) -> List[str]:
    crumbs: List[str] = []

    nav = soup.select_one("nav.ui-pdp-breadcrumb, nav.breadcrumb")
    if nav:
        for li in nav.find_all("li"):
            txt = li.get_text(" ", strip=True)
            if txt:
                crumbs.append(txt)
        if crumbs:
            return crumbs

    for li in soup.select('[itemprop="itemListElement"]'):
        txt = li.get_text(" ", strip=True)
        if txt:
            crumbs.append(txt)

    seen = set()
    unique: List[str] = []
    for t in crumbs:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique


def _infer_commission_from_category_label(label: str) -> Optional[float]:
    if not label:
        return None
    low = label.lower()

    if "alimentos" in low and "bebidas" in low:
        return 0.0

    if (
        "electrónica" in low
        or "electronica" in low
        or "videojuegos" in low
        or "consolas" in low
        or "televisores" in low
        or "celulares" in low
        or "computación" in low
        or "computacion" in low
    ):
        return 0.10

    if "hogar" in low or "muebles" in low or "jardín" in low or "jardin" in low:
        return 0.07

    if "moda" in low or "ropa" in low or "calzado" in low:
        return 0.08

    if "bebés" in low or "bebes" in low or "juguetes" in low:
        return 0.08

    if "herramientas" in low or "industriales" in low:
        return 0.08

    return 0.07


# ----------------------------------------------------------------------
# Enriquecer item
# ----------------------------------------------------------------------


def enrich_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Enriquece item con info extra"""
    enriched = dict(item)

    url = enriched.get("permalink") or enriched.get("url") or enriched.get("link")
    if not url:
        return enriched

    print(f"[ENRICH] Enriqueciendo {url}")
    html = _safe_get(url)
    if not html:
        return enriched

    soup = BeautifulSoup(html, "html.parser")
    plain_text = _html_to_text(html)

    # Imagen
    img = _extract_main_image(soup)
    if img:
        enriched["image_url"] = img
        enriched["photo_url"] = img

    # Breadcrumb / categoría
    crumbs = _extract_breadcrumb(soup)
    if crumbs:
        enriched["breadcrumb"] = crumbs
        enriched["category_label"] = " > ".join(crumbs)

    # Ventas / calidad
    sold = _extract_sold_count(plain_text)
    if sold:
        enriched["sold_quantity"] = sold

    rating = _extract_rating(soup)
    if rating is not None:
        enriched["rating"] = rating

    reviews = _extract_reviews_count(soup)
    if reviews is not None:
        enriched["reviews_count"] = reviews

    # ----------------- DESCUENTO PARA TAGS SINTÉTICOS -----------------
    def _to_float(x):
        try:
            return float(x)
        except Exception:
            return 0.0

    original_price = _to_float(enriched.get("original_price"))
    price_base = _to_float(enriched.get("price_base"))
    price_final = _to_float(enriched.get("price_final") or enriched.get("price"))

    pct_discount = 0
    ref_orig = original_price or price_base
    if ref_orig > 0 and price_final > 0 and price_final < ref_orig:
        pct_discount = int(round((ref_orig - price_final) / ref_orig * 100))

    # TAG OFICIAL - Con debug mejorado
    existing_tag = (
        enriched.get("promo_tag")
        or enriched.get("tag")
        or enriched.get("badge")
    )
    
    print(f"[TAG_DEBUG] Tag existente del scraping: {existing_tag}")
    
    # Buscar específicamente "oferta relámpago" en el HTML
    if "relámpago" in plain_text.lower() or "relampago" in plain_text.lower():
        print("[TAG_DEBUG] ⚡ Texto 'relámpago' encontrado en la página")
    
    official_tag = _choose_best_official_tag(plain_text, existing_tag, soup)
    
    print(f"[TAG_DEBUG] Tag oficial detectado: {official_tag}")

    # ----------------- TAGS SINTÉTICOS -----------------
    quality_tag = None
    discount_tag = None
    volume_tag = None

    if rating is not None and reviews is not None and rating >= 4.5 and reviews >= 200:
        quality_tag = "Top Valoración"

    if pct_discount >= 60:
        discount_tag = "Descuento Alto"

    if sold and sold >= 1000:
        volume_tag = "Muy Vendido"

    # ----------------- TAG FINAL PARA MOSTRAR -----------------
    final_tag = None
    secondary_tags: List[str] = []

    if official_tag:
        final_tag = official_tag
    else:
        # Sin tag oficial: usamos calidad / descuento / volumen
        if quality_tag:
            final_tag = quality_tag
        elif discount_tag:
            final_tag = discount_tag
        elif volume_tag:
            final_tag = volume_tag

        # Si aun así no hay y es FULL, usamos FULL
        if not final_tag and is_full:
            final_tag = "FULL"

    # armar lista de secundarios (sin duplicados y sin repetir el final)
    for t in [quality_tag, discount_tag, volume_tag]:
        if t and t != final_tag and t not in secondary_tags:
            secondary_tags.append(t)

    # Guardar en el item
    enriched["promo_tag_official"] = official_tag or ""
    enriched["promo_tag_quality"] = quality_tag or ""
    enriched["promo_tag_discount"] = discount_tag or ""
    enriched["promo_tag_volume"] = volume_tag or ""
    enriched["promo_tag_secondary"] = secondary_tags
    enriched["promo_tag_final"] = final_tag or ""

    # Para compatibilidad con el resto del código
    enriched["promo_tag"] = final_tag or ""
    enriched["tag"] = final_tag or ""
    if not enriched["promo_tag"] and is_full:
        enriched["promo_tag"] = "FULL"
        enriched["tag"] = "FULL"

    # Cupón y precio final
    coupon = _extract_coupon_snippet(html)
    if coupon:
        enriched["coupon_text"] = coupon
        val, coupon_label = _guess_final_price(
            enriched.get("price"),
            coupon,
            plain_text,
        )
        if val is not None:
            enriched["price_final"] = float(val)
            if coupon_label:
                enriched["coupon_text"] = coupon_label

    # Comisión estimada
    cat_label = enriched.get("category_label") or ""
    comm = _infer_commission_from_category_label(cat_label)
    if comm is not None:
        enriched["estimated_commission_rate"] = comm

    # ============= VALIDACIÓN DE DESCUENTO REAL =============
    from src.price_validator import extract_price_history_from_html, get_discount_confidence_score
    
    price_history = extract_price_history_from_html(html)
    if price_history:
        enriched["price_history"] = price_history
        print(f"[PRICE_HISTORY] Encontrado: {price_history}")
    
    # Calcular confianza en descuento
    confidence = get_discount_confidence_score(enriched, price_history)
    enriched["discount_confidence"] = confidence
    print(f"[DISCOUNT_CONFIDENCE] Score: {confidence:.0%}")
    
    return enriched
