import os

# ---------- Parámetros de Mercado Libre ----------
ML_SITE_ID = os.getenv("ML_SITE_ID", "MLM")  # México por default

# Búsqueda base
SEARCH_QUERY = os.getenv("PROMO_SEARCH_QUERY", "oferta")

# Paginación
PAGES = int(os.getenv("PROMO_PAGES", 3))
LIMIT_PER_PAGE = int(os.getenv("PROMO_LIMIT_PER_PAGE", 50))

# Filtro mínimo de descuento (porcentaje)
MIN_DISCOUNT_PERCENT = float(os.getenv("PROMO_MIN_DISCOUNT_PERCENT", 50))

# ---------- OCR / Tesseract ----------
# Si Tesseract NO está en el PATH, pon aquí la ruta completa al ejecutable.
# Ejemplo típico en Windows:
# TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "").strip()

# ---------- Notificador (Telegram) ----------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# Número máximo de ofertas a enviar por corrida (para no spamear)
MAX_OFFERS_TO_SEND = int(os.getenv("MAX_OFFERS_TO_SEND", 20))
