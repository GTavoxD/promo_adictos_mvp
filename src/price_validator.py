# -*- coding: utf-8 -*-
"""
price_validator.py

Valida si un descuento es REAL (histórico) o FALSO (precio inflado).
Intenta extraer el histórico de precios de Mercado Libre.
"""

import re
from typing import Optional, Dict, List


def extract_price_history_from_html(html: str) -> Optional[Dict]:
    """
    Intenta extraer histórico de precios del HTML de la página.
    
    Mercado Libre muestra en algún lugar:
    - "Precio más bajo en los últimos 30 días: $X"
    - "Precio anterior: $Y"
    - Gráfico de precios (en JSON dentro del HTML)
    
    Retorna:
        {
            "lowest_30_days": 5000,
            "highest_30_days": 8000,
            "current_price": 3000,
            "price_before": 6000,
        }
    """
    
    if not html:
        return None
    
    data = {}
    
    # Búsqueda 1: "Precio más bajo en los últimos 30 días"
    match = re.search(
        r"precio\s+m[aá]s\s+bajo\s+en\s+los\s+[úu]ltimos\s+30\s+d[íi]as[^$]*\$\s*([\d.,]+)",
        html,
        re.IGNORECASE
    )
    if match:
        try:
            lowest = float(match.group(1).replace(".", "").replace(",", ""))
            data["lowest_30_days"] = lowest
        except:
            pass
    
    # Búsqueda 2: "Precio más alto en los últimos 30 días"
    match = re.search(
        r"precio\s+m[aá]s\s+alto\s+en\s+los\s+[úu]ltimos\s+30\s+d[íi]as[^$]*\$\s*([\d.,]+)",
        html,
        re.IGNORECASE
    )
    if match:
        try:
            highest = float(match.group(1).replace(".", "").replace(",", ""))
            data["highest_30_days"] = highest
        except:
            pass
    
    # Búsqueda 3: "Precio anterior" (antes del descuento)
    match = re.search(
        r"precio\s+anterior[^$]*\$\s*([\d.,]+)",
        html,
        re.IGNORECASE
    )
    if match:
        try:
            price_before = float(match.group(1).replace(".", "").replace(",", ""))
            data["price_before"] = price_before
        except:
            pass
    
    return data if data else None


def is_discount_real(item: Dict, price_history: Optional[Dict]) -> bool:
    """
    Determina si un descuento es REAL o FALSO.
    
    Parámetros:
        item: producto con "original_price" y "price"
        price_history: histórico extraído del HTML (puede ser None)
    
    Retorna:
        True = Descuento es REAL
        False = Descuento sospechoso (inflado)
    
    Lógica:
    -------
    1. Si NO tenemos histórico:
       → Usar heurísticas conservadoras
    
    2. Si SÍ tenemos histórico:
       → Comparar precio actual con mínimo de 30 días
       → Si actual == mínimo → es nuevo descuento REAL
       → Si actual > mínimo → descuento FALSO
    """
    
    try:
        original = float(item.get("original_price") or 0)
        current = float(item.get("price") or 0)
    except:
        return False  # No se puede validar, rechazar por seguridad
    
    if original <= 0 or current <= 0:
        return False
    
   
    # Caso 1: Tenemos histórico de precios
    if isinstance(price_history, dict) and "lowest_30_days" in price_history:
        lowest_30 = price_history["lowest_30_days"]
        
        # Si precio actual está CERCANO al mínimo de 30 días → DESCUENTO REAL
        # "Cercano" = diferencia < 5%
        diff_percent = abs(current - lowest_30) / lowest_30 * 100
        
        if diff_percent < 5:
            print(f"[REAL] Descuento REAL: precio actual ${current:.0f} ≈ mínimo 30d ${lowest_30:.0f}")
            return True
        
        # Si precio actual está MÁS ALTO que el mínimo → Posible inflado
        if current > lowest_30 * 1.05:  # 5% de margen
            print(f"[FAKE] Descuento SOSPECHOSO: precio actual ${current:.0f} > mínimo 30d ${lowest_30:.0f}")
            return False
    
    # Caso 2: Validar con "precio_before" (ML anterior)
    if isinstance(price_history, dict) and "price_before" in price_history:
        price_before = price_history["price_before"]
        
        # Si el "precio anterior" (tachado) es similar al "original_price"
        # Y el precio actual es REALMENTE descuento
        # → Es REAL
        if abs(original - price_before) / original * 100 < 10:  # Menos 10% de diferencia
            print(f"[REAL] Descuento REAL: oficial de ML")
            return True
    
    # Caso 3: Heurísticas (sin histórico)
    # Si NO tenemos datos de histórico, usar reglas conservadoras
    
    discount_pct = (original - current) / original * 100
    
    # ROJO INTENSO: Descuentos > 80% son MUY sospechosos
    if discount_pct > 80:
        print(f"[FAKE] Descuento > 80% ({discount_pct:.0f}%) - SOSPECHOSO")
        return False
    
    # AMARILLO: Descuentos 60-80% requieren validación extra
    if discount_pct > 60:
        # Solo aceptar si:
        # 1. Es marca conocida (no verificable aquí)
        # 2. Tiene MUCHAS opiniones positivas
        
        reviews = item.get("reviews_count") or 0
        rating = item.get("rating") or 0
        
        # Si tiene >= 500 opiniones Y rating >= 4.5 → probablemente REAL
        if reviews >= 500 and rating >= 4.5:
            print(f"[PROBABLY_REAL] Alto descuento pero muchas opiniones ({reviews}) y buena calificación ({rating}⭐)")
            return True
        
        # Si NO tiene suficientes opiniones → SOSPECHOSO
        if reviews < 100:
            print(f"[FAKE] Descuento alto ({discount_pct:.0f}%) pero pocas opiniones ({reviews})")
            return False
    
    # VERDE: Descuentos 20-60% son típicamente REALES
    if 20 <= discount_pct <= 60:
        print(f"[REAL] Descuento realista ({discount_pct:.0f}%)")
        return True
    
    # Descuentos < 20% no son interesantes
    if discount_pct < 20:
        print(f"[TOO_SMALL] Descuento muy pequeño ({discount_pct:.0f}%)")
        return False
    
    # Fallback
    return True


