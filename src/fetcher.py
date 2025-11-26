import requests

BASE_URL = "https://api.mercadolibre.com/sites/MLM/search"

# Headers tipo navegador para que Mercado Libre no nos tire 403 tan fácil
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


def fetch_page(page: int = 0, limit: int = 50):
    """
    Descarga una página de ofertas desde Mercado Libre.

    Usamos la API pública de búsqueda de ML:
      GET /sites/MLM/search?q=...

    Ajusta el parámetro 'q' si quieres filtrar distinto.
    """
    params = {
        "q": "ofertas",          # palabra clave; se puede ajustar
        "offset": page * limit,  # paginación
        "limit": limit,
        "sort": "discount"       # prioriza artículos con descuento
    }

    try:
        resp = requests.get(
            BASE_URL,
            params=params,
            headers=HEADERS,
            timeout=15
        )
    except requests.RequestException as e:
        print(f"[fetch_page] ERROR de red: {e}")
        return []

    if resp.status_code != 200:
        print(f"[fetch_page] ERROR {resp.status_code}")
        return []

    try:
        data = resp.json()
    except ValueError:
        print("[fetch_page] ERROR al parsear JSON")
        return []

    results = data.get("results", [])

    items = []
    for r in results:
        # algunos campos pueden venir en None, lo manejamos
        price = r.get("price") or 0
        original_price = r.get("original_price") or price

        # ML suele mandar el descuento en 'discount_percentage' si está
        discount = r.get("discount_percentage")
        if discount is None:
            # cálculo manual simple
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
            "discount": discount,
            "thumbnail": r.get("thumbnail"),
            "url": r.get("permalink"),
        }
        items.append(item)

    return items


def fetch_offers(pages: int = 3, limit: int = 50):
    """
    Descarga varias páginas de ofertas y devuelve una lista completa
    sin duplicados (por id).
    """
    all_items = []

    print(f"[fetch_offers] pages={pages}")

    for p in range(pages):
        page_items = fetch_page(page=p, limit=limit)
        print(f"[fetch_offers] page {p} -> {len(page_items)} items")
        all_items.extend(page_items)

    # quitar duplicados por id
    unique = {}
    for item in all_items:
        item_id = item.get("id")
        if not item_id:
            continue
        unique[item_id] = item

    print(f"[fetch_offers] raw={len(all_items)} unique={len(unique)}")

    return list(unique.values())
