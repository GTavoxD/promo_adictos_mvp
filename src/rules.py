# -*- coding: utf-8 -*-
"""
rules.py - MODO PERMISIVO

Objetivo: Dejar pasar CUALQUIER oferta con buen descuento hacia la etapa de enriquecimiento.
No filtrar por rating aquí, porque el rating se obtiene después.
"""

from __future__ import annotations
from typing import Dict, Tuple, Any

def score_item(item: Dict[str, Any]) -> Tuple[float, float]:
    price = item.get("price")
    original = item.get("original_price")

    # Validación básica de números
    try:
        price = float(price)
        original = float(original)
    except Exception:
        return -1.0, 0.0

    # Validación lógica de precios
    if original <= 0 or price <= 0 or original <= price:
        return -1.0, 0.0

    # Calcular descuento
    discount = (original - price) / original

    # --- LÓGICA PERMISIVA ---
    
    # 1. Si el descuento es menor al 20%, descartar.
    if discount < 0.20:
        return -1.0, discount

    # 2. Puntuación Base = El porcentaje de descuento (Ej: 40% = 40 puntos)
    score = discount * 100

    # 3. NO penalizar por falta de rating aquí (el rating viene después)
    
    # 4. Pequeña penalización si es extremadamente barato (evitar basura < $100 pesos)
    if price < 100:
        score -= 50

    return score, discount