def get_discount_confidence_score(item: Dict, price_history: Optional[Dict]) -> float:
    """
    Calcula un score de CONFIANZA en que el descuento es real (0.0 a 1.0)
    
    Uso para REWEIGHT el scoring:
        score = original_score * confidence_score
    
    Ejemplo:
        original_score = 1500
        confidence = 0.8  (descuento probablemente real)
        final_score = 1500 * 0.8 = 1200
    """
    
    try:
        original = float(item.get("original_price") or 0)
        current = float(item.get("price") or 0)
    except:
        return 0.5  # Neutral si hay error
    
    if original <= 0 or current <= 0:
        return 0.0
    
    confidence = 0.5  # Base neutral
    
    # Factor 1: Histórico disponible (importante)
    if price_history and "lowest_30_days" in price_history:
        lowest_30 = price_history["lowest_30_days"]
        diff_percent = abs(current - lowest_30) / lowest_30 * 100
        
        if diff_percent < 2:
            confidence += 0.35  # Muy confiable
        elif diff_percent < 5:
            confidence += 0.25
        elif diff_percent < 10:
            confidence += 0.10
        else:
            confidence -= 0.20  # Muy sospechoso
    
    # Factor 2: Opiniones y rating (indica que otros compraron real)
    reviews = item.get("reviews_count") or 0
    rating = item.get("rating") or 0
    
    if reviews >= 1000 and rating >= 4.5:
        confidence += 0.20
    elif reviews >= 500 and rating >= 4.3:
        confidence += 0.10
    elif reviews >= 100 and rating >= 4.0:
        confidence += 0.05
    elif reviews < 50:
        confidence -= 0.15  # Pocas opiniones = sospechoso
    
    # Factor 3: Porcentaje de descuento
    discount_pct = (original - current) / original * 100
    
    if 25 <= discount_pct <= 50:
        confidence += 0.15  # Rango realista
    elif 50 < discount_pct <= 70:
        confidence += 0.05
    elif discount_pct > 75:
        confidence -= 0.30  # Muy alto, sospechoso
    
    # Factor 4: Ventas (indica confianza)
    sold = item.get("sold_quantity") or 0
    
    if sold >= 1000:
        confidence += 0.10
    elif sold >= 100:
        confidence += 0.05
    
    # Clamp entre 0.0 y 1.0
    confidence = max(0.0, min(1.0, confidence))
    
    return confidence