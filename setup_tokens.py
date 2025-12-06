import requests
import os
from dotenv import load_dotenv

# Carga las variables de tu archivo .env (CLIENT_ID y CLIENT_SECRET)
load_dotenv()

APP_ID = os.getenv("MELI_CLIENT_ID")
CLIENT_SECRET = os.getenv("MELI_CLIENT_SECRET")

# --- CAMBIO IMPORTANTE AQUÍ ---
# Debe coincidir letra por letra con lo que tienes en el panel de MeLi
REDIRECT_URI = "https://www.google.com" 

def obtener_primeros_tokens():
    if not APP_ID or not CLIENT_SECRET:
        print("❌ Faltan el ID o el SECRET en el archivo .env")
        return

    # 1. Generar el link de autorización
    auth_url = f"https://auth.mercadolibre.com.mx/authorization?response_type=code&client_id={APP_ID}&redirect_uri={REDIRECT_URI}"
    
    print("\n--- PASO 1: AUTORIZACIÓN ---")
    print("1. Copia y pega esta URL en tu navegador:")
    print(f"\n{auth_url}\n")
    print("2. Inicia sesión en MercadoLibre y da click en 'Permitir'.")
    print("3. MercadoLibre te redirigirá a la página de GOOGLE.")
    print("4. ⚠️ NO busques nada en Google. ¡Mira la BARRA DE DIRECCIONES arriba!")
    print("   Verás algo así: https://www.google.com/?code=TG-66b2xxxxx...")
    print("5. Copia SOLO el código que está después de 'code=' y antes del '&' (si lo hay).")
    
    auth_code = input("\nPegue el CODE (TG-xxxx...) aquí: ").strip()

    # 2. Canjear el código por el token real
    url = "https://api.mercadolibre.com/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": APP_ID,
        "client_secret": CLIENT_SECRET,
        "code": auth_code,
        "redirect_uri": REDIRECT_URI
    }

    print("\n--- PASO 2: GENERANDO TOKENS ---")
    response = requests.post(url, data=payload)
    
    if response.status_code == 200:
        data = response.json()
        refresh_token = data['refresh_token']
        print("\n✅ ¡EXCELENTE! Tenemos conexión.")
        print(f"\nTu nuevo REFRESH TOKEN es:")
        print(f"---------------------------------------------------")
        print(refresh_token)
        print(f"---------------------------------------------------")
        print("\n>>> ACCIÓN REQUERIDA: Copia ese token largo y pégalo en tu archivo .env")
        print("donde dice MELI_REFRESH_TOKEN=...")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    obtener_primeros_tokens()