# -*- coding: utf-8 -*-
"""
offers_fetcher.py - VERSIÓN FINAL CON PLAYWRIGHT

Scrapea las ofertas de Mercado Libre usando Playwright (navegador real).

VENTAJAS:
  ✅ Evita CAPTCHA (navegador real, no requests)
  ✅ Renderiza JavaScript completamente
  ✅ Parece usuario real
  ✅ Funciona con ML bloqueador

DESVENTAJAS:
  ❌ Más lento (~2-3 min por página)
  ❌ Consume más recursos (RAM/CPU)

CONFIGURACIÓN (.env):
  MIN_PRICE=300
  MAX_PRICE=20000
  PAGES=5
  HEADLESS=1  (0=mostrar ventana, 1=oculta)
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
import os
import time
import random
import re

from playwright.sync_api import sync_playwright, Page, BrowserContext
from bs4 import BeautifulSoup


# ====================================================
# CONFIGURACIÓN
# ====================================================

MIN_PRICE = float(os.getenv("MIN_PRICE", "300") or 300)
MAX_PRICE = float(os.getenv("MAX_PRICE", "20000") or 20000)
HEADLESS = int(os.getenv("HEADLESS", "1") or 1) == 1

print(f"[CONFIG] MIN_PRICE={MIN_PRICE}, MAX_PRICE={MAX_PRICE}, HEADLESS={HEADLESS}")


# ====================================================
# FUNCIONES AUXILIARES
# ====================================================

def _wait_for_offers(page: Page, timeout: int = 30000) -> bool:
    """
    Esperar a que carguen las ofertas en la página.
    
    Parámetros:
        page: página de Playwright
        timeout: ms máximo a esperar
    
    Retorna:
        True si cargaron, False si timeout
    """
    try:
        # Esperar a que aparezcan cards
        page.wait_for_selector(
            "li.poly-card, div.poly-card, div.promotion-item",
            timeout=timeout
        )
        print("[WAIT] ✅ Ofertas cargadas")
        return True
    except Exception as e:
        print(f"[WAIT] ❌ Timeout esperando ofertas: {e}")
        return False


def _scroll_page(page: Page, scrolls: int = 3) -> None:
    """
    Hacer scroll en la página para cargar lazy-load.
    
    Parámetros:
        page: página de Playwright
        scrolls: número de scrolls a hacer
    """
    print(f"[SCROLL] Haciendo {scrolls} scrolls...")
    
    for i in range(scrolls):
        page.mouse.wheel(0, 1500)  # Scroll down 1500px
        time.sleep(random.uniform(0.5, 1.0))
    
    print("[SCROLL] ✅ Completado")


def _check_for_captcha(page: Page) -> bool:
    """
    Detectar si hay CAPTCHA en la página.
    
    Retorna:
        True si hay CAPTCHA, False si no
    """
    try:
        html = page.content()
        html_lower = html.lower()
        
        captcha_indicators = [
            "captcha",
            "recaptcha",
            "hcaptcha",
            "verify",
            "verificar",
            "robot",
            "comportamiento inusual",
        ]
        
        for indicator in captcha_indicators:
            if indicator in html_lower:
                print(f"[CAPTCHA] ⚠️  Detectado: '{indicator}'")
                return True
        
        return False
    
    except Exception as e:
        print(f"[CAPTCHA] Error checking: {e}")
        return False


def _extract_offers_from_html(html: str, page_num: int) -> tuple[List[Dict[str, Any]], int]:
    """
    Extraer ofertas del HTML renderizado.
    
    Parámetros:
        html: contenido HTML de la página
        page_num: número de página (para logging)
    
    Retorna:
        (lista de items, count de items válidos)
    """
    
    items = []
    
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception as e:
        print(f"[PARSE] ❌ Error parseando HTML: {e}")
        return items, 0
    
    # Buscar cards
    cards = soup.select("li.poly-card, div.poly-card, div.promotion-item")
    print(f"[CARDS] 📦 {len(cards)} cards encontradas")
    
    if len(cards) == 0:
        print("[CARDS] ⚠️  No se encontraron cards")
        return items, 0
    
    # Procesar cada card
    valid_count = 0
    
    for card_idx, card in enumerate(cards, 1):
        try:
            # ===== ID =====
            cid = card.get("data-item-id") or card.get("id") or ""
            cid = cid.strip()
            
            # ===== TÍTULO =====
            title_el = (
                card.select_one("h2, h3, .poly-card__title, .promotion-item__title")
            )
            title = (title_el.get_text(strip=True) if title_el else "").strip()
            
            if not title or len(title) < 5:
                continue
            
            # ===== LINK =====
            link_el = card.select_one("a")
            permalink = ""
            if link_el and link_el.get("href"):
                permalink = link_el["href"].split("#")[0]
            
            # ===== IMAGEN =====
            thumb_el = (
                card.select_one("img") or card.select_one("figure img")
            )
            thumbnail = ""
            if thumb_el:
                thumbnail = thumb_el.get("src") or thumb_el.get("data-src") or ""
            
            # ===== PRECIO ACTUAL =====
            price_val = None
            
            # Intento 1: precio no tachado
            cand_price = card.select_one(
                ".andes-money-amount:not(.andes-money-amount--previous) "
                ".andes-money-amount__fraction"
            )
            if cand_price and cand_price.get_text(strip=True):
                txt = cand_price.get_text(strip=True)
                txt = txt.replace(".", "").replace(",", "")
                try:
                    price_val = float(txt)
                except Exception:
                    price_val = None
            
            # Intento 2: cualquier fraction
            if price_val is None:
                cand_price = card.select_one(".andes-money-amount__fraction")
                if cand_price and cand_price.get_text(strip=True):
                    txt = cand_price.get_text(strip=True)
                    txt = txt.replace(".", "").replace(",", "")
                    try:
                        price_val = float(txt)
                    except Exception:
                        price_val = None
            
            # ===== PRECIO ORIGINAL =====
            original_val = None
            prev_el = card.select_one(
                ".andes-money-amount--previous .andes-money-amount__fraction"
            )
            if prev_el and prev_el.get_text(strip=True):
                txt = prev_el.get_text(strip=True)
                txt = txt.replace(".", "").replace(",", "")
                try:
                    original_val = float(txt)
                except Exception:
                    original_val = None
            
            # ===== DESCUENTO (%) =====
            discount_el = card.select_one(
                ".andes-money-amount__discount, .promotion-item__discount"
            )
            discount_text = (
                discount_el.get_text(strip=True) if discount_el else ""
            )
            
            # ===== PROMO TAG =====
            promo_el = card.select_one(
                ".poly-component__badge, .promotion-item__badge, .poly-badge, "
                ".andes-badge, .andes-badge__text, .ui-search-item__highlight-label__text, "
                ".ui-search-badge__highlight, .ui-search-item__group__element"  # Agregar más selectores
            )
            promo_tag = promo_el.get_text(strip=True) if promo_el else ""

            # Buscar específicamente ofertas relámpago
            if not promo_tag:
                # Buscar en todo el card
                card_text = card.get_text(" ", strip=True).lower()
                if "relámpago" in card_text or "relampago" in card_text:
                    promo_tag = "Oferta Relámpago"
                elif "más vendido" in card_text or "mas vendido" in card_text:
                    promo_tag = "Más Vendido"

            print(f"[SCRAPING_TAG] Producto: {title[:30]}... Tag: {promo_tag}")
            
            if not promo_tag:
                mv = card.find(
                    string=lambda t: t and "más vendido" in t.lower()
                )
                if mv:
                    promo_tag = "Más Vendido"
            
            # ===== CUPÓN =====
            coupon_el = card.find(
                string=lambda t: t and "cupón" in t.lower()
            )
            coupon_text = coupon_el.strip() if coupon_el else ""
            
            # ===== TIME LIMIT =====
            time_limit_el = card.find(
                string=lambda t: t and ("Termina en" in t or "termina en" in t.lower())
            )
            time_limit_label = time_limit_el.strip() if time_limit_el else ""
            
            # ===== SHIPPING TAGS =====
            shipping_tags = []
            full_el = card.find(
                string=lambda t: t and "FULL" in t.upper()
            )
            if full_el:
                shipping_tags.append("fulfillment")
            
            # ===== DEDUCIR ORIGINAL SI FALTA =====
            if original_val is None and price_val is not None and discount_text:
                m = re.search(r"(\d{1,3})\s*%?", discount_text)
                if m:
                    try:
                        pct = int(m.group(1))
                    except Exception:
                        pct = None
                    if pct and 0 < pct < 100:
                        original_val = price_val / (1.0 - pct / 100.0)
            
            # ===== VALIDACIONES =====
            if price_val is None or original_val is None:
                continue
            
            price_val = float(price_val)
            original_val = float(original_val)
            
            if original_val <= 0 or price_val <= 0:
                continue
            
            if original_val <= price_val:
                continue  # Sin descuento real
            
            # ✅ ITEM VÁLIDO
            item = {
                "id": cid,
                "title": title,
                "price": price_val,
                "original_price": original_val,
                "permalink": permalink,
                "thumbnail": thumbnail,
                "shipping": {"tags": shipping_tags},
                "promo_tag": promo_tag,
                "coupon_text": coupon_text,
                "time_limit_label": time_limit_label,
            }
            
            items.append(item)
            valid_count += 1
            
            print(f"  ✓ {valid_count}. {title[:50]}... (${price_val:.0f})")
        
        except Exception as e:
            print(f"  ❌ Card {card_idx}: {e}")
            continue
    
    return items, valid_count


# ====================================================
# SCRAPING PRINCIPAL CON PLAYWRIGHT
# ====================================================

def fetch_offers(pages: int = 3) -> List[Dict[str, Any]]:
    """
    Scrapea ofertas de Mercado Libre usando Playwright.
    
    Parámetros:
        pages: número de páginas a scrapear
    
    Retorna:
        Lista de ofertas (diccionarios)
    """
    
    base_url = "https://www.mercadolibre.com.mx/ofertas"
    price_segment = f"price={MIN_PRICE:.1f}-{MAX_PRICE:.1f}"
    
    all_items = {}  # Dedup por key
    
    print(f"\n{'='*60}")
    print(f"[PLAYWRIGHT] Iniciando scraping de {pages} páginas")
    print(f"[PLAYWRIGHT] Rango de precio: ${MIN_PRICE:.0f} - ${MAX_PRICE:.0f}")
    print(f"{'='*60}\n")
    
    with sync_playwright() as p:
        # Lanzar navegador
        print("[BROWSER] Lanzando navegador Chromium...")
        
        browser = p.chromium.launch(
            headless=HEADLESS,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-gpu",
            ]
        )
        
        # Crear contexto (simular usuario)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
        )
        
        # Agregar cookies para parecer usuario recurrente
        context.add_cookies([
            {
                "name": "visited_offers",
                "value": "1",
                "domain": "mercadolibre.com.mx",
                "path": "/",
            }
        ])
        
        print("[BROWSER] ✅ Navegador iniciado\n")
        
        # Scraping por página
        for page_num in range(1, pages + 1):
            print(f"\n{'='*60}")
            print(f"[PAGE {page_num}/{pages}] Iniciando...")
            print(f"{'='*60}\n")
            
            # Construir URL
            if page_num == 1:
                url = (
                    f"{base_url}?{price_segment}"
                    "#filter_applied=price&filter_position=5&origin=qcat"
                )
            else:
                url = (
                    f"{base_url}?{price_segment}&page={page_num}"
                    "#filter_applied=price&filter_position=5&origin=qcat"
                )
            
            try:
                # Crear página
                page = context.new_page()
                
                print(f"[NAV] Navegando a: {url[:80]}...")
                
                # Navegar
                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=60000
                )
                
                print("[NAV] ✅ Página cargada")
                
                # Esperar ofertas
                if not _wait_for_offers(page, timeout=30000):
                    print(f"[PAGE {page_num}] ❌ Timeout esperando ofertas")
                    page.close()
                    continue
                
                # Scroll para lazy-load
                _scroll_page(page, scrolls=3)
                
                # Verificar CAPTCHA
                if _check_for_captcha(page):
                    print(f"[PAGE {page_num}] ⚠️  CAPTCHA detectado, esperando...")
                    print("[PAUSE] Por favor completa el CAPTCHA en la ventana del navegador")
                    time.sleep(15)  # Dar tiempo para completar CAPTCHA manualmente
                
                # Obtener HTML renderizado
                html = page.content()
                print(f"[HTML] Tamaño: {len(html):,} bytes")
                
                # Extraer ofertas
                items, count = _extract_offers_from_html(html, page_num)
                
                # Agregar a todos (dedup)
                for item in items:
                    key = item.get("permalink") or item.get("id") or item.get("title")
                    if key and key not in all_items:
                        all_items[key] = item
                
                print(f"[PAGE {page_num}] ✅ {count} items válidos")
                
                page.close()
                
            except Exception as e:
                print(f"[PAGE {page_num}] ❌ Error: {e}")
                try:
                    page.close()
                except:
                    pass
                continue
            
            # Delay entre páginas
            if page_num < pages:
                wait = random.uniform(5, 10)
                print(f"\n[DELAY] Esperando {wait:.1f}s antes de siguiente página...")
                time.sleep(wait)
        
        # Cerrar navegador
        print("\n[BROWSER] Cerrando navegador...")
        browser.close()
    
    print(f"\n{'='*60}")
    print(f"[FETCH] ✅ Scraping completado")
    print(f"[FETCH] Total items únicos: {len(all_items)}")
    print(f"{'='*60}\n")
    
    return list(all_items.values())