# -*- coding: utf-8 -*-
"""
rules.py - Versión simplificada y estable

Objetivo:
  - NO romper el bot.
  - Asegurar que haya productos "Eligible" de forma consistente.
  - Score basado únicamente en:
        * que exista descuento real (original > price)
        * tamaño del descuento (%)
        * ticket del producto (price)
  - La lógica de comisión por categoría la dejamos PARA DESPUÉS,
    cuando el flujo ya esté estable.

Interfaz:
  score_item(item) -> (score, discount)

  - score  > 0  => candidato válido
  - score <= 0  => descartado en main.py
"""

from __future__ import annotations

from typing import Dict, Tuple, Any


# En src/rules.py, modifica score_item():

def score_item(item: Dict[str, Any]) -> Tuple[float, float]:
    price = item.get("price")
    original = item.get("original_price")

    try:
        price = float(price)
        original = float(original)
    except Exception:
        return -1.0, 0.0

    if original <= 0 or price <= 0:
        return -1.0, 0.0

    if original <= price:
        return -1.0, 0.0

    discount = (original - price) / original

    # ✅ NUEVO SCORING: Balanceado entre descuento y precio
    
    # Factor 1: Descuento % (importancia media)
    discount_factor = discount * 100  # 0-100
    
    # Factor 2: Precio (importancia baja, para no favorecer solo caros)
    # Normalizar precio a escala 0-100
    # Productos entre $500-$10000 son "normales"
    price_factor = min(100, (price / 10000) * 100)  # Cap a 100
    
    # Factor 3: Confianza en descuento (se agregará en enrich_item)
    confidence = item.get("discount_confidence", 0.7)
    
    # Combinación ponderada:
    # 60% descuento + 20% precio + 20% confianza
    score = (
        (discount_factor * 0.60) +
        (price_factor * 0.20) +
        (confidence * 100 * 0.20)
    )

    return score, discount