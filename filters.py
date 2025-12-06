# filters.py

# 🔞 Adultos
BANNED_ADULT = [
    "juguete sexual", "adultos", "sexy", "erotico",
    "anal", "dildo", "sexo", "condon", "pene"
]

# 👕 Ropa íntima
BANNED_CLOTHING = [
    "ropa interior", "boxer", "calzon",
    "braga", "panty", "panties", "tanga", "lenceria"
]

# 💊 Farmacia y suplementos
BANNED_HEALTH = [
    "vitamina", "suplemento alimenticio", "farmacia",
    "medicina", "pastilla", "tableta recubierta"
]

# 🏠 Línea blanca y muebles
BANNED_HOME = [
    "colchon", "matrimonial", "king", "queen",
    "parrilla de gas", "parrilla electrica", "estufa", 
    "lavadora", "secadora", "refrigerador", "refrigeradora"
]

# 💳 Productos digitales
BANNED_DIGITAL = [
    "gift card", "tarjeta regalo", "recarga", "recargas"
]

# 📚 Otros
BANNED_MISC = [
    "libro usado", "revista", "fanzine",
    "pintura al oleo", "lienzo", "acuarela",
    "manualidades", "hecho a mano",
    "hospital", "hospitalario", "quirurgico", "ortopedico",
    "silla de ruedas",
    "protector de pantalla", "mica de vidrio",
    "funda para celular", "case para iphone", "carcasa para"
]

# ✅ Unión de todas
BANNED_KEYWORDS = (
    BANNED_ADULT + BANNED_CLOTHING + BANNED_HEALTH +
    BANNED_HOME + BANNED_DIGITAL + BANNED_MISC
)
