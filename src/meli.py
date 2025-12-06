import requests

BASE_URL = "https://api.mercadolibre.com/sites/MLM/search"

# Headers tipo navegador para reducir probabilidad de 403
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}


def _fetch_page(q: str, page: int = 0, limit: int = 50) -> list[dict]:
    """
    Descarga una página de resultados desde Mercado Libre.

    :param q: query de búsqueda (texto).
    :param page: índice de página (0 = primera).
    :param limit: cantidad de resultados por página.
    :return: lista de items crudos de la API.
    """
    params = {
        "q": q,
        "offset": page * limit,
        "limit": limit,
        "sort": "discount",  # try: ordenar por descuento
    }

    try:
        resp = requests.get(
            BASE_URL,
            params=params,
            headers=HEADERS,
            timeout=15,
        )
    except requests.RequestException as e:
        print(f"[meli] ERROR de red: {e}")
        return []

    if resp.status_code != 200:
        print(f"[meli] ERROR HTTP {resp.status_code}: {resp.text[:200]}")
        return []

    try:
        data = resp.json()
    except ValueError:
        print("[meli] ERROR al parsear JSON")
        return []

    return data.get("results", [])


def _normalize_item(r: dict) -> dict:
    """Convierte un item crudo de ML en un dict estándar para el bot."""
    price = r.get("price") or 0
    original_price = r.get("original_price") or r.get("base_price") or price

    # Intentar traer descuento directo
    discount = r.get("discount_percentage")
    if discount is None:
        try:
            if original_price and original_price > 0:
                discount = int(round((1 - (price / original_price)) * 100))
            else:
                discount = 0
        except Exception:
            discount = 0

    item = {
        "id": r.get("id"),
        "title": r.get("title") or "Sin título",
        "price": price,
        "original_price": original_price,
        "discount": int(discount) if discount is not None else 0,
        "thumbnail": r.get("thumbnail") or r.get("secure_thumbnail"),
        "url": r.get("permalink"),
    }
    return item


def fetch_offers(
    q: str = "oferta",
    pages: int = 3,
    limit_per_page: int = 50,
) -> list[dict]:
    """
    Descarga varias páginas de resultados y las normaliza.

    :param q: texto de búsqueda (por defecto 'oferta').
    :param pages: cuántas páginas traer.
    :param limit_per_page: límite por página.
    :return: lista de items normalizados sin duplicados.
    """
    print(f"[meli.fetch_offers] q='{q}', pages={pages}, limit_per_page={limit_per_page}")

    all_raw: list[dict] = []
    for p in range(pages):
        page_items = _fetch_page(q=q, page=p, limit=limit_per_page)
        print(f"[meli] page {p} -> {len(page_items)} items")
        all_raw.extend(page_items)

    print(f"[meli] raw items: {len(all_raw)}")

    # Normalizar y quitar duplicados por id
    unique: dict[str, dict] = {}
    for r in all_raw:
        item = _normalize_item(r)
        item_id = item.get("id")
        if not item_id:
            continue
        unique[item_id] = item

    print(f"[meli] unique items: {len(unique)}")

    return list(unique.values())
