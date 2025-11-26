import requests

# =====================================================================
# CONFIGURA TUS CREDENCIALES DE TELEGRAM AQUÍ
# =====================================================================
BOT_TOKEN = "PON_AQUI_TU_BOT_TOKEN"
CHAT_ID = "@TU_CANAL_O_CHAT_ID"  # puede ser @nombre_canal o ID numérico
# =====================================================================


API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def _send_request(method: str, payload: dict) -> bool:
    """Función interna para mandar requests a la API de Telegram."""
    url = f"{API_URL}/{method}"
    try:
        resp = requests.post(url, json=payload, timeout=15)
    except requests.RequestException as e:
        print(f"[telegram] ERROR de red: {e}")
        return False

    if resp.status_code != 200:
        print(f"[telegram] ERROR HTTP {resp.status_code}: {resp.text}")
        return False

    data = resp.json()
    if not data.get("ok", False):
        print(f"[telegram] ERROR API: {data}")
        return False

    return True


def post_telegram(caption: str, url_button: str | None = None) -> bool:
    """
    Envía un mensaje de texto a Telegram con opción de botón de URL.

    :param caption: Texto del mensaje (se permite Markdown).
    :param url_button: URL para el botón (opcional).
    :return: True si se envió bien, False si hubo error.
    """
    payload: dict = {
        "chat_id": CHAT_ID,
        "text": caption,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }

    if url_button:
        payload["reply_markup"] = {
            "inline_keyboard": [
                [
                    {
                        "text": "🔗 Ver oferta",
                        "url": url_button,
                    }
                ]
            ]
        }

    return _send_request("sendMessage", payload)


def post_telegram_photo(
    photo_url: str,
    caption: str,
    url_button: str | None = None,
) -> bool:
    """
    Envía una foto con caption a Telegram, con opción de botón de URL.

    :param photo_url: URL pública de la imagen.
    :param caption: Texto del mensaje (Markdown).
    :param url_button: URL para el botón (opcional).
    :return: True si se envió bien, False si hubo error.
    """
    payload: dict = {
        "chat_id": CHAT_ID,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "Markdown",
    }

    if url_button:
        payload["reply_markup"] = {
            "inline_keyboard": [
                [
                    {
                        "text": "🔗 Ver oferta",
                        "url": url_button,
                    }
                ]
            ]
        }

    return _send_request("sendPhoto", payload)
