# -*- coding: utf-8 -*-
"""
alerts.py

Sistema de alertas para errores críticos.
Envía alertas al chat PERSONAL (no al grupo).
"""

import os
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
PERSONAL_CHAT_ID = os.getenv("TELEGRAM_PERSONAL_CHAT_ID", "").strip()

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


def send_alert(title: str, message: str, level: str = "ERROR"):
    """
    Enviar alerta al chat personal.
    
    Parámetros:
        title: Título de la alerta (ej: "Error en Scraping")
        message: Mensaje detallado (ej: "HTTP 429 en página 3")
        level: "ERROR", "WARNING", "SUCCESS", "INFO"
    
    Ejemplo:
        send_alert(
            title="Error en scraping",
            message="ML bloqueó por rate limit",
            level="ERROR"
        )
    
    Emojis por nivel:
        ERROR    → 🔴
        WARNING  → 🟡
        SUCCESS  → 🟢
        INFO     → 🔵
    """
    
    if not TELEGRAM_TOKEN or not PERSONAL_CHAT_ID:
        print("[ALERT] No configurados TELEGRAM_TOKEN o TELEGRAM_PERSONAL_CHAT_ID")
        print(f"  Title: {title}")
        print(f"  Message: {message}")
        return False
    
    # Emojis por nivel
    emojis = {
        "ERROR": "🔴",
        "WARNING": "🟡",
        "SUCCESS": "🟢",
        "INFO": "🔵",
    }
    emoji = emojis.get(level, "❓")
    
    # Timestamp
    now = datetime.now().strftime("%H:%M:%S")
    
    # Construir mensaje
    text = f"""
{emoji} {level} | {now}

<b>{title}</b>

{message}
    """.strip()
    
    # Enviar
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": PERSONAL_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }
    
    try:
        resp = requests.post(url, data=payload, timeout=10)
        
        if resp.status_code == 200:
            print(f"[ALERT SENT] {level}: {title}")
            return True
        else:
            print(f"[ALERT FAILED] Status {resp.status_code}: {resp.text}")
            return False
            
    except Exception as e:
        print(f"[ALERT ERROR] {e}")
        return False


def send_error(title: str, error_message: str):
    """Enviar alerta de ERROR"""
    send_alert(title, error_message, level="ERROR")


def send_warning(title: str, warning_message: str):
    """Enviar alerta de WARNING"""
    send_alert(title, warning_message, level="WARNING")


def send_success(title: str, success_message: str):
    """Enviar alerta de SUCCESS"""
    send_alert(title, success_message, level="SUCCESS")


def send_info(title: str, info_message: str):
    """Enviar alerta de INFO"""
    send_alert(title, info_message, level="INFO")


def send_summary(stats: dict):
    """
    Enviar resumen de la ejecución.
    
    Parámetros:
        stats: diccionario con resultados
        {
            "fetched": 100,
            "eligible": 30,
            "published": 10,
            "errors": 0,
            "duration_minutes": 5.2,
        }
    """
    
    text = f"""
✅ RESUMEN DE EJECUCIÓN

📊 Resultados:
  • Scrapeados: {stats.get('fetched', 0)}
  • Elegibles: {stats.get('eligible', 0)}
  • Publicados: {stats.get('published', 0)}
  • Errores: {stats.get('errors', 0)}

⏱️ Duración: {stats.get('duration_minutes', 0):.1f} min

📝 Próxima ejecución: ~30 min
    """.strip()
    
    send_alert(
        title="Ejecución completada",
        message=text,
        level="SUCCESS"
    )