# -*- coding: utf-8 -*-
"""
generate_affiliate_links.py

Flujo:
1) Abrir URL del producto
2) Click en botón azul "Compartir" (barra de afiliados)
3) Esperar a que se abra el modal "Generar link / ID de producto"
4) Escanear el DOM buscando cualquier valor/texto que contenga
   'https://mercadolibre.com/sec/'
5) Guardar original + afiliado en data/affiliate_links.csv

NO usa clipboard, NO pide permisos.
"""

import time
import csv
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
STATE_PATH = DATA_DIR / "ml_affiliate_state.json"
INPUT_FILE = DATA_DIR / "product_urls.txt"
OUTPUT_FILE = DATA_DIR / "affiliate_links.csv"


def ensure_data_dir():
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_product_urls():
    if not INPUT_FILE.exists():
        print(f"[ERROR] No existe {INPUT_FILE}. Crea ese archivo con URL por línea.")
        return []

    urls = []
    for line in INPUT_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
    return urls


def maybe_login_first_time(context):
    """
    Si no hay STATE_PATH, abrimos Meli para que inicies sesión manualmente.
    """
    if STATE_PATH.exists():
        return

    page = context.new_page()
    print("[INFO] No hay sesión guardada. Abriendo Mercado Libre para login...")

    page.goto("https://www.mercadolibre.com.mx", wait_until="domcontentloaded")

    print("""
>>> ACCIÓN NECESARIA <<<
1) Inicia sesión en tu cuenta de Mercado Libre
2) Abre cualquier publicación y verifica que aparece la barra de afiliados
3) Cuando ya esté la sesión OK, vuelve aquí y presiona ENTER
""")

    input("Presiona ENTER cuando ya hayas iniciado sesión correctamente... ")

    context.storage_state(path=str(STATE_PATH))
    print(f"[OK] Estado (sesión) guardado en {STATE_PATH}.\n")
    page.close()


# --------------------------------------------------------------
# 1. CLICK EN “COMPARTIR”
# --------------------------------------------------------------

def click_share_button(page):
    """
    Clic en el botón azul de la barra de afiliados: 'Compartir'.
    """
    selectors = [
        'button:has-text("Compartir")',
        'text="Compartir"',
        '[data-testid="share-button"]',
        '[aria-label="Compartir"]',
        'button[title="Compartir"]',
    ]

    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if btn.is_visible():
                print(f"[INFO] Clic en Compartir con selector: {sel}")
                btn.click()
                time.sleep(1.0)
                return True
        except Exception:
            pass

    # Último intento: texto suelto
    try:
        btn = page.get_by_text("Compartir", exact=False).first
        if btn.is_visible():
            print("[INFO] Clic en Compartir con get_by_text('Compartir').")
            btn.click()
            time.sleep(1.0)
            return True
    except Exception:
        pass

    print("[WARN] No encontré el botón Compartir automáticamente.")
    return False


# --------------------------------------------------------------
# 2. EXTRAER LINK /sec/XXXX DESDE EL DOM
# --------------------------------------------------------------

def extract_affiliate_link(page, timeout_seconds=10) -> str:
    """
    Durante 'timeout_seconds', escanea el DOM buscando cualquier texto/valor
    que contenga 'https://mercadolibre.com/sec/'.
    """
    js = """
    () => {
      const prefix = 'https://mercadolibre.com/sec/';
      const found = [];

      const pushIf = (v) => {
        if (!v) return;
        if (typeof v !== 'string') v = String(v);
        if (v.includes(prefix)) found.push(v);
      };

      // 1) Inputs, textareas y data-copyvalue
      const nodes = document.querySelectorAll('input,textarea,[data-copyvalue]');
      nodes.forEach(n => {
        try { pushIf(n.value); } catch(e) {}
        try { pushIf(n.textContent); } catch(e) {}
        try {
          if (n.getAttribute) pushIf(n.getAttribute('data-copyvalue'));
        } catch(e) {}
      });

      // 2) Si no encontramos nada, escanear texto completo del body
      if (found.length === 0) {
        const bodyText = document.body.innerText || '';
        bodyText.split(/\\s+/).forEach(tok => {
          if (tok.startsWith(prefix)) found.push(tok);
        });
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

        # Normalizar y devolver el primero razonable
        for raw in candidates:
            if not raw:
                continue
            text = str(raw).strip()
            if prefix in text:
                # sacar exactamente el link
                start = text.find(prefix)
                end = text.find(" ", start)
                if end == -1:
                    end = len(text)
                link = text[start:end].strip()
                if link.startswith(prefix):
                    return link

        time.sleep(0.5)

    return ""


# --------------------------------------------------------------

def main():
    ensure_data_dir()
    load_dotenv()

    urls = load_product_urls()
    if not urls:
        return

    print(f"[INFO] Procesando {len(urls)} URLs…")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )

        if STATE_PATH.exists():
            context = browser.new_context(storage_state=str(STATE_PATH))
        else:
            context = browser.new_context()

        maybe_login_first_time(context)
        page = context.new_page()

        results = []

        for idx, url in enumerate(urls, start=1):
            print(f"\n[{idx}/{len(urls)}] URL: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=35000)

            time.sleep(1.5)
            page.mouse.wheel(0, 1200)
            time.sleep(1.0)

            # 1) Intentar abrir el modal con el botón azul Compartir
            click_share_button(page)

            print("   Buscando 'https://mercadolibre.com/sec/...' en la página (hasta 10s)...")
            aff = extract_affiliate_link(page, timeout_seconds=10)

            if not aff:
                print("   [ERROR] No pude encontrar ningún link de afiliado en el DOM.")
            else:
                print(f"   → Enlace afiliado detectado: {aff}")

            results.append({"original_url": url, "affiliate_url": aff})

        # Guardar CSV
        fieldnames = ["original_url", "affiliate_url"]
        write_header = not OUTPUT_FILE.exists()

        with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerows(results)

        print(f"\n[OK] Listo. Archivo actualizado en {OUTPUT_FILE}")

        # Guardar sesión
        try:
            context.storage_state(path=str(STATE_PATH))
        except Exception:
            pass

        page.close()
        browser.close()


if __name__ == "__main__":
    main()
