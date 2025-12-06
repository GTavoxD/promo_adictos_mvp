# -*- coding: utf-8 -*-
"""
affiliate_runtime.py

Generador de links de afiliado para Mercado Libre BLINDADO.
Solo retorna links SEC válidos y funcionales.
"""

import csv
import time
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright, Page

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CSV_PATH = DATA_DIR / "affiliate_links.csv"
STATE_PATH = DATA_DIR / "ml_affiliate_state.json"

_aff_map = None  # cache en memoria


def _ensure_data_dir():
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)


def _canonical(url: str) -> str:
    """
    Crea clave ÚNICA para cada producto.
    Usa URL COMPLETA, no solo el path.
    """
    if not url:
        return ""
    # ✅ Usar URL completa normalizada
    url_lower = url.lower().strip()
    return url_lower


def _load_map() -> dict:
    """Lee affiliate_links.csv y lo guarda en memoria"""
    global _aff_map
    if _aff_map is not None:
        return _aff_map

    mapping = {}
    if not CSV_PATH.exists():
        _aff_map = mapping
        return mapping

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            orig = (row.get("original_url") or "").strip()
            aff = (row.get("affiliate_url") or "").strip()
            if not orig or not aff:
                continue
            key = _canonical(orig)
            if key and aff.startswith("https://mercadolibre.com/sec/"):
                mapping[key] = aff

    _aff_map = mapping
    print(f"[CSV_LOAD] Cargados {len(mapping)} links del CSV")
    return mapping


def _save_mapping(original_url: str, affiliate_url: str):
    """Agrega fila a affiliate_links.csv"""
    global _aff_map
    _ensure_data_dir()

    write_header = not CSV_PATH.exists()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["original_url", "affiliate_url"])
        if write_header:
            writer.writeheader()
        writer.writerow({
            "original_url": original_url,
            "affiliate_url": affiliate_url,
        })

    m = _load_map()
    m[_canonical(original_url)] = affiliate_url
    print(f"[CSV_SAVE] Guardado: {original_url[:60]}... → {affiliate_url[:60]}...")


def _cerrar_popup_cashback(page: Page) -> bool:
    """
    Cierra el popup de cashback de Mercado Libre si aparece.
    Devuelve True si lo cerró, False si no existía.
    """
    page.wait_for_timeout(500)  # pequeño delay para que cargue el modal

    selectores = [
        'button:has-text("Entendido")',
        'button:has-text("Ahora no")',
        'button:has-text("No, gracias")',
    ]

    for sel in selectores:
        try:
            boton = page.locator(sel).first
            if boton.is_visible():
                print("💸 Popup detectado → cerrando…")
                boton.click()
                page.wait_for_timeout(400)
                return True
        except:
            pass

    return False


def _maybe_login_first_time(context, permalink):
    """Si no existe STATE_PATH, pide login UNA VEZ"""
    if STATE_PATH.exists():
        return

    print("[AFF] ⚠️ PRIMERA VEZ: Se requiere inicio de sesión manual.")
    page = context.new_page()
    page.goto(permalink, wait_until="domcontentloaded")

    # Intentar cerrar popups iniciales
    _cerrar_popup_cashback(page)
    
    print("""
    =======================================================
    [ACCIÓN NECESARIA - SOLO UNA VEZ]
      1) Inicia sesión en tu cuenta de Mercado Libre en la ventana abierta.
      2) Abre cualquier publicación y verifica que ves la barra de afiliados (arriba).
      3) Regresa a esta consola y presiona ENTER.
    =======================================================
    """)

    input(">>> Presiona ENTER cuando hayas terminado el login... ")

    context.storage_state(path=str(STATE_PATH))
    print(f"[AFF] ✅ Sesión guardada en {STATE_PATH}\n")
    page.close()


def _click_share_button(page):
    """Clic en botón Compartir"""
    selectors = [
        'button:has-text("Compartir")',
        'text="Compartir"',
        '[data-testid="share-button"]',
        '[aria-label="Compartir"]',
        'button[title="Compartir"]',
        '.ui-pdp-share__button' 
    ]

    for sel in selectors:
        try:
            # Intentamos encontrar el botón
            btn = page.locator(sel).first
            if btn.is_visible():
                print(f"[AFF] 🖱️ Clic en Compartir ({sel})")
                btn.click()
                time.sleep(1.5) # Esperar animación del modal
                return True
        except Exception:
            pass

    print("[AFF] ❌ No encontré botón Compartir")
    return False


