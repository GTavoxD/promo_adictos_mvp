# -*- coding: utf-8 -*-
"""
audit.py

Guarda un registro de cada oferta publicada en data/audit_offers.csv

Campos:
- timestamp         (ISO)
- id                (ID de Mercado Libre)
- title             (título recortado)
- price             (precio actual)
- original_price    (precio anterior)
- discount_pct      (descuento aplicado, 0-100)
- permalink         (link original de ML)
- link_used         (link final que se mandó a Telegram)
- affiliate_used    ("yes" si link_used es /sec/, si no "no")
"""

import csv
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
AUDIT_FILE = DATA_DIR / "audit_offers.csv"


def _ensure_data_dir():
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)


def audit_row(item: dict, discount: float, link_used: str):
    _ensure_data_dir()

    now = datetime.datetime.now().isoformat(timespec="seconds")

    item_id = item.get("id", "")
    title = (item.get("title", "") or "").strip()
    price = item.get("price")
    original_price = item.get("original_price") or ""
    try:
        disc_pct = round(discount * 100, 2)
    except Exception:
        disc_pct = ""

    permalink = item.get("permalink", "") or ""
    link_used = (link_used or "").strip()
    affiliate_used = "yes" if link_used.startswith("https://mercadolibre.com/sec/") else "no"

    write_header = not AUDIT_FILE.exists()
    fieldnames = [
        "timestamp",
        "id",
        "title",
        "price",
        "original_price",
        "discount_pct",
        "permalink",
        "link_used",
        "affiliate_used",
    ]

    with open(AUDIT_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow({
            "timestamp": now,
            "id": item_id,
            "title": title,
            "price": price,
            "original_price": original_price,
            "discount_pct": disc_pct,
            "permalink": permalink,
            "link_used": link_used,
            "affiliate_used": affiliate_used,
        })
