# -*- coding: utf-8 -*-
import requests
import os
from dotenv import load_dotenv

# Cargar el archivo .env al inicio del modulo
load_dotenv()

# =====================================================================
# CONFIGURA TUS CREDENCIALES DE TELEGRAM AQUI
# =====================================================================
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
# =====================================================================

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def _send_request(method: str, payload: dict) -> bool:
    """Funcion interna para mandar requests a la API de Telegram."""
    if not BOT_TOKEN or not CHAT_ID:
        print(f"[TELEGRAM] Error: Faltan credenciales en .env")
        return False
        
    url = f"{API_URL}/{method}"
    try:
        resp = requests.post(url, json=payload, timeout=20)
    except requests.RequestException as e:
        print(f"[telegram] ERROR de red: {e}")
        return False

    if resp.status_code != 200:
        print(f"[telegram] ERROR HTTP {resp.status_code}: {resp.text}")
        return False

    return True

def post_telegram(caption: str, url_button: str | None = None) -> bool:
    """Envia mensaje de TEXTO con formato HTML."""
    payload = {
        "chat_id": CHAT_ID,
        "text": caption,
        "parse_mode": "HTML", # ?? ESTO ARREGLA LAS NEGRITAS
        "disable_web_page_preview": False,
    }

    if url_button:
        payload["reply_markup"] = {
            "inline_keyboard": [[
                {"text": "Ver oferta", "url": url_button}
            ]]
        }

    return _send_request("sendMessage", payload)

def post_telegram_photo(photo_url: str, caption: str, url_button: str | None = None) -> bool:
    """Envia FOTO con caption HTML."""
    payload = {
        "chat_id": CHAT_ID,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "HTML", # ?? ESTO ARREGLA EL FORMATO EN FOTOS
    }

    if url_button:
        payload["reply_markup"] = {
            "inline_keyboard": [[
                {"text": "Ver oferta", "url": url_button}
            ]]
        }

    return _send_request("sendPhoto", payload)