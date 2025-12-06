# -*- coding: utf-8 -*-
"""
daily_stats.py

Lee data/audit_offers.csv y muestra estadísticas del día actual:
- total de ofertas publicadas
- cuántas con link de afiliado (/sec/)
- cuántas con link normal
- descuento promedio
"""

import csv
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
AUDIT_FILE = DATA_DIR / "audit_offers.csv"


def main():
    if not AUDIT_FILE.exists():
        print("[STATS] No existe audit_offers.csv todavía.")
        return

    today = datetime.date.today()
    total = 0
    aff = 0
    normal = 0
    discounts = []

    with open(AUDIT_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts = row.get("timestamp") or ""
            if len(ts) < 10:
                continue

            try:
                d = datetime.date.fromisoformat(ts[:10])
            except Exception:
                continue

            if d != today:
                continue

            total += 1
            if (row.get("affiliate_used") or "").strip().lower() == "yes":
                aff += 1
            else:
                normal += 1

            try:
                dp = float(row.get("discount_pct") or 0.0)
                discounts.append(dp)
            except Exception:
                pass

    print(f"[STATS] Fecha: {today.isoformat()}")
    print(f"[STATS] Ofertas publicadas hoy: {total}")
    print(f"[STATS]  - con link afiliado: {aff}")
    print(f"[STATS]  - con link normal  : {normal}")

    if discounts:
        avg_disc = sum(discounts) / len(discounts)
        print(f"[STATS] Descuento promedio hoy: {avg_disc:.2f}%")
        if discounts:
            print(f"[STATS] Máx descuento hoy     : {max(discounts):.2f}%")
            print(f"[STATS] Mín descuento hoy     : {min(discounts):.2f}%")
    else:
        print("[STATS] No pude calcular descuentos (sin datos).")


if __name__ == "__main__":
    main()