def _extract_affiliate_link(page, timeout_seconds=10) -> str:
    """Escanea DOM buscando https://mercadolibre.com/sec/"""
    js = """
    () => {
      const prefix = 'https://mercadolibre.com/sec/';
      const found = [];

      const pushIf = (v) => {
        if (!v) return;
        if (typeof v !== 'string') v = String(v);
        if (v.includes(prefix)) found.push(v);
      };

      const nodes = document.querySelectorAll('input,textarea,[data-copyvalue]');
      nodes.forEach(n => {
        try { pushIf(n.value); } catch(e) {}
        try { pushIf(n.textContent); } catch(e) {}
        try {
          if (n.getAttribute) pushIf(n.getAttribute('data-copyvalue'));
        } catch(e) {}
      });

      if (found.length === 0) {
        // Fallback: buscar en todo el texto del body si no está en inputs
        const bodyText = document.body.innerText || '';
        // Buscar patrón regex simple en el texto
        const match = bodyText.match(/https:\\/\\/mercadolibre\\.com\\/sec\\/[a-zA-Z0-9]+/);
        if (match) found.push(match[0]);
      }

      return found;
    }
    """

    deadline = time.time() + timeout_seconds
    prefix = "https://mercadolibre.com/sec/"

    while time.time() < deadline:
        try:
            candidates = page.evaluate(js) or []
        except Exception:
            candidates = []

        for raw in candidates:
            if not raw:
                continue
            text = str(raw).strip()
            if prefix in text:
                # Extraer URL limpia si viene con texto extra
                start = text.find(prefix)
                end = text.find(" ", start)
                if end == -1:
                    end = len(text)
                link = text[start:end].strip()
                
                # Validación final
                if link.startswith(prefix):
                    return link

        time.sleep(0.5)

    return ""


def _generate_affiliate_url(permalink: str) -> str | None:
    """
    Genera link SEC BLINDADO.
    Solo retorna si es https://mercadolibre.com/sec/XXXXX y funciona.
    """
    if not permalink:
        print("[AFF] ❌ Permalink vacío")
        return None

    print(f"\n[AFF] ======================================")
    print(f"[AFF] Generando link afiliado")
    print(f"[AFF] URL: {permalink[:60]}...")
    print(f"[AFF] ======================================")
    
    _ensure_data_dir()

    try:
        with sync_playwright() as p:
            # HEADLESS=False para ver qué pasa
            browser = p.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )

            # Permisos de portapapeles para evitar popups molestos
            permissions = ["clipboard-read", "clipboard-write"]

            if STATE_PATH.exists():
                print("[AFF] ✅ Usando sesión guardada")
                context = browser.new_context(
                    storage_state=str(STATE_PATH),
                    permissions=permissions
                )
            else:
                print("[AFF] ⚠️ SIN SESIÓN")
                context = browser.new_context(permissions=permissions)

            # Pasamos permalink aquí para que pueda navegar si tiene que loguearse
            _maybe_login_first_time(context, permalink)
            
            page = context.new_page()

            print("[AFF] 🌐 Navegando...")
            try:
                page.goto(permalink, wait_until="domcontentloaded", timeout=40000)
            except:
                print("[AFF] Timeout de carga (pero intentaremos seguir)")

            # Cerrar popups agresivos antes de interactuar
            _cerrar_popup_cashback(page)
            
            time.sleep(2)
            page.mouse.wheel(0, 500)
            time.sleep(1)

            print("[AFF] 🔘 Buscando botón Compartir...")
            found_share = _click_share_button(page)
            
            if not found_share:
                # Intento de rescate: cerrar popups de nuevo y reintentar
                _cerrar_popup_cashback(page)
                found_share = _click_share_button(page)
                if not found_share:
                    print("[AFF] ❌ NO encontró botón - FALLA")
                    page.close(); context.close(); browser.close()
                    return None

            print("[AFF] 🔗 Extrayendo link SEC...")
            aff = _extract_affiliate_link(page, timeout_seconds=10)

            if not aff:
                print("[AFF] ❌ No se encontró link SEC - FALLA")
                page.close(); context.close(); browser.close()
                return None

            if not aff.startswith("https://mercadolibre.com/sec/"):
                print(f"[AFF] ❌ No es formato SEC: {aff} - FALLA")
                page.close(); context.close(); browser.close()
                return None

            print(f"[AFF] ✅✅✅ LINK SEC VÁLIDO: {aff}")
            
            # Guardar estado de sesión actualizado
            try:
                context.storage_state(path=str(STATE_PATH))
            except Exception:
                pass

            page.close()
            context.close()
            browser.close()

            return aff

    except Exception as e:
        print(f"[AFF] ❌ ERROR CRÍTICO: {type(e).__name__}: {e}")
        return None


def get_or_create_affiliate_url(permalink: str) -> str | None:
    """
    BLINDADO: Solo retorna links SEC válidos.
    """
    if not permalink:
        return None

    mapping = _load_map()
    key = _canonical(permalink)

    # ✅ IMPORTANTE: Verifica en caché con URL COMPLETA
    if key in mapping:
        cached = mapping[key]
        print(f"[AFF] 💾 DESDE CACHÉ: {cached}")
        return cached

    print(f"[AFF] 🆕 NO EN CACHÉ - GENERANDO NUEVO LINK")
    aff = _generate_affiliate_url(permalink)
    
    # ✅ VALIDACIÓN FINAL: Solo acepta SEC
    if aff and aff.startswith("https://mercadolibre.com/sec/"):
        print(f"[AFF] 📁 GUARDANDO EN CSV")
        _save_mapping(permalink, aff)
        return aff
    
    print(f"[AFF] 🚫 RECHAZADO: No se pudo generar link")
    return None