# -*- coding: utf-8 -*-
"""
offers_fetcher.py - VERSIÓN ROBUSTA (FULL + SIN ACENTOS)
"""
from __future__ import annotations
from typing import List, Dict, Any
import os
import time
import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from src.logger import get_logger

log = get_logger("offers_fetcher")

# CONFIGURACIÓN
MIN_PRICE = float(os.getenv("MIN_PRICE", "300") or 300)
MAX_PRICE = float(os.getenv("MAX_PRICE", "20000") or 20000)

def _clean_price(text: str) -> float:
    if not text: return 0.0
    clean = text.replace("$", "").replace(" ", "").strip()
    clean = clean.replace(",", "") 
    try: return float(clean)
    except ValueError: return 0.0

def _extract_id_from_url(url: str) -> str:
    if not url: return ""
    match = re.search(r"(MLM-?\d+)", url)
    if match: return match.group(1).replace("-", "")
    return ""

def _parse_coupon_strict(card_soup) -> tuple[str, float, str]:
    c_text_found = ""
    selectors = [
        ".ui-vpp-coupons-awareness__checkbox-label", 
        ".poly-coupon", 
        ".ui-search-item__coupon",
        "span.andes-badge__content--green" 
    ]
    
    for sel in selectors:
        tags = card_soup.select(sel)
        for tag in tags:
            text = tag.get_text(" ", strip=True).upper()
            is_checkbox = "checkbox-label" in sel
            has_keyword = any(k in text for k in ["CUPÓN", "CUPON", "APLICAR"])
            
            if is_checkbox or has_keyword:
                if "ENVÍO" in text or "LLEGA" in text: continue
                c_text_found = text
                break
        if c_text_found: break

    if c_text_found:
        clean_txt = c_text_found.upper()
        for word in ["APLICAR", "CUPÓN", "CUPON", "DE REGALO", "DE DESCUENTO", "OFF"]:
            clean_txt = clean_txt.replace(word, "")
        clean_txt = clean_txt.strip()
        val = 0.0
        c_type = "fixed"
        m_pct = re.search(r"(\d+(?:\.\d+)?)%", c_text_found)
        if m_pct:
            val = float(m_pct.group(1))
            c_type = "percent"
            return f"🎟️ Cupón {int(val)}% OFF", val, c_type
        m_fixed = re.search(r"\$\s?([\d\.,]+)", clean_txt)
        if m_fixed:
            try:
                val = float(m_fixed.group(1).replace(",", ""))
                c_type = "fixed"
                return f"🎟️ Cupón -${int(val)}", val, c_type
            except: pass
    return "", 0.0, None

# Añadir esta función en offers_fetcher.py
def _normalize_text(text: str) -> str:
    """Elimina acentos y mayúsculas para comparación segura."""
    return text.upper().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
    
