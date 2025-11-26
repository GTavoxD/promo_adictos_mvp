# -*- coding: utf-8 -*-
"""
affiliate_map.py

Lee data/affiliate_links.csv y expone una función:
    get_affiliate_url(permalink_original) -> str | None

Usa la URL base (sin querystring) como clave, para que no afecten
parámetros extras.
"""

import csv
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CSV_PATH = DATA_DIR / "affiliate_links.csv"

_aff_map = None  # cache en memoria


def _canonical(url: str) -> str:
    if not url:
        return ""
    parts = urlsplit(url)
    return parts.scheme + "://" + parts.netloc + parts.path


def _load_map() -> dict:
    global _aff_map
    if _aff_map is not None:
        return _aff_map

    mapping = {}
    if not CSV_PATH.exists():
        _aff_map = mapping
        return mapping

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            orig = (row.get("original_url") or "").strip()
            aff = (row.get("affiliate_url") or "").strip()
            if not orig or not aff:
                continue
            key = _canonical(orig)
            if key and aff.startswith("https://mercadolibre.com/sec/"):
                mapping[key] = aff

    _aff_map = mapping
    return mapping


def get_affiliate_url(permalink: str) -> str | None:
    """
    Devuelve el link de afiliado si existe para el permalink dado,
    o None si no hay mapeo.
    """
    if not permalink:
        return None
    m = _load_map()
    key = _canonical(permalink)
    return m.get(key)
