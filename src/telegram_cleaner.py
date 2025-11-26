# -*- coding: utf-8 -*-
import os
import json
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
SENT_PATH = ROOT / "sent_messages.json"

load_dotenv(ROOT / ".env")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

API = f"https://api.telegram.org/bot{TOKEN}" if TOKEN else None


def _load_sent():
    if not SENT_PATH.exists():
        return []
    try:
        return json.load(open(SENT_PATH, "r", encoding="utf-8"))
    except Exception:
        return []


def _save_sent(data):
    json.dump(data, open(SENT_PATH, "w", encoding="utf-8"))


def delete_message(chat_id, message_id):
    r = requests.post(
        f"{API}/deleteMessage",
        data={"chat_id": chat_id, "message_id": message_id},
        timeout=20,
    )
    try:
        return r.json()
    except Exception:
        return {"ok": False, "error": "no-json", "raw": r.text[:200]}


def clean_group():
    if not TOKEN or not CHAT_ID:
        print("[ERROR] Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID en .env")
        return

    if not API:
        print("[ERROR] API base no construida.")
        return

    data = _load_sent()
    if not data:
        print("No hay mensajes registrados en sent_messages.json")
        return

    print(f"Mensajes registrados para borrar: {len(data)}")
    remaining = []
    deleted = 0
    failed = 0

    for entry in data:
        cid = entry.get("chat_id")
        mid = entry.get("message_id")
        if cid is None or mid is None:
            continue

        print(f"Eliminando mensaje {mid}...", end=" ")
        resp = delete_message(cid, mid)
        if resp.get("ok"):
            deleted += 1
            print("OK")
        else:
            failed += 1
            remaining.append(entry)
            print("FALLO:", resp)

    _save_sent(remaining)

    print("\nResumen limpieza:")
    print(f"  Eliminados: {deleted}")
    print(f"  Fallidos:   {failed}")
    print(f"  Pendientes: {len(remaining)}")


if __name__ == "__main__":
    clean_group()
