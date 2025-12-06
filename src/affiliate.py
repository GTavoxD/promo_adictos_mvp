# -*- coding: utf-8 -*-
"""
Construcción de links de afiliado para Mercado Libre.

Tomamos el permalink original del producto y lo envolvemos con tu shortlink
oficial de afiliado, por ejemplo:

    https://mercadolibre.com/sec/2vy22V5?url=<URL-ENCODED>

Ese patrón es el que pasa correctamente por el sistema de atribución de Meli.
"""

import urllib.parse

# TU ID DE AFILIADO (del link: https://mercadolibre.com/sec/2vy22V5)
AFF_SEC_ID = "2vy22V5"


def affiliate_link(original_url: str) -> str:
    """
    Envuelve la URL original del artículo en tu shortlink de afiliado.

    Si original_url está vacío o raro, regresa tal cual.
    """
    if not original_url:
        return original_url

    encoded = urllib.parse.quote_plus(original_url)
    return f"https://mercadolibre.com/sec/{AFF_SEC_ID}?url={encoded}"
