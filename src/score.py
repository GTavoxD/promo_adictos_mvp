def calc_discount(price, original):
    if not original or original <= 0:
        return 0.0
    return max(0.0, (original - price) / original)

def score_item(it: dict):
    price = float(it.get("price") or 0)
    orig = float(it.get("original_price") or price)
    # Filtra productos baratos que no dejan comisión relevante:
    if price < 800:
        return -1.0, 0.0  # cae fuera del TOP
    disc = calc_discount(price, orig)
    rating = (it.get("reviews", {}).get("rating_average") or 0) / 5
    tags = it.get("shipping", {}).get("tags", [])
    trust = 0.15 if "fulfillment" in tags else 0.0
    # Bonus por ticket (ligero) para empatar descuento + confianza:
    ticket_boost = min(price / 10000, 0.15)  # +0..0.15 hasta ~$10k
    return (0.5 * disc) + (0.25 * rating) + trust + ticket_boost, disc

def short_title(t, maxlen=72):
    return t[:maxlen-1] + "…" if len(t) > maxlen else t

def format_money(x):
    return "${:,.0f}".format(x)

def format_message(it):
    s, disc = score_item(it)
    price = float(it.get("price") or 0)
    orig = float(it.get("original_price") or price)
    title = short_title(it.get("title", ""))
    rating = it.get("reviews", {}).get("rating_average")
    rating_txt = f"{rating:.1f}/5" if rating else "—"
    envio_tags = it.get("shipping", {}).get("tags", [])
    envio = "FULL" if "fulfillment" in envio_tags else "Estándar"
    return (
        f"💥 {int(disc*100)}% de descuento | <b>{title}</b>\n"
        f"Precio: <b>{format_money(price)}</b> (antes {format_money(orig)})\n"
        f"⭐ {rating_txt} | 🚚 {envio}\n"
        f"🔗 {it.get('permalink','')}"
    )
