# src/short_ml.py
import os
from dotenv import load_dotenv

# Cargar variables del .env
load_dotenv()

AFFILIATE_APPEND = os.getenv("AFFILIATE_APPEND", "").strip()

def create_short_link(long_url: str) -> str:
    """
    Shortener simplificado:
    - Asegura que el link lleve tu parámetro de afiliado.
    - NO usa Chrome, ni Playwright, ni nada externo.
    """
    if not long_url:
        return long_url

    url = long_url.strip()

    # Si no hay parámetro de afiliado configurado, regresa tal cual
    if not AFFILIATE_APPEND:
        return url

    # Normaliza el AFFILIATE_APPEND por si viene con '?'
    aff = AFFILIATE_APPEND.lstrip("?")

    # Si ya trae exactamente ese parámetro, lo dejamos igual
    if aff in url:
        return url

    # Elegir si se concatena con ? o con &
    join_char = "&" if "?" in url else "?"
    return f"{url}{join_char}{aff}"


def shorten_via_linkbuilder(long_url: str) -> str:
    """
    Wrapper para ser compatible con main.py
    """
    return create_short_link(long_url)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python -m src.short_ml <URL>")
        raise SystemExit(1)

    url = sys.argv[1]
    print(create_short_link(url))
