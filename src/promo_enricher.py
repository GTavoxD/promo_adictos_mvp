# -*- coding: utf-8 -*-
"""
promo_enricher.py - VERSIÓN ROBUSTA
"""

from __future__ import annotations
from typing import Dict, Any, Optional
import re

def _extract_item_id_from_url(url: str) -> Optional[str]:
    m = re.search(r"(MLM\d{8,12})", url.upper())
    if m: return m.group(1)
    return None

def _normalize_official_tag(text: str) -> Optional[str]:
    if not text: return None
    
    # 🚨 FIX: Creamos la versión sin acento para la comparación
    t_norm = text.strip().lower().replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")
    
    # Usamos las claves sin acento para la comparación
    if "relampago" in t_norm: return "⚡ Oferta Relámpago"
    if "imperdible" in t_norm: return "💎 Imperdible"
    if "oferta del dia" in t_norm: return "⏰ Oferta del Día"
    if "mas vendido" in t_norm: return "🔥 Más Vendido"
    if "recomendado" in t_norm: return "⭐ Recomendado"
    
    return None
    
def enrich_item(item: Dict[str, Any]) -> Dict[str, Any]:
    enriched = dict(item or {})  
    url = enriched.get("permalink") or enriched.get("url") or enriched.get("link")
    if not url: return enriched

    print(f"[ENRICH] 🚀 Procesando: {enriched.get('title', '')[:30]}...")
    
    fetcher_tag = enriched.get("promo_tag", "")
    fetcher_coupon = enriched.get("coupon_text", "")
    
    official_tag = _normalize_official_tag(fetcher_tag)
    
    # Detección de FULL en el tag crudo
    is_full = "FULL" in fetcher_tag.upper() # <--- Se asegura de detectar FULL aquí
    
    final_tag = official_tag if official_tag else ""
    
    # Re-insertar FULL si estaba presente
    if is_full:
        if final_tag:
            if "FULL" not in final_tag.upper():
                final_tag = f"{final_tag} | ⚡ FULL"
        else:
            final_tag = "⚡ FULL"
            
    # Fallback si no hay tag oficial pero sí texto
    if not final_tag and fetcher_tag:
        final_tag = fetcher_tag

    # Calidad simulada para ofertas fuertes
    enriched["rating"] = float(enriched.get("rating") or 0.0)
    enriched["reviews_count"] = int(enriched.get("reviews_count") or 0)
    enriched["sold_quantity"] = int(enriched.get("sold_quantity") or 0)

    if enriched["rating"] == 0.0 and enriched["reviews_count"] == 0:
        # 🚨 FIX: Usamos t_check sin acentos para validar (Garantiza que no falle por acentos)
        t_check = final_tag.lower().replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")
        
        if "relampago" in t_check or "mas vendido" in t_check or "full" in t_check:
            enriched["rating"] = 4.5
            enriched["reviews_count"] = 100
            enriched["sold_quantity"] = 500
            print(f"[QUALITY] Inyectando calidad alta por tag: {final_tag}")
        elif final_tag:
            enriched["rating"] = 4.0
            enriched["reviews_count"] = 50
            enriched["sold_quantity"] = 100
            print(f"[QUALITY] Inyectando calidad alta por tag: {final_tag}")

    enriched["promo_tag"] = final_tag
    enriched["coupon_text"] = fetcher_coupon
    
    enriched["id"] = _extract_item_id_from_url(url) or enriched.get('id')
    
    from src.price_validator import get_discount_confidence_score
    enriched["discount_confidence"] = get_discount_confidence_score(enriched, None)
    
    return enriched