# -*- coding: utf-8 -*-
"""
publisher.py

Funciones para publicar en Telegram.

post_telegram(text):      envía solo texto (HTML).
post_telegram_photo(url): envía foto usando la URL directa + caption en HTML.
"""

import os
import requests
from dotenv import load_dotenv

# Cargamos .env UNA sola vez, al importar el módulo
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

if not TELEGRAM_TOKEN:
    print("[TELEGRAM] WARNING: TELEGRAM_TOKEN no está definido en .env")
if not TELEGRAM_CHAT_ID:
    print("[TELEGRAM] WARNING: TELEGRAM_CHAT_ID no está definido en .env")

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else ""


def post_telegram(text: str) -> bool:
    """
    Envía un mensaje de texto (HTML) al chat configurado.
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[TELEGRAM] No hay credenciales configuradas. Abortando post_telegram.")
        return False

    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    try:
        resp = requests.post(url, data=payload, timeout=20)
        if resp.status_code != 200:
            print(f"[TELEGRAM] ERROR sendMessage status={resp.status_code}: {resp.text}")
            return False
        return True
    except Exception as e:
        print(f"[TELEGRAM] EXCEPTION en sendMessage: {e}")
        return False


def post_telegram_photo(photo_url: str, caption: str) -> bool:
    """
    Envía una foto a Telegram usando la URL directa en el campo "photo".
    NO descargamos la imagen localmente; Telegram la baja por su cuenta.
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[TELEGRAM] No hay credenciales configuradas. Abortando post_telegram_photo.")
        return False

    if not photo_url.startswith("http"):
        print(f"[TELEGRAM] photo_url no es una URL válida: {photo_url!r}")
        return False

    url = f"{BASE_URL}/sendPhoto"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "HTML",
    }

    print(f"[TELEGRAM] Enviando foto por URL: {photo_url}")

    try:
        resp = requests.post(url, data=payload, timeout=20)
        if resp.status_code != 200:
            print(f"[TELEGRAM] ERROR sendPhoto status={resp.status_code}: {resp.text}")
            return False
        return True
    except Exception as e:
        print(f"[TELEGRAM] EXCEPTION en sendPhoto: {e}")
        return False