def _parse_html_offers(html: str) -> List[Dict[str, Any]]:
    items = []
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("li.ui-search-layout__item, div.ui-search-result__wrapper, div.poly-card, div.andes-card")
    
    for card in cards:
        try:
            title_tag = card.select_one(".poly-component__title, .ui-search-item__title, h2")
            link_tag = card.select_one("a.poly-component__title, a.ui-search-link, a")
            if not title_tag: continue
            
            title = title_tag.get_text(strip=True)
            permalink = link_tag.get("href", "").split("#")[0] if link_tag else ""
            if not permalink: continue
            
            cid = card.get("data-item-id") or _extract_id_from_url(permalink)

            curr_tag = card.select_one(".poly-price__current .andes-money-amount__fraction, .ui-search-price__second-line .andes-money-amount__fraction")
            price = _clean_price(curr_tag.get_text(strip=True)) if curr_tag else 0.0

            orig_tag = card.select_one(".andes-money-amount--previous .andes-money-amount__fraction, .ui-search-price__original-value .andes-money-amount__fraction")
            original_price = _clean_price(orig_tag.get_text(strip=True)) if orig_tag else 0.0

            if price <= 0: continue
            if original_price == 0: original_price = price

            img_tag = card.select_one("img")
            thumbnail = ""
            if img_tag:
                thumbnail = img_tag.get("data-src") or img_tag.get("src") or ""
                if "http" in thumbnail:
                    thumbnail = thumbnail.replace("I.jpg", "V.jpg").replace("_I.jpg", "_V.jpg")

            rating = 0.0
            reviews = 0
            rating_tag = card.select_one(".poly-reviews__rating, .ui-search-reviews__rating")
            if rating_tag:
                try: rating = float(rating_tag.get_text(strip=True))
                except: pass
            reviews_tag = card.select_one(".poly-reviews__total, .ui-search-reviews__amount")
            if reviews_tag:
                try: reviews = int(reviews_tag.get_text(strip=True).replace("(", "").replace(")", ""))
                except: pass

            # 5. TAGS DE OFERTA
            promo_tag = ""
            badges = card.select(".poly-component__highlight, .ui-search-item__highlight-label, .andes-badge__content")
            for b in badges:
                t_raw = b.get_text(strip=True).upper()
                t_norm = _normalize_text(t_raw) # <--- USAR NORMALIZACIÓN
                
                if "MAS VENDIDO" in t_norm: promo_tag = "🔥 Más Vendido"
                elif "DEL DIA" in t_norm: promo_tag = "⏰ Oferta del Día"
                elif "RELAMPAGO" in t_norm: promo_tag = "⚡ Oferta Relámpago" # <--- FIX: Detecta sin acento
                elif "IMPERDIBLE" in t_norm: promo_tag = "💎 Imperdible"
                elif "RECOMENDADO" in t_norm: promo_tag = "⭐ Recomendado"
                if promo_tag: break

            # DETECCIÓN DE FULL
            is_full = False
            # Detección por CSS/clases
            if card.select_one(".poly-component__shipped-from-fulfillment, .andes-icon--fulfillment, span.ui-search-item__fulfillment-label, .poly-component__shipping-badge"):
                is_full = True
            # Detección por texto (usando normalización)
            elif "FULL" in _normalize_text(card.get_text()): 
                is_full = True
            
            # Concatenación de FULL
            if is_full:
                if promo_tag:
                    if "FULL" not in promo_tag.upper():
                        promo_tag = f"{promo_tag} | ⚡ FULL"
                else:
                    promo_tag = "⚡ FULL"
                   
            c_text, c_val, c_type = _parse_coupon_strict(card)

            item = {
                "id": cid,
                "title": title,
                "price": price,
                "original_price": original_price,
                "permalink": permalink,
                "thumbnail": thumbnail,
                "promo_tag": promo_tag,
                "coupon_text": c_text, 
                "coupon_value": c_val,
                "rating": rating,
                "reviews_count": reviews
            }
            items.append(item)
        except Exception: continue
    return items

def fetch_offers(pages: int = 3) -> List[Dict[str, Any]]:
    print(f"\n[PLAYWRIGHT] Iniciando scraping de {pages} páginas")
    all_items = {}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            page = context.new_page()
            base_url = "https://www.mercadolibre.com.mx/ofertas"
            #?promotion_type=lightning&shipping=fulfillment#filter_applied=promotion_type&filter_position=2&origin=qcat
            
            for page_num in range(1, pages + 1):
                url = f"{base_url}?price={MIN_PRICE}-{MAX_PRICE}&page={page_num}"
                print(f"[PAGE {page_num}] 📍 Navegando...")
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    for _ in range(5): 
                        page.mouse.wheel(0, 1000)
                        time.sleep(0.5)
                    html = page.content()
                    items = _parse_html_offers(html)
                    new_c = 0
                    for it in items:
                        if it["permalink"] not in all_items:
                            all_items[it["permalink"]] = it
                            new_c += 1
                    print(f"[PAGE {page_num}] ✅ {len(items)} items ({new_c} nuevos)")
                except Exception as e: print(f"[PAGE {page_num}] ❌ Error: {e}")
            browser.close()
    except Exception as e:
        print(f"[PLAYWRIGHT] ❌ Error crítico: {e}")
        return []
    results = list(all_items.values())
    print(f"[PLAYWRIGHT] 🏁 Total: {len(results)} ofertas.")
    return results