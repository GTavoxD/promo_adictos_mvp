import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Recuperamos el token refrescado (asegúrate de haber corrido main_search.py al menos una vez antes)
# Nota: Como el access_token cambia, lo ideal es obtenerlo fresco, 
# pero para esta prueba rápida usaremos el refresh logic.
client_id = os.getenv("MELI_CLIENT_ID")
client_secret = os.getenv("MELI_CLIENT_SECRET")
refresh_token = os.getenv("MELI_REFRESH_TOKEN")

def probar_token():
    # 1. Renovamos token al vuelo para asegurar que sea válido
    url_auth = "https://api.mercadolibre.com/oauth/token"
    payload = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token
    }
    
    try:
        r_auth = requests.post(url_auth, data=payload)
        if r_auth.status_code != 200:
            print("❌ Error renovando token (tu refresh token quizás murió). Corre setup_tokens.py de nuevo.")
            return

        access_token = r_auth.json()['access_token']
        print("✅ Token generado correctamente.")

        # 2. PRUEBA DE FUEGO: ¿Quién soy?
        # Este endpoint requiere permisos básicos.
        url_me = "https://api.mercadolibre.com/users/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        r_me = requests.get(url_me, headers=headers)
        
        if r_me.status_code == 200:
            user_data = r_me.json()
            print(f"\n✅ ¡EL TOKEN FUNCIONA! Eres el usuario: {user_data.get('nickname')}")
            print("CONCLUSIÓN: Tu token está perfecto. El problema es el endpoint de Búsqueda.")
        else:
            print(f"\n❌ ERROR 403 en /users/me")
            print("CONCLUSIÓN: A tu aplicación le faltan permisos (Scopes).")

    except Exception as e:
        print(e)

if __name__ == "__main__":
    probar_token